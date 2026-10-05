#!/usr/bin/env python3
"""Strict native legacy-stdlib bodies, value behavior, and ownership controls.

This is a component gate for an explicitly supplied self-hosted compiler. It
does not reconstruct the compiler or replace the installed public-import gate.
All nine production module bodies are checked as ordinary source, without
trusted-source offsets, bootstrap compatibility, or filename exemptions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import zipfile


MODULES = ("math", "string", "convert", "algorithm", "json", "version",
           "http", "math3d", "zip")

FIXTURE = r'''
pilot mut std_gate_checks = 0

task std_gate_check(condition: bool) -> void {
    if not condition { panic("legacy standard-library contract failed at check " + word_from_int(std_gate_checks + 1)) }
    std_gate_checks += 1
}

-- Release fixture-owned legacy pools explicitly. The public legacy modules
-- retain their original process-global state and lifetime policy.
task std_gate_clear_pools() -> void {
    if json_inited != 0 {
        pilot mut i = 0
        repeat json_count times {
            pilot t: word = array_get(json_types, i)
            if t == "a" or t == "o" {
                array_release(word_to_int(array_get(json_children, i)))
            }
            if t == "o" { array_release(word_to_int(array_get(json_keys, i))) }
            i += 1
        }
        array_release(json_types) json_types = 0
        array_release(json_vals) json_vals = 0
        array_release(json_children) json_children = 0
        array_release(json_keys) json_keys = 0
        json_src = "" json_count = 0 json_inited = 0
    }
    if http_inited != 0 {
        array_release(http_resp_statuses) http_resp_statuses = 0
        array_release(http_resp_bodies) http_resp_bodies = 0
        array_release(http_resp_headers_raw) http_resp_headers_raw = 0
        http_resp_count = 0 http_inited = 0
    }
    if zip_arch_inited {
        pilot mut j = 0
        repeat zip_arch_count times {
            array_release(word_to_int(array_get(zip_arch_names, j)))
            array_release(word_to_int(array_get(zip_arch_contents, j)))
            j += 1
        }
        array_release(zip_arch_names) zip_arch_names = 0
        array_release(zip_arch_contents) zip_arch_contents = 0
        array_release(zip_arch_paths) zip_arch_paths = 0
        zip_arch_count = 0 zip_arch_inited = false zip_last_error_message = ""
    }
}

-- Exercise the existing sized raw-word character primitive. Source literal
-- embedded NUL and ByteBuffer text conversion remain rejected separately.
task std_gate_zero() -> word {
    give back char_to_word(0)
}

task std_gate_core() -> void {
    std_gate_check(std_abs(-99) == 99)
    std_gate_check(std_clamp(17, 2, 9) == 9)
    std_gate_check(std_clamp(-7, 2, 9) == 2)
    std_gate_check(std_pow(2, 10) == 1024)
    std_gate_check(std_pow(2, -1) == 0)
    std_gate_check(std_pow(99, 0) == 1)
    std_gate_check(std_pow(-3, 3) == -27)
    std_gate_check(std_gcd(-48, 18) == 6)
    std_gate_check(std_lcm(12, 18) == 36)
    std_gate_check(std_factorial(6) == 720)
    std_gate_check(std_fibonacci(10) == 55)
    std_gate_check(std_is_even(-4) and std_is_odd(-3))
    std_gate_check(int_to_hex(-255) == "-ff")
    std_gate_check(int_to_bin(-13) == "-1101")
    std_gate_check(int_to_oct(511) == "777")
    std_gate_check(int_to_hex(0) == "0")
    std_gate_check(word_to_int_safe("-12034") == -12034)
    std_gate_check(word_to_int_safe("12x") == 0)
    std_gate_check(bool_to_word(false) == "false")
    std_gate_check(string_repeat("ab", 3) == "ababab")
    std_gate_check(string_pad_left("x", 4, "0") == "000x")
    std_gate_check(string_pad_right("x", 3, ".") == "x..")
    std_gate_check(string_reverse("abcd") == "dcba")
    std_gate_check(string_reverse(("a" + std_gate_zero() + "b")) == ("b" + std_gate_zero() + "a"))
    std_gate_check(string_count("aaaa", "aa") == 3)
    std_gate_check(string_count("abc", "") == 0)
    std_gate_check(string_split("a,b,c", ",") == "a|b|c")
    std_gate_check(string_join("a|b|c", "::") == "a::b::c")
    std_gate_check(string_trim(" \tvalue\r\n") == "value")
    std_gate_check(string_trim(" \t\n") == "")
    std_gate_check(string_replace("ababa", "ab", "X") == "XXa")
    std_gate_check(string_substring("abcdef", 1, 4) == "bcd")
    std_gate_check(string_index_of("abcabc", "bc") == 1)
    std_gate_check(string_starts_with("éclair", "é"))
    std_gate_check(string_ends_with("helloΩ", "Ω"))

    pilot numbers = array_new()
    array_push(numbers, "9") array_push(numbers, "-3")
    array_push(numbers, "9") array_push(numbers, "0")
    array_sort_int(numbers)
    std_gate_check(array_join(numbers, ",") == "-3,0,9,9")
    std_gate_check(array_sum_int(numbers) == 15)
    std_gate_check(array_min_int(numbers) == -3 and array_max_int(numbers) == 9)
    std_gate_check(array_binary_search_int(numbers, -3) == 0)
    std_gate_check(array_find(numbers, "missing") == -1)
    std_gate_check(array_count(numbers, "9") == 2)
    pilot copied = array_copy(numbers)
    array_reverse(copied)
    std_gate_check(array_join(copied, ";") == "9;9;0;-3")
    array_release(copied) array_release(numbers)
    pilot extremes = array_new()
    array_push(extremes, "9223372036854775807")
    array_push(extremes, "-9223372036854775808") array_push(extremes, "0")
    array_sort_int(extremes)
    std_gate_check(array_join(extremes, ",") == "-9223372036854775808,0,9223372036854775807")
    std_gate_check(array_min_int(extremes) == -9223372036854775808 and array_max_int(extremes) == 9223372036854775807)
    array_release(extremes)

    -- strcmp compares unsigned bytes and stops at the first NUL. Preserve
    -- that existing API, including stable equality of distinct sized tails.
    std_gate_check(freak_word_compare("", "x") == -1)
    std_gate_check(freak_word_compare("z", "é") == -1)
    std_gate_check(freak_word_compare("Ω", "é") == 1)
    std_gate_check(freak_word_compare(("a" + std_gate_zero() + "b"), ("a" + std_gate_zero() + "c")) == 0)
    pilot words = array_new()
    array_push(words, "Ω") array_push(words, ("a" + std_gate_zero() + "second"))
    array_push(words, "z") array_push(words, ("a" + std_gate_zero() + "third"))
    array_push(words, "") array_push(words, "é")
    array_sort_word(words)
    std_gate_check(array_get(words, 0) == "")
    std_gate_check(array_get(words, 1) == ("a" + std_gate_zero() + "second"))
    std_gate_check(array_get(words, 2) == ("a" + std_gate_zero() + "third"))
    std_gate_check(array_get(words, 3) == "z")
    std_gate_check(array_get(words, 4) == "é")
    std_gate_check(array_get(words, 5) == "Ω")
    array_release(words)

    std_gate_check(ver_parse("v1.2.3-alpha+build.7") == "1:2:3:alpha:build.7")
    std_gate_check(ver_to_string("1:2:3:alpha:build.7") == "1.2.3-alpha+build.7")
    std_gate_check(ver_compare("1:2:3::", "1:2:4::") == -1)
    std_gate_check(ver_compare("1:2:3:alpha:", "1:2:3::") == -1)
    std_gate_check(ver_bump_minor("1:2:3:x:y") == "1:3:0::")
    std_gate_check(ver_bump_patch("1:2:3:x:y") == "1:2:4::")
    std_gate_check(ver_satisfies("1.5.0", ">=1.0.0 <2.0.0"))
    std_gate_check(not ver_satisfies("2.0.0", "^1.0.0"))
    std_gate_check(ver_satisfies("2.4.9", "~2.4.0"))
    std_gate_check(not ver_satisfies("2.5.0", "~2.4.0"))
    std_gate_check(ver_satisfies("7.0.0", "*"))

    pilot root = json_parse("{\"s\":\"hello\",\"a\":[2,true,null],\"u\":\"Ω\"}")
    std_gate_check(json_obj_len(root) == 3)
    std_gate_check(json_get_str(json_obj_get(root, "s")) == "hello")
    pilot children = json_obj_get(root, "a")
    std_gate_check(json_arr_len(children) == 3)
    std_gate_check(json_get_int(json_arr_get(children, 0)) == 2)
    std_gate_check(json_get_bool(json_arr_get(children, 1)))
    std_gate_check(json_is_null(json_arr_get(children, 2)))
    std_gate_check(json_stringify(root) == "{\"s\":\"hello\",\"a\":[2,true,null],\"u\":\"Ω\"}")
    pilot later = json_parse("[7,8]")
    std_gate_check(json_arr_len(later) == 2)
    std_gate_check(json_get_str(json_obj_get(root, "s")) == "hello")

    http_init()
    pilot response = http_split_response(("HTTP/1.1 201 Created\r\nX-A: b\r\n\r\na" + std_gate_zero() + "Ω"))
    std_gate_check(http_resp_status(response) == 201)
    std_gate_check(http_resp_body(response) == ("a" + std_gate_zero() + "Ω"))
    std_gate_check(http_resp_headers(response) == "HTTP/1.1 201 Created\r\nX-A: b\r\n\r\n")
    std_gate_check(http_parse_status("not-http") == 0)

    pilot mut i = 0
    repeat 100 times {
        std_gate_check(ver_to_string(ver_parse("v1.2.3-alpha+build")) == "1.2.3-alpha+build")
        std_gate_check(ver_satisfies("1.7.3", ">=1.0.0 <2.0.0"))
        std_gate_check(string_replace("a-b-a", "a", "Ω") == "Ω-b-Ω")
        i += 1
    }
}

task std_gate_3d() -> void {
    std_gate_check(math3d_magnitude2(math3d_vec2(3.0, 4.0)) == 5.0)
    std_gate_check(math3d_magnitude3(math3d_vec3(2.0, 3.0, 6.0)) == 7.0)
    std_gate_check(math3d_magnitude4(math3d_vec4(0.0, 0.0, 3.0, 4.0)) == 5.0)
    pilot v = math3d_normalize3(math3d_vec3(3.0, 0.0, 4.0))
    std_gate_check(math3d_approx_eq(v.x, 0.6, 0.000001))
    std_gate_check(math3d_approx_eq(v.z, 0.8, 0.000001))
    pilot z = math3d_normalize2(math3d_vec2(0.0, 0.0))
    std_gate_check(z.x == 0.0 and z.y == 0.0)
    pilot transformed = math3d_mat4_transform_point(math3d_mat4_identity(), math3d_vec3(1.0, 2.0, 3.0))
    std_gate_check(transformed.x == 1.0 and transformed.y == 2.0 and transformed.z == 3.0)
    pilot camera = math3d_mat4_look_at(math3d_vec3(0.0, 0.0, 1.0), math3d_vec3(0.0, 0.0, 0.0), math3d_vec3(0.0, 1.0, 0.0))
    std_gate_check(camera.m11 == 1.0 and camera.m22 == 1.0 and camera.m33 == 1.0)
    std_gate_check(camera.m34 == -1.0)
}

task std_gate_client(port: int) -> void {
    pilot a = http_get("127.0.0.1", "/get", port)
    std_gate_check(http_resp_status(a) == 200)
    std_gate_check(http_resp_body(a) == ("get" + std_gate_zero() + "é"))
    pilot b = http_post("127.0.0.1", "/post", port, "text/plain", "postΩ")
    std_gate_check(http_resp_status(b) == 201)
    std_gate_check(http_resp_body(b) == ("post" + std_gate_zero() + "é"))
    pilot c = http_put("127.0.0.1", "/put", port, "text/plain", "puté")
    std_gate_check(http_resp_status(c) == 202)
    std_gate_check(http_resp_body(c) == ("put" + std_gate_zero() + "é"))
    pilot d = http_delete("127.0.0.1", "/delete", port)
    std_gate_check(http_resp_status(d) == 204)
    std_gate_check(http_resp_body(d) == ("delete" + std_gate_zero() + "é"))
}

task std_gate_zip(path: word) -> void {
    pilot archive = zip_archive_new()
    zip_archive_add(archive, "entryΩ.txt", "line1\nquote\"slash\\é")
    std_gate_check(zip_archive_entry_count(archive) == 1)
    std_gate_check(zip_archive_name_at(archive, 0) == "entryΩ.txt")
    std_gate_check(zip_archive_content_at(archive, 0) == "line1\nquote\"slash\\é")
    std_gate_check(zip_write_payload(archive) == "{\"entries\":[{\"name\":\"entryΩ.txt\",\"content\":\"line1\\nquote\\\"slash\\\\é\"}]}")
    std_gate_check(zip_write(path + "", archive))
    pilot loaded = zip_read(path)
    std_gate_check(loaded >= 0)
    std_gate_check(zip_archive_entry_count(loaded) == 1)
    std_gate_check(zip_archive_name_at(loaded, 0) == "entryΩ.txt")
    std_gate_check(zip_archive_content_at(loaded, 0) == "line1\nquote\"slash\\é")
}

task main() -> void {
    pilot mode = process::arg(1)
    if mode == "core" { std_gate_core() }
    if mode == "3d" { std_gate_3d() }
    if mode == "client" { std_gate_client(word_to_int(process::arg(2))) }
    if mode == "zip" { std_gate_zip(process::arg(2)) }
    std_gate_clear_pools()
    say "PASS " + mode + " " + word_from_int(std_gate_checks)
}
'''

NEGATIVE = {
    "transferred_string": 'pilot s = "abc"\n pilot t = string_reverse(s)\n say s',
    "transferred_version": 'pilot v = "1:2:3::"\n pilot n = ver_minor(v)\n say v',
    "transferred_json": 'pilot s = "[1]"\n pilot h = json_parse(s)\n say s',
    "transferred_vector": 'pilot v = math3d_vec3(1.0,2.0,3.0)\n pilot n = math3d_magnitude3(v)\n say v.x',
    "immutable_local": 'pilot n = 0\n n = 1\n say n',
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--compiler", type=Path, required=True)
    ap.add_argument("--runtime-root", type=Path)
    ap.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--clang", default="clang")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--opt", type=int, nargs="+", choices=(0, 2, 3), default=[0, 2, 3])
    ap.add_argument("--backends", nargs="+", choices=("c", "llvm"), default=["c", "llvm"])
    ap.add_argument("--sanitize", action="store_true")
    args = ap.parse_args()
    args.compiler = args.compiler.resolve()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    repo = args.source_root.resolve()
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:halt_on_error=1",
               UBSAN_OPTIONS="halt_on_error=1")
    tracked = {str(repo / "std" / (n + ".fk")): digest(repo / "std" / (n + ".fk")) for n in MODULES}
    for path in sorted(runtime.rglob("*")):
        if path.is_file(): tracked[str(path)] = digest(path)
    for path in sorted((runtime.parents[1] / "third_party/llhttp").rglob("*")):
        if path.is_file(): tracked[str(path)] = digest(path)
    report = {"compiler_sha256": digest(args.compiler), "inputs_sha256": tracked,
              "sanitize": args.sanitize, "cases": [], "native_platform": sys.platform}

    def run(command: list, label: str, timeout: int = 90) -> subprocess.CompletedProcess:
        p = subprocess.run(list(map(str, command)), cwd=args.out_dir, env=env,
                           capture_output=True, timeout=timeout)
        (args.out_dir / (label + ".log")).write_bytes(p.stdout + p.stderr)
        return p

    def require(p: subprocess.CompletedProcess, label: str, output: bytes | None = None) -> None:
        if p.returncode or (output is not None and p.stdout != output) or (output is not None and p.stderr):
            raise AssertionError(f"{label}: exit={p.returncode}; stdout={p.stdout[-3000:]!r}; stderr={p.stderr[-3000:]!r}")

    production = "\n".join((repo / "std" / (n + ".fk")).read_text() for n in MODULES)
    for backend in args.backends:
        source = args.out_dir / ("stdlib-" + backend + ".fk")
        source.write_text(production + FIXTURE)
        require(run([args.compiler, source, "--" + backend, "--strict-borrow"], "emit-" + backend), "strict production bodies " + backend)
        for name, body in NEGATIVE.items():
            negative = args.out_dir / (name + "-" + backend + ".fk")
            negative.write_text(production + "\ntask main() {\n" + body + "\n}\n")
            generated = Path(str(negative) + (".c" if backend == "c" else ".ll"))
            generated.write_text("stale output sentinel")
            p = run([args.compiler, negative, "--" + backend, "--strict-borrow"], "reject-" + name + "-" + backend)
            if not p.returncode or b"borrowck" not in p.stdout or generated.exists():
                raise AssertionError(f"strict rejection lost for {name} {backend}")
            report["cases"].append({"backend": backend, "case": name, "rejected": True})

    for opt in args.opt:
        flags = [f"-O{opt}", "-g", "-I" + str(runtime),
                 "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1"]
        if args.sanitize: flags += ["-fsanitize=address,undefined,function", "-fno-omit-frame-pointer"]
        objects = []
        for name in ("freak_runtime.c", "freak_llvm_runtime.c"):
            obj = args.out_dir / (name + f"-O{opt}.o")
            require(run([args.clang, *flags, "-c", runtime / name, "-o", obj], name + f"-O{opt}"), "runtime object " + name)
            objects.append(obj)
        for backend in args.backends:
            generated = args.out_dir / ("stdlib-" + backend + ".fk" + (".c" if backend == "c" else ".ll"))
            exe = args.out_dir / (f"stdlib-{backend}-O{opt}")
            require(run([args.clang, *flags, generated, *(objects if backend == "llvm" else objects[:1]), "-lm", "-o", exe], f"link-{backend}-O{opt}"), "link " + backend)
            for mode in ("core", "3d", "zip"):
                archive = args.out_dir / (f"roundtrip-{backend}-O{opt}.zip")
                # Native files are published only into this harness's owned
                # fresh output leaf; never replace caller-selected archives.
                if archive.exists(): raise AssertionError(f"output already exists: {archive}")
                p = run([exe, mode, archive], f"run-{mode}-{backend}-O{opt}")
                counts = {"core": 378, "3d": 9, "zip": 9}
                require(p, mode + " " + backend, f"PASS {mode} {counts[mode]}\n".encode())
                if mode == "zip":
                    with zipfile.ZipFile(archive) as z:
                        assert z.namelist() == ["entryΩ.txt"]
                        assert z.read("entryΩ.txt") == 'line1\nquote"slash\\é'.encode()
                report["cases"].append({"backend": backend, "opt": opt, "case": mode, "output": p.stdout.decode().strip()})
                print(f"PASS {backend} O{opt} {mode}", flush=True)

            requests, errors = [], []
            server = socket.socket()
            server.bind(("127.0.0.1", 0)); server.listen(4); server.settimeout(15)
            port = server.getsockname()[1]
            def serve() -> None:
                try:
                    for idx, method in enumerate(("get", "post", "put", "delete")):
                        with server.accept()[0] as conn:
                            conn.settimeout(10); data = b""
                            while b"\r\n\r\n" not in data:
                                chunk = conn.recv(4096)
                                if not chunk: raise EOFError("client closed before headers")
                                data += chunk
                            headers, body = data.split(b"\r\n\r\n", 1)
                            length = 0
                            for line in headers.split(b"\r\n"):
                                if line.lower().startswith(b"content-length:"): length = int(line.split(b":", 1)[1])
                            while len(body) < length:
                                chunk = conn.recv(4096)
                                if not chunk: raise EOFError("client closed before body")
                                body += chunk
                            requests.append(headers + b"\r\n\r\n" + body)
                            payload = method.encode() + b"\0" + "é".encode()
                            conn.sendall(f"HTTP/1.1 {200 + idx if idx < 3 else 204} OK\r\nContent-Length: {len(payload)}\r\nConnection: close\r\n\r\n".encode() + payload)
                except BaseException as exc: errors.append(repr(exc))
                finally: server.close()
            thread = threading.Thread(target=serve, daemon=True); thread.start()
            p = run([exe, "client", port], f"run-client-{backend}-O{opt}", 30)
            thread.join(16)
            require(p, "loopback client " + backend, b"PASS client 8\n")
            assert not thread.is_alive() and not errors and len(requests) == 4, (errors, requests)
            for request, method, body in zip(requests, ("GET", "POST", "PUT", "DELETE"), (b"", "postΩ".encode(), "puté".encode(), b"")):
                expected = f"{method} /{method.lower()} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\nUser-Agent: FREAK/0.8\r\n".encode()
                if method in ("POST", "PUT"): expected += f"Content-Type: text/plain\r\nContent-Length: {len(body)}\r\n".encode()
                assert request == expected + b"\r\n" + body, (request, expected)
            report["cases"].append({"backend": backend, "opt": opt, "case": "client", "requests_hex": [x.hex() for x in requests]})
            print(f"PASS {backend} O{opt} client", flush=True)

        # Both ownership audit domains must actually fail when an owner leaks.
        for domain in ("c", "llvm"):
            src = args.out_dir / (f"audit-control-{domain}.c")
            leak = ('freak_word_from_int(123);' if domain == "c" else
                    'char *p = malloc(5); memcpy(p,"leak",5); freak_llvm_word_adopt_sized((int64_t)p,4);')
            src.write_text('#include <stdlib.h>\n#include <string.h>\n#include "freak_runtime.h"\nint main(void){' + leak + 'return 0;}\n')
            exe = args.out_dir / (f"audit-control-{domain}-O{opt}")
            require(run([args.clang, *flags, src, objects[0], "-lm", "-o", exe], f"audit-link-{domain}-O{opt}"), "audit control link")
            p = run([exe], f"audit-run-{domain}-O{opt}")
            assert p.returncode and b"ownership audit found" in p.stderr, p.stderr
            report["cases"].append({"case": domain + "-audit-failing-control", "opt": opt})
        if args.sanitize:
            src = args.out_dir / "asan-control.c"
            src.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n')
            exe = args.out_dir / (f"asan-control-O{opt}")
            require(run([args.clang, *flags, src, "-o", exe], f"asan-link-O{opt}"), "ASan control link")
            p = run([exe], f"asan-run-O{opt}")
            assert p.returncode and b"AddressSanitizer" in p.stderr, p.stderr
            report["cases"].append({"case": "asan-failing-control", "opt": opt})
    assert tracked == {path: digest(Path(path)) for path in tracked}, "production input changed during the gate"
    (args.out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS native legacy std ownership: {len(report['cases'])} contracts")


if __name__ == "__main__":
    main()
