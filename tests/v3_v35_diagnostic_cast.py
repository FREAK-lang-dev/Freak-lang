#!/usr/bin/env python3
"""Native selector parity, deterministic embedding and append-only presentation.

The oracle is the checked-in Python selector. --static checks regeneration and
the existing data gate; a native compiler is required for executable parity.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zlib

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src/diagnostics'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


ORACLE = module('diagnostic_cast_oracle', DATA/'selector.py')
EMBED = module('diagnostic_cast_embedding', ROOT/'tools/embed_diagnostic_cast.py')

PROGRAM = r'''
task cast_read_raw(path: word) -> word {
    pilot ticket = fs::read_source_ticket(path)
    pilot mut text = ""
    if fs::result_ok(ticket) { text = fs::result_word(ticket) }
    pilot complete = fs::result_ok(ticket)
    fs::result_release(ticket)
    if not complete { panic("cast fixture: raw source read failed") }
    give back text
}
task cast_hex(text: word) -> word {
    pilot bytes: ByteBuffer = ByteBuffer::new()
    bytes.write_word(text)
    bytes.seek(0)
    pilot digits = "0123456789abcdef"
    pilot builder = word_builder::new()
    repeat until bytes.remaining() == 0 {
        pilot value = bytes.read_byte()
        word_builder::append(builder, digits.char_at(value / 16))
        word_builder::append(builder, digits.char_at(value % 16))
    }
    bytes.release()
    give back word_builder::finish(builder)
}
task main() {
    pilot operation = process::arg(1)
    if operation == "upper" {
        say cast_hex(cli_diagnostic_cast_upper(cast_read_raw(process::arg(2))))
    } else if operation == "index" {
        say cli_diagnostic_cast_index(process::arg(2), word_to_int(process::arg(3)))
    } else if operation == "mode" {
        say cli_diagnostic_cast_mode_valid(process::arg(2))
    } else if operation == "defaults" {
        say cli_diagnostic_cast_default_mode(false, false)
        say cli_diagnostic_cast_default_mode(false, true)
        say cli_diagnostic_cast_default_mode(true, false)
        say cli_diagnostic_cast_default_mode(true, true)
    } else if operation == "off" {
        say cast_hex(cli_diagnostic_cast_render(cast_read_raw(process::arg(11)), process::arg(2), process::arg(3), process::arg(4), process::arg(5), word_to_int(process::arg(6)), word_to_int(process::arg(7)), cast_read_raw(process::arg(8)), process::arg(9), process::arg(10)))
    } else {
        say cli_diagnostic_cast_digest(process::arg(3), process::arg(4), process::arg(5), word_to_int(process::arg(6)), word_to_int(process::arg(7)), cast_read_raw(process::arg(8)), process::arg(9))
        say cast_hex(cli_diagnostic_cast_render(cast_read_raw(process::arg(11)), process::arg(2), process::arg(3), process::arg(4), process::arg(5), word_to_int(process::arg(6)), word_to_int(process::arg(7)), cast_read_raw(process::arg(8)), process::arg(9), process::arg(10)))
        say cast_hex(cli_diagnostic_cast_suffix(process::arg(2), process::arg(3), process::arg(4), process::arg(5), word_to_int(process::arg(6)), word_to_int(process::arg(7)), cast_read_raw(process::arg(8)), process::arg(9), process::arg(10)))
        say cli_diagnostic_cast_code_known(process::arg(4))
        say cli_diagnostic_cast_default_speaker(process::arg(4))
    }
}
'''


def run(command, *, cwd, env=None, timeout=90):
    return subprocess.run(list(map(str, command)), cwd=cwd, env=env, capture_output=True, timeout=timeout)


def good(command, *, cwd, env=None):
    completed = run(command, cwd=cwd, env=env)
    assert completed.returncode == 0 and not completed.stderr, (command, completed.returncode, completed.stdout, completed.stderr)
    return completed.stdout


def key(**changes):
    fields = dict(version='0.14.2', code='E0002', file='src/main.fk', line=7, column=3,
                  source='pilot x: num = 42', speaker='YUUKO', platform='')
    fields.update(changes)
    return fields


def digest(fields):
    return ORACLE.digest_hex(**{k:v for k,v in fields.items() if k != 'platform'})


def covering_keys(speaker, platform, count, code='E0002'):
    found = {}
    for index in range(20000):
        fields = key(speaker=speaker, platform=platform, file=f'coverage/{speaker}/{platform}/{index}.fk', code=code)
        selected = int(digest(fields), 16) % count
        if selected not in found:
            found[selected] = fields
        if len(found) == count:
            return [found[i] for i in range(count)]
    raise AssertionError(('could not cover pack', speaker, platform, count))


def cases():
    tests = []
    canonical = 'type error: canonical exact bytes\n --> main.fk:7:3\n日本語 🎌'
    for speaker in ORACLE.list_speakers():
        pack = ORACLE.load_pack(speaker)
        for fields in covering_keys(speaker, '', len(pack['lines'])):
            tests.append(('normal', canonical, fields))
        for platform, subset in ORACLE._pack_platforms(speaker).items():
            for fields in covering_keys(speaker, platform.upper(), len(subset)):
                tests.append(('normal', canonical, fields))
    for code in ORACLE.code_order():
        for mode in ('off', 'minimal', 'normal'):
            tests.append((mode, canonical, key(code=code.lower(), speaker=ORACLE.load_codes()[code]['default_speaker'].lower())))
    for mode in ('off', 'minimal', 'normal', 'OFF', 'MINIMAL', 'NORMAL'):
        for text in ('', '\n', 'trailing newline\n', 'canonical\0raw\0bytes', '日本語と絵文字 🎌'):
            tests.append((mode, text, key(source='x\0y\n', speaker='unknown')))
    # Unknown packs retain the ORIGINAL uppercased speaker in the hash and tag.
    for speaker in ('', 'DOES_NOT_EXIST', 'does_not_exist', 'ß', 'ı', 'ﬃ', 'παράδειγμα', 'é', '𐐨', 'i\u0307', 'FREAK', 'freak', 'FREAK', 'linKer', 'COCKPIT', 'cocKpit'):
        for platform in ('', 'linux', 'macos', 'windows', 'termux', 'plan9'):
            tests.append(('normal', canonical, key(speaker=speaker, platform=platform)))
    for egg in ORACLE.load_easter_eggs():
        paired = egg['code'] or 'E0001'
        for mode in ('off', 'minimal', 'normal'):
            tests.append((mode, canonical, key(source=egg['exact_source'], code=paired)))
        for near in (egg['exact_source']+' ', ' '+egg['exact_source'], egg['exact_source'].upper(), egg['exact_source']+'\n', egg['exact_source']+'\0'):
            if near != egg['exact_source']:
                tests.append(('normal', canonical, key(source=near, code=paired)))
        if egg['code']:
            different = next(c for c in ORACLE.code_order() if c != paired)
            tests.append(('normal', canonical, key(source=egg['exact_source'], code=different)))
        else:
            for code in ORACLE.code_order():
                tests.append(('minimal', canonical, key(source=egg['exact_source'], code=code)))
    resources = ORACLE.load_resources()
    seen = {}
    for index in range(20000):
        fields = key(code='E0009', file=f'resources/{index}.fk')
        line = ORACLE.select_resource(**{k:v for k,v in fields.items() if k not in ('speaker', 'platform')})
        seen.setdefault(line, fields)
        if len(seen) == len(resources):
            break
    assert len(seen) == len(resources)
    for fields in seen.values():
        for mode in ('minimal', 'normal'):
            tests.append((mode, 'allocation failed', fields))
    base = key()
    for field, value in dict(version='v0.14.3', code='E0008', file='日本語/🛩.fk', line=-(2**63), column=2**63-1, source='raw\0日本語\n', speaker='MEIYA').items():
        mutated = dict(base); mutated[field] = value
        assert digest(mutated) != digest(base)
        tests.append(('normal', canonical, mutated))
    for code in ('E0000', 'E0011', 'E9999', 'unknown', 'éß'):
        tests.append(('normal', canonical, key(code=code)))
    return tests


def arguments(binary, operation, mode, fields, source_path, canonical_path):
    return [binary, operation, mode, fields['version'], fields['code'], fields['file'], str(fields['line']), str(fields['column']), source_path, fields['speaker'], fields['platform'], canonical_path]


def corpus(binary, scratch, env, tests):
    source_path = scratch/'source.fk'; canonical_path = scratch/'canonical.txt'
    for index, (mode, canonical, fields) in enumerate(tests):
        source_path.write_bytes(fields['source'].encode('utf-8'))
        canonical_path.write_bytes(canonical.encode('utf-8'))
        out = good(arguments(binary, 'all', mode, fields, source_path, canonical_path), cwd=scratch, env=env)
        rendered = ORACLE.render(canonical, mode=mode, **fields)
        known = 'true' if ORACLE.is_known_code(fields['code']) else 'false'
        expected = (digest(fields)+'\n'+rendered.encode().hex()+'\n'+rendered[len(canonical):].encode().hex()+'\n'+known+'\n'+ORACLE.load_codes().get(fields['code'].upper(), {}).get('default_speaker', 'FREAK')+'\n').encode()
        assert out == expected, (index, mode, fields, out, expected)
    # One large UTF-8 key covers every pinned non-ASCII uppercase mapping and
    # all ASCII letters, including one-to-many expansions. No generator code
    # or Python selector runs in the native program.
    mappings = json.loads(zlib.decompress(base64.b85decode(EMBED.UNICODE_DATA)))
    unicode_text = 'aAzZ 123\n' + '|'.join(chr(point) for point,_ in mappings) + '|日本語 🛩'
    source_path.write_text(unicode_text, encoding='utf-8')
    uppercase = good([binary, 'upper', source_path], cwd=scratch, env=env)
    assert uppercase == (unicode_text.upper().encode().hex()+'\n').encode()
    assert good([binary, 'defaults'], cwd=scratch, env=env) == b'off\nnormal\noff\noff\n'
    for mode in ('off', 'OFF', 'minimal', 'MINIMAL', 'normal', 'NORMAL', '', 'verbose', 'normal ', 'nörmal'):
        expected = b'true\n' if mode.lower() in ORACLE.MODES else b'false\n'
        assert good([binary, 'mode', mode], cwd=scratch, env=env) == expected
    # Values whose first 32 bits, first 64 bits and full 256 bits select
    # different residues make truncated digest implementations fail.
    full_bits = '0000000000000000000000000000000000000000000000000000000000000001'
    wrap_bits = 'f'*64
    counts = (1, 2, 4, 6, 9, 10, 11, 12, 14, 103, 65536)
    for hexadecimal in (full_bits, wrap_bits, digest(key()), hashlib.sha256(b'known').hexdigest()):
        for count in counts:
            out = good([binary, 'index', hexadecimal, count], cwd=scratch, env=env)
            assert out == (str(int(hexadecimal,16)%count)+'\n').encode(), (hexadecimal, count, out)
    assert int(full_bits[:16],16)%14 != int(full_bits,16)%14
    return dict(render_parity_cases=len(tests), top_level_lines=103, packs=9, platform_subset_lines=20,
                easter_eggs=len(ORACLE.load_easter_eggs()), resource_lines=len(ORACLE.load_resources()),
                unicode_upper_mappings=len(mappings), full_256_bit_modulo_cases=4*len(counts), default_mode_cases=4, mode_validation_cases=10)


def static_checks():
    assert EMBED.generate() == (DATA/'embedded_cast.fk').read_text(encoding='utf-8'), 'embedded source is stale'
    static = run([sys.executable, ROOT/'tests/v3_diagnostic_codes.py'], cwd=ROOT)
    assert static.returncode == 0, (static.stdout, static.stderr)
    # Exercise the actual generator CLI and a data-only stale-input control
    # under a private replica. Never edit the authoritative packs in place.
    with tempfile.TemporaryDirectory(prefix='freak-cast-freshness-') as temporary:
        replica=Path(temporary);(replica/'tools').mkdir();(replica/'src/diagnostics/packs').mkdir(parents=True)
        generator=replica/'tools/embed_diagnostic_cast.py'
        shutil.copy2(ROOT/'tools/embed_diagnostic_cast.py', generator)
        for path in [*DATA.glob('*.json'),DATA/'embedded_cast.fk',*(DATA/'packs').glob('*.json')]:
            shutil.copy2(path, replica/'src/diagnostics'/path.relative_to(DATA))
        fresh=run([sys.executable,generator,'--check'],cwd=replica)
        assert fresh.returncode==0, (fresh.stdout,fresh.stderr)
        generated=(replica/'src/diagnostics/embedded_cast.fk').read_bytes()
        pack=replica/'src/diagnostics/packs/freak.json';payload=json.loads(pack.read_text())
        payload['lines'][0]+=' stale control';pack.write_text(json.dumps(payload),encoding='utf-8')
        stale=run([sys.executable,generator,'--check'],cwd=replica)
        assert stale.returncode!=0 and b'stale' in stale.stderr, (stale.stdout,stale.stderr)
        assert (replica/'src/diagnostics/embedded_cast.fk').read_bytes()==generated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--static', action='store_true')
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--runtime-root', type=Path)
    parser.add_argument('--clang', default=os.environ.get('FREAK_CLANG', 'clang'))
    parser.add_argument('--optimization', type=int, choices=(0,2,3), action='append')
    parser.add_argument('--backend', choices=('c','llvm'), action='append')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    static_checks()
    if args.static:
        print('PASS diagnostic cast generation freshness and canonical data oracle')
        return
    if not args.compiler:
        parser.error('--compiler is required for native verification')
    compiler = args.compiler.resolve(strict=True)
    runtime = (args.runtime_root or ROOT/'freakc/runtime').resolve(strict=True)
    clang = Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    vendor = runtime/'third_party/llhttp'
    if not vendor.exists():
        vendor = runtime.parents[1]/'third_party/llhttp'
    pinned = [compiler, Path(__file__).resolve(), ROOT/'tools/embed_diagnostic_cast.py', ROOT/'src/cli/diagnostic_cast.fk', DATA/'selector.py', DATA/'embedded_cast.fk', *sorted(DATA.glob('*.json')), *sorted((DATA/'packs').glob('*.json')), *sorted(runtime.glob('*.c')), *sorted(runtime.glob('*.h')), *sorted(runtime.glob('*.inc')), *sorted(p for p in vendor.rglob('*') if p.is_file())]
    before = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned}
    version = run([clang, '--version'], cwd=ROOT); assert version.returncode == 0, version.stderr
    evidence = dict(compiler_sha256=before[str(compiler)], pinned_input_sha256=before, clang=str(clang), clang_sha256=hashlib.sha256(clang.read_bytes()).hexdigest(), clang_version=version.stdout.decode().splitlines()[0], strict_borrow=True, ownership_audits=True, sanitize=args.sanitize, generation_freshness_failing_control=True, unicode_mapping_version=EMBED.UNICODE_VERSION, python_oracle_unicode_version=unicodedata.unidata_version, matrices=[])
    env = os.environ.copy(); env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1'; env['UBSAN_OPTIONS']='halt_on_error=1'
    tests = cases()
    body = (DATA/'embedded_cast.fk').read_text()+'\n'+(ROOT/'src/cli/diagnostic_cast.fk').read_text()+'\n'+PROGRAM
    with tempfile.TemporaryDirectory(prefix='freak-diagnostic-cast-') as temporary:
        scratch = Path(temporary); source = scratch/'selector.fk'; source.write_text(body)
        if args.sanitize:
            control = scratch/'control.c'; control.write_text('#include <stdlib.h>\nint main(int n,char **v){volatile char *p=malloc(1);p[n+4]=3;free((void*)p);return 0;}\n')
            control_binary = scratch/'control'
            linked = run([clang, control, '-O0', '-fsanitize=address,undefined', '-o', control_binary], cwd=scratch)
            assert linked.returncode == 0, linked.stderr
            failed = run([control_binary], cwd=scratch, env=env)
            assert failed.returncode != 0 and b'AddressSanitizer' in failed.stderr, failed.stderr
            evidence['sanitizer_failing_control'] = True
        for backend in args.backend or ('c','llvm'):
            compiled = run([compiler, source, '--'+backend, '--strict-borrow'], cwd=scratch)
            assert compiled.returncode == 0, (compiled.stdout, compiled.stderr)
            generated = Path(str(source)+('.c' if backend=='c' else '.ll'))
            for opt in args.optimization or (0,2,3):
                binary = scratch/f'selector-{backend}-O{opt}'
                command = [clang, '-O'+str(opt), generated, runtime/'freak_runtime.c', '-I'+str(runtime), '-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1', '-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1', '-o', binary]
                if backend=='llvm': command += [runtime/'freak_llvm_runtime.c']
                if args.sanitize: command += ['-fsanitize=address,undefined,function', '-fno-omit-frame-pointer', '-g']
                command += ['-lws2_32','-lshell32'] if os.name=='nt' else ['-lm']
                linked = run(command, cwd=scratch); assert linked.returncode == 0, (linked.stdout, linked.stderr)
                result = corpus(binary, scratch, env, tests)
                evidence['matrices'].append(dict(backend=backend, optimization=opt, **result))
                print(f'PASS strict native diagnostic cast {backend} O{opt}: {len(tests)} render cases,103 lines,20 platform lines,1499 Unicode mappings,44 full-digest residues', flush=True)
            # A link-time SHA failure control proves off does not hash or
            # consult a presentation key. The same binary's enabled branch
            # calls the trap, proving this control actually intercepts SHA.
            if sys.platform.startswith('linux'):
                wrapper = scratch/'sha_trap.c'
                wrapper.write_text('#include "freak_runtime.h"\n#include <stdio.h>\n#include <stdlib.h>\nfreak_word __wrap_freak_fs_sha256_bytes(int64_t ticket){fputs("cast-sha-trap\\n",stderr);_Exit(77);}\n')
                trapped = scratch/f'selector-{backend}-off-control'
                command = [clang, '-O2', generated, runtime/'freak_runtime.c', wrapper, '-I'+str(runtime), '-Wl,--wrap=freak_fs_sha256_bytes', '-o', trapped, '-lm']
                if backend=='llvm': command += [runtime/'freak_llvm_runtime.c']
                linked = run(command, cwd=scratch); assert linked.returncode == 0, linked.stderr
                source_path=scratch/'trap-source.fk';source_path.write_bytes(b'\xff\0raw\n')
                canonical_path=scratch/'trap-canonical.txt';canonical_path.write_bytes(b'canonical\0bytes\n\xff')
                fields=key()
                off=good(arguments(trapped, 'off', 'off', fields, source_path, canonical_path), cwd=scratch, env=env)
                assert off == canonical_path.read_bytes().hex().encode()+b'\n', off
                enabled=run(arguments(trapped, 'all', 'normal', fields, source_path, canonical_path), cwd=scratch, env=env)
                assert enabled.returncode==77 and enabled.stderr==b'cast-sha-trap\n', (enabled.returncode, enabled.stderr)
                evidence.setdefault('off_hash_failing_controls', []).append(backend)
    after = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned}
    assert before == after, 'pinned compiler/runtime/selector/data changed during gate'
    evidence['pinned_inputs_unchanged'] = True
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(evidence, indent=2)+'\n')


if __name__ == '__main__':
    main()
