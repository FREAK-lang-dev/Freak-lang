#!/usr/bin/env python3
"""Build FREAK's three mbedTLS amalgamations from an upstream release.

    python -u tools/mbedtls_amalgamate.py <mbedtls-3.6.x source dir>

mbedTLS's library files clash on file-local names, so they compile as three
translation units (core, extra, keys). Each unit is written as one
self-contained .inc under freakc/runtime/third_party/mbedtls/: every
quoted mbedTLS header is inlined once, at its first inclusion, and the
FREAK build configuration (freak_mbedtls_config.h) stands in for
`#include MBEDTLS_CONFIG_FILE`. System headers stay as #include lines.

--verify preprocesses every unit both ways (upstream tree vs amalgamation)
for several targets, with empty stand-ins for system headers, and fails if
any token differs. Run it after every update.
"""
import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VENDOR = REPO / "freakc" / "runtime" / "third_party" / "mbedtls"
CONFIG = VENDOR / "freak_mbedtls_config.h"

# The grouping that compiles: see the header of each generated file.
KEYS = ["ssl_tls13_keys.c"]
EXTRA = ["cipher.c", "psa_crypto_aead.c", "psa_crypto_cipher.c", "psa_crypto_mac.c",
         "psa_crypto_slot_management.c", "sha512.c", "ssl_tls12_server.c",
         "ssl_tls13_generic.c", "ssl_tls13_server.c"]
# The public headers freak_tls.c uses, brought in with the keys unit.
GLUE_HEADERS = ["mbedtls/ssl.h", "mbedtls/ssl_ticket.h", "mbedtls/x509_crt.h", "mbedtls/pk.h",
                "mbedtls/error.h", "mbedtls/net_sockets.h", "mbedtls/platform_util.h", "psa/crypto.h"]

INCLUDE = re.compile(r'^\s*#\s*include\s*(?:"([^"]+)"|<((?:mbedtls|psa)/[^>]+)>)')
CONFIG_INCLUDE = re.compile(r'^\s*#\s*include\s+MBEDTLS_CONFIG_FILE\b')


DIRECTIVE = re.compile(r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif|define)\b\s*(.*)')
# Conditions inside the configuration headers run while the configuration is
# still being built, so they are never evaluated ahead of time.
CONFIG_HEADERS = re.compile(r'(^|/)(build_info\.h|mbedtls_config\.h|check_config\.h|config_adjust_[a-z_]+\.h|'
                            r'config_psa\.h|crypto_config\.h|crypto_adjust_[a-z_]+\.h|freak_mbedtls_config\.h)$')
TRUE, FALSE, DYNAMIC = "true", "false", "dynamic"


def strip_c_comments(text: str) -> str:
    """Drop /* */ and // comments, keeping the line count (so line numbers
    stay put) and leaving string and character literals alone."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":
                    j += 1
                elif text[j] == "\n":
                    break
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            # Line splices keep the line count without ending a macro
            # whose body the comment sits in.
            out.append(" " + "\\\n" * text.count("\n", i, j))
            i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            # a // comment ending in a backslash continues onto the next line
            while j < n and text[j - 1] == "\\":
                k = text.find("\n", j + 1)
                out.append("\n")
                j = n if k < 0 else k
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', ' ', text)
    return text.split('//')[0].strip()


class Amalgamator:
    """Inline mbedTLS headers once per unit.

    A header is marked done only where it is included unconditionally or
    under a condition that holds on every target (config macros, which are
    the same everywhere). Under platform conditions it is inlined but not
    marked, so a later unconditional #include inlines it again and the
    header's own guard keeps the compile from seeing it twice. Includes in
    regions that are false on every target are left out."""

    def __init__(self, root: Path, static_macros, defined_somewhere):
        self.root = root
        self.static = static_macros
        self.defined_somewhere = defined_somewhere
        self.done = set()
        self.out = []

    def resolve(self, name: str, here: Path):
        for base in (here, self.root / "include", self.root / "library"):
            candidate = (base / name).resolve()
            if candidate.is_file() and self.root.resolve() in candidate.parents:
                return candidate
        return None

    def evaluate(self, expression: str):
        expression = strip_comments(expression)
        def known(name):
            if name in self.static:
                return True
            if (name.startswith("MBEDTLS_") or name.startswith("PSA_")) and name not in self.defined_somewhere:
                self.static[name] = None
                return True
            return False
        def defined(match):
            name = match.group(1)
            if not known(name):
                return " __dynamic__ "
            return " 1 " if self.static[name] is not None else " 0 "
        text = re.sub(r'defined\s*\(\s*(\w+)\s*\)', defined, expression)
        text = re.sub(r'defined\s+(\w+)', defined, text)
        def name(match):
            word = match.group(0)
            if re.fullmatch(r'0[xX][0-9a-fA-F]+[uUlL]*|\d+[uUlL]*', word):
                return re.sub(r'[uUlL]+$', '', word)
            if word in ("and", "or", "not"):
                return word
            if not known(word):
                return " __dynamic__ "
            if self.static[word] is None:
                return " 0 "
            value = self.static[word]
            if not re.fullmatch(r'\(?\s*(0[xX][0-9a-fA-F]+|\d+)[uUlL]*\s*\)?', value):
                return " __dynamic__ "
            return re.sub(r'[uUlL]+', '', value)
        text = re.sub(r'\b\w+\b', name, text)
        if "__dynamic__" in text or not text:
            return DYNAMIC
        text = text.replace("&&", " and ").replace("||", " or ")
        text = re.sub(r'!(?!=)', ' not ', text)
        try:
            return TRUE if eval(text, {"__builtins__": {}}) else FALSE
        except Exception:
            return DYNAMIC

    def emit_file(self, path: Path, label: str, dynamic_context=False):
        if path in self.done:
            return
        if not dynamic_context:
            self.done.add(path)
        self.out.append(f'#line 1 "{label}"\n')
        configuring = False and bool(CONFIG_HEADERS.search(path.as_posix()))
        lines = strip_c_comments(path.read_text(encoding="utf-8")).splitlines(keepends=True)
        # Directive text with its backslash continuations joined (the lines
        # themselves are copied unchanged).
        joined = []
        for i, l in enumerate(lines):
            text = l
            j = i
            while text.rstrip("\r\n").endswith("\\") and j + 1 < len(lines):
                j += 1
                text = text.rstrip("\r\n")[:-1] + " " + lines[j]
            joined.append(text)
        # The header's include guard: the first directive is #ifndef G and
        # the next one #define G. Inlined once, it is always true.
        guard_line = None
        directives = [(i, DIRECTIVE.match(l)) for i, l in enumerate(joined)]
        directives = [(i, m) for i, m in directives if m]
        if len(directives) >= 2 and directives[0][1].group(1) == "ifndef" and directives[1][1].group(1) == "define":
            if strip_comments(directives[0][1].group(2)) == strip_comments(directives[1][1].group(2)).split()[0]:
                guard_line = directives[0][0]
        stack = []  # [state, taken]
        continued = False
        for number, line in enumerate(lines):
            directive = None if continued else DIRECTIVE.match(joined[number])
            continued = line.rstrip("\r\n").endswith("\\")
            if directive:
                kind, rest = directive.group(1), directive.group(2)
                if kind in ("if", "ifdef", "ifndef"):
                    if number == guard_line:
                        state = TRUE
                    elif configuring:
                        state = DYNAMIC
                    elif kind == "if":
                        state = self.evaluate(rest)
                    else:
                        state = self.evaluate(("defined(%s)" if kind == "ifdef" else "!defined(%s)") % strip_comments(rest))
                    stack.append([state, state == TRUE])
                elif kind == "elif" and stack:
                    frame = stack[-1]
                    if frame[0] == DYNAMIC and not frame[1] is True:
                        frame[0] = DYNAMIC
                    elif frame[1]:
                        frame[0] = FALSE
                    else:
                        state = DYNAMIC if configuring else self.evaluate(rest)
                        frame[0] = state
                        frame[1] = state == TRUE
                        if state == DYNAMIC:
                            frame[1] = "dynamic"
                elif kind == "else" and stack:
                    frame = stack[-1]
                    if frame[0] == DYNAMIC or frame[1] == "dynamic":
                        frame[0] = DYNAMIC
                    else:
                        frame[0] = FALSE if frame[1] else TRUE
                elif kind == "endif" and stack:
                    stack.pop()
            if CONFIG_INCLUDE.match(line):
                self.emit_file(CONFIG.resolve(), "freak_mbedtls_config.h", dynamic_context)
                self.out.append(f'#line {number + 2} "{label}"\n')
                continue
            match = INCLUDE.match(line)
            if match:
                name = match.group(1) or match.group(2)
                if name == "mbedtls/mbedtls_config.h" and path == CONFIG.resolve():
                    target = self.root / "include" / "mbedtls" / "mbedtls_config.h"
                else:
                    target = self.resolve(name, path.parent)
                if target is not None:
                    states = [frame[0] for frame in stack]
                    if FALSE in states:
                        self.out.append(f"/* #include \"{name}\": not built in this configuration */\n")
                    else:
                        before = len(self.out)
                        self.emit_file(target.resolve(), self.label(target), dynamic_context or DYNAMIC in states)
                        if len(self.out) != before:
                            self.out.append(f'#line {number + 2} "{label}"\n')
                        else:
                            self.out.append("\n")
                    continue
            self.out.append(line if line.endswith("\n") else line + "\n")

    def label(self, path: Path) -> str:
        return path.resolve().relative_to(self.root.resolve()).as_posix()


# FREAK's local changes to upstream sources, applied to a copy of the tree
# before amalgamating (and verifying, so --verify still proves the .inc files
# are exactly upstream plus these). Each: file, the text it goes before or
# after, where, and the file in tools/mbedtls_patches/ that holds it.
PATCHES: list = []
PATCH_DIR = REPO / "tools" / "mbedtls_patches"


def patched_tree(root: Path, temp: Path) -> Path:
    """A copy of the upstream tree with PATCHES applied; #line keeps every
    original line number right after each insertion."""
    copy = temp / "src"
    shutil.copytree(root, copy)
    for name, anchor, where, patch_file in PATCHES:
        path = copy / name
        text = path.read_text(encoding="utf-8")
        if text.count(anchor) != 1:
            raise SystemExit(f"patch {patch_file}: its anchor isn't in {name} exactly once (new mbedTLS?)")
        insert = (PATCH_DIR / patch_file).read_text(encoding="utf-8")
        if not insert.endswith("\n"):
            insert += "\n"
        at = text.index(anchor)
        if where == "before":
            line = text.count("\n", 0, at) + 1
            block = f"#if defined(__SIZEOF_INT128__)\n{insert}#endif\n#line {line} \"{name}\"\n"
            text = text[:at] + block + text[at:]
        else:
            # after the function's opening brace, ahead of its declarations
            brace = text.index("{\n", at) + 2
            line = text.count("\n", 0, brace) + 1
            text = text[:brace] + insert + f"#line {line} \"{name}\"\n" + text[brace:]
        path.write_text(text, encoding="utf-8")
    return copy


def unit_files(root: Path):
    library = sorted(p.name for p in (root / "library").glob("*.c"))
    core = [f for f in library if f not in EXTRA and f not in KEYS]
    return {"core": core, "extra": EXTRA, "keys": KEYS}


def entry_text(root: Path, unit: str, files):
    """The upstream-tree form of a unit: what the amalgamation must match."""
    lines = ['#define MBEDTLS_CONFIG_FILE "freak_mbedtls_config.h"\n']
    lines += [f'#include "library/{f}"\n' for f in files]
    if unit == "keys":
        lines += [f'#include "{h}"\n' for h in GLUE_HEADERS]
    return "".join(lines)


# Names the build never defines: C, not C++; no docs build; no test drivers.
ASSUMED_UNDEFINED = ("__cplusplus", "__DOXYGEN_ONLY__", "PSA_CRYPTO_DRIVER_TEST",
                     "MBEDTLS_TEST_LIBTESTDRIVER1", "MBEDTLS_TEST_HOOKS", "MBEDTLS_TEST_HOOKS_FOR_TESTS")


def static_macros(root: Path, clang: str, stubs: Path, config_dir: Path, unit: str, files):
    """MBEDTLS_/PSA_ macros with the same value on every target at the end of
    the unit (None = never defined). Conditions on them are decided ahead of
    time; the verification pass checks that this matched the real compile."""
    probe = config_dir / f"probe_{unit}.c"
    probe.write_text(entry_text(root, unit, files))
    dumps = []
    for target in TARGETS:
        command = [clang, "-E", "-dM", "-nostdinc", "-isystem", str(stubs), "--target=" + target,
                   "-I", str(root), "-I", str(root / "include"), "-I", str(root / "library"),
                   "-I", str(config_dir), str(probe)]
        result = subprocess.run(command, capture_output=True, text=True)
        macros = {}
        for line in result.stdout.splitlines():
            m = re.match(r'#define (\w+)(\(.*?\))?\s*(.*)', line)
            if m:
                macros[m.group(1)] = "<function>" if m.group(2) else m.group(3).strip()
        if not macros:
            raise SystemExit(f"could not list the macros of the {unit} unit for {target}")
        dumps.append(macros)
    static = {name: None for name in ASSUMED_UNDEFINED}
    for name in set().union(*dumps):
        if not (name.startswith("MBEDTLS_") or name.startswith("PSA_")):
            continue
        values = {d.get(name) for d in dumps}
        if len(values) == 1:
            static[name] = values.pop()
    return static, set().union(*dumps)


def build(root: Path, version: str, clang: str, stubs: Path, config_dir: Path):
    outputs = {}
    for unit, files in unit_files(root).items():
        static, defined_somewhere = static_macros(root, clang, stubs, config_dir, unit, files)
        amalgamator = Amalgamator(root, static, defined_somewhere)
        amalgamator.out.append(
            f"/* mbedTLS {version}, {unit} unit, amalgamated for the FREAK runtime by\n"
            f"   tools/mbedtls_amalgamate.py. Generated: don't edit by hand.\n"
            f"   SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-or-later (see LICENSE). */\n")
        amalgamator.emit_file(CONFIG.resolve(), "freak_mbedtls_config.h")
        for name in files:
            amalgamator.emit_file((root / "library" / name).resolve(), "library/" + name)
        if unit == "keys":
            # After the library file, whose common.h opens private fields.
            for header in GLUE_HEADERS:
                amalgamator.emit_file((root / "include" / header).resolve(), "include/" + header)
        outputs[unit] = "".join(amalgamator.out)
    return outputs


TARGETS = ["x86_64-linux-gnu", "aarch64-linux-gnu", "x86_64-pc-windows-msvc",
           "aarch64-pc-windows-msvc", "x86_64-w64-windows-gnu", "x86_64-apple-darwin",
           "arm64-apple-darwin", "x86_64-unknown-freebsd"]


def stub_system_headers(root: Path, stubs: Path):
    names = set()
    pattern = re.compile(r'^\s*#\s*include\s*<([^>]+)>', re.M)
    for path in list(root.rglob("*.[ch]")) + [CONFIG]:
        names.update(pattern.findall(path.read_text(encoding="utf-8", errors="replace")))
    for name in names:
        target = stubs / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("")


def preprocess(clang: str, source: Path, includes, target: str, stubs: Path) -> str:
    command = [clang, "-E", "-P", "-nostdinc", "-isystem", str(stubs), "--target=" + target]
    for include in includes:
        command += ["-I", str(include)]
    command.append(str(source))
    # Empty system headers trip a few #error checks (CHAR_BIT, clocks):
    # both sides hit the same ones, so compare the output and the errors.
    result = subprocess.run(command, capture_output=True, text=True)
    if not result.stdout.strip():
        raise SystemExit(f"preprocessing {source} for {target} failed:\n{result.stderr[:2000]}")
    errors = sorted(set(re.findall(r'error: (.*)', result.stderr)))
    text = re.sub(r'"[^"\n]*?/((?:library|include)/[\w./]+)"', r'"\1"', result.stdout)
    text = re.sub(r'"[^"\n]*?/(freak_mbedtls_config\.h)"', r'"\1"', text)
    return " ".join(text.split()) + "\n" + "\n".join(errors)


def workspace(root: Path, temp: Path):
    stubs = temp / "stubs"
    stub_system_headers(root, stubs)
    config_dir = temp / "config"
    config_dir.mkdir()
    (config_dir / "freak_mbedtls_config.h").write_text(CONFIG.read_text(encoding="utf-8"))
    return stubs, config_dir


def verify(root: Path, outputs, clang: str, stubs: Path, config_dir: Path):
    temp = config_dir.parent
    for unit, files in unit_files(root).items():
        upstream = temp / f"upstream_{unit}.c"
        upstream.write_text(entry_text(root, unit, files))
        amalgamated = temp / f"amalgamated_{unit}.c"
        amalgamated.write_text(outputs[unit])
        for target in TARGETS:
            a = preprocess(clang, upstream, [root, root / "include", root / "library", config_dir], target, stubs)
            b = preprocess(clang, amalgamated, [], target, stubs)
            if a != b:
                raise SystemExit(f"{unit} unit differs from upstream for {target}")
        print(f"  {unit}: identical to upstream (plus any PATCHES) on {len(TARGETS)} targets")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="an extracted mbedtls-3.6.x release")
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.source.resolve()
    version_header = (root / "include" / "mbedtls" / "build_info.h").read_text(encoding="utf-8")
    version = re.search(r'#define MBEDTLS_VERSION_STRING\s+"([^"]+)"', version_header).group(1)
    with tempfile.TemporaryDirectory() as temp:
        tree = patched_tree(root, Path(temp))
        stubs, config_dir = workspace(tree, Path(temp))
        outputs = build(tree, version, args.clang, stubs, config_dir)
        if args.verify:
            verify(tree, outputs, args.clang, stubs, config_dir)
    sums = []
    for unit, text in outputs.items():
        name = f"mbedtls_{unit}.inc"
        (VENDOR / name).write_text(text, encoding="utf-8", newline="\n")
        sums.append(f"{hashlib.sha256(text.encode('utf-8')).hexdigest()}  {name}")
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    (VENDOR / "LICENSE").write_text(license_text, encoding="utf-8", newline="\n")
    sums.append(f"{hashlib.sha256(license_text.encode('utf-8')).hexdigest()}  LICENSE")
    config_text = CONFIG.read_text(encoding="utf-8")
    sums.append(f"{hashlib.sha256(config_text.encode('utf-8')).hexdigest()}  freak_mbedtls_config.h")
    (VENDOR / "SHA256SUMS").write_text("\n".join(sorted(sums, key=lambda l: l.split()[1])) + "\n", encoding="utf-8", newline="\n")
    print(f"mbedTLS {version}: wrote " + ", ".join(f"mbedtls_{u}.inc" for u in outputs))


if __name__ == "__main__":
    main()
