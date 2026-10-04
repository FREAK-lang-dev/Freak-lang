#!/usr/bin/env python3
"""Closed typed parser/process/filesystem native gate. Source/pure preparation
alone is not native proof. Actual entry requires an explicit root lease token.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
OPTS = (0, 2, 3)
COUNTS = {"linux": 40, "darwin": 40, "win32": 38}
GRANT_NAME = "FREAK_TYPED_OS_ENTRY_ROOT_GRANT"
GRANT_VALUE = "typed-os-entry-native-gate-v1"
PREFIX = "typed-os-entry-execute stages=clean v9-restore=true old-seal=true fresh-module=true\n"
AUDIT_FLAGS = ("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
SANITIZER_FLAGS = ("-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer")
RUNTIME_SOURCES = ("freak_llvm_runtime.c", "freak_v4_word_runtime.c", "freak_v4_numeric_runtime.c", "freak_v4_unicode_runtime.c", "freak_v4_system_runtime.c", "freak_v4_panic_runtime.c", "freak_runtime.c")
RUNTIME_HEADERS = ("freak_runtime.h", "freak_v4_word_runtime.h", "freak_v4_numeric_runtime.h", "freak_v4_unicode_runtime.h", "freak_v4_unicode_lower_tables.h", "freak_v4_system_runtime.h", "freak_v4_panic_runtime.h")
CRATES = ("freak_span", "freak_diag", "freak_macro_api", "freak_arena", "freak_intern", "freak_session", "freak_target", "freak_lex", "freak_parse", "freak_expand", "freak_hir", "freak_resolve", "freak_ty", "freak_mir", "freak_mir_build", "freak_borrowck", "freak_codegen_llvm", "freak_query", "freak_driver", "freak_editor", "freak_snapshot", "freak_lsp")
OWNED_NAMES = ("src/compiler/v4/tests/typed_os_entry_contract_smoke.fk", "src/compiler/v4/tests/typed_os_entry_execute_smoke.fk", "tests/v4_typed_os_entry_codegen.py", "tests/test_v4_typed_os_entry_codegen.py", "src/compiler/v4/TYPED_OS_ENTRY_CONTRACT.md")
SUPPORT_NAME = "tests/v4_c_integer_runtime.py"
SUPPORT_SHA = "1fe37e9bf8f33c72193e85cfa87ffef78ed29bc0663ff447acd35a42f6fbd8e2"
GUARD_NAME = "src/compiler/v4/check_v4.py"
SCOPE = "Only prelude maybe<int>/result<word,word>, parser120/process202203/fs204 and zero-parameter native entry; broader sums/List/B01/native unwind remain fenced."
BRIDGE_COUNTS = {
    "argument_bounds": (6, 0, 0, 2), "argument_parser": (1, 1, 0, 1),
    "fs_discard_scopes": (1, 0, 2, 0), "fs_echo": (1, 0, 1, 0),
    "fs_loop_edges": (1, 0, 1, 0), "fs_move_rebind": (1, 0, 4, 0),
    "fs_nul_path": (0, 0, 1, 0), "fs_parse": (1, 1, 1, 0),
    "process_count_only": (0, 0, 0, 1),
}

PROGRAMS = {'fs_discard_scopes': 'task main() -> int {\n'
                      '    check result process::arg(1) {\n'
                      '        ok(path) -> {\n'
                      '            pilot saved = path.clone()\n'
                      '            fs::read(path)\n'
                      '            check result fs::read(path) {\n'
                      '                ok(_) -> { say "ok-ignored" }\n'
                      '                err(_) -> { say "err-ignored" }\n'
                      '            }\n'
                      '            if path != saved { give back 71 }\n'
                      '            give back 0\n'
                      '        }\n'
                      '        err(_) -> { give back 72 }\n'
                      '    }\n'
                      '    give back 70\n'
                      '}\n',
 'fs_echo': 'task relay_result(value: result<word,word>) -> result<word,word> {\n'
            '    give back value\n'
            '}\n'
            '\n'
            'task main() -> int {\n'
            '    check result process::arg(1) {\n'
            '        ok(path) -> {\n'
            '            pilot saved = path.clone()\n'
            '            pilot contents = relay_result(fs::read(path))\n'
            '            if path != saved { give back 71 }\n'
            '            check result contents {\n'
            '                ok(text) -> { say "ok"; say text; give back 0 }\n'
            '                err(message) -> {\n'
            '                    if message.length() < 1 { give back 72 }\n'
            '                    say "err"\n'
            '                    say message\n'
            '                    give back 2\n'
            '                }\n'
            '            }\n'
            '        }\n'
            '        err(message) -> {\n'
            '            if message.length() < 1 { give back 73 }\n'
            '            say "arg-error"\n'
            '            give back 3\n'
            '        }\n'
            '    }\n'
            '    give back 70\n'
            '}\n',
 'fs_loop_edges': 'task main() -> int {\n'
                  '    check result process::arg(1) {\n'
                  '        ok(path) -> {\n'
                  '            pilot saved = path.clone()\n'
                  '            pilot mut attempts = 0\n'
                  '            repeat until attempts >= 3 {\n'
                  '                attempts += 1\n'
                  '                pilot pending = fs::read(path)\n'
                  '                if attempts == 1 { continue }\n'
                  '                check result pending {\n'
                  '                    ok(_) -> {}\n'
                  '                    err(_) -> {}\n'
                  '                }\n'
                  '                if attempts == 2 { break }\n'
                  '            }\n'
                  '            if path != saved { give back 71 }\n'
                  '            say "loop-done"\n'
                  '            give back 0\n'
                  '        }\n'
                  '        err(_) -> { give back 72 }\n'
                  '    }\n'
                  '    give back 70\n'
                  '}\n',
 'fs_move_rebind': 'task relay_result(value: result<word,word>) -> result<word,word> {\n'
                   '    give back value\n'
                   '}\n'
                   '\n'
                   'task main() -> int {\n'
                   '    check result process::arg(1) {\n'
                   '        ok(path) -> {\n'
                   '            pilot saved = path.clone()\n'
                   '            pilot mut first = fs::read(path)\n'
                   '            pilot mut moved = relay_result(first)\n'
                   '            if path.contains("rebind-ok") { first = fs::read(path) } else { '
                   'first = fs::read(path) }\n'
                   '            moved = fs::read(path)\n'
                   '            if path != saved { give back 71 }\n'
                   '            check result moved {\n'
                   '                ok(_) -> { say "ok-rebind"; give back 0 }\n'
                   '                err(_) -> { say "err-rebind"; give back 0 }\n'
                   '            }\n'
                   '        }\n'
                   '        err(_) -> { give back 72 }\n'
                   '    }\n'
                   '    give back 70\n'
                   '}\n',
 'fs_nul_path': 'task main() -> int {\n'
                '    pilot path = "a\\0b"\n'
                '    pilot saved = path.clone()\n'
                '    pilot result = fs::read(path)\n'
                '    if path != saved { give back 71 }\n'
                '    check result result {\n'
                '        ok(_) -> { give back 72 }\n'
                '        err(message) -> { say message; give back 0 }\n'
                '    }\n'
                '    give back 70\n'
                '}\n',
 'fs_parse': 'task relay_result(value: result<word,word>) -> result<word,word> {\n'
             '    give back value\n'
             '}\n'
             '\n'
             'task relay_maybe(value: maybe<int>) -> maybe<int> { give back value }\n'
             '\n'
             'task main() -> int {\n'
             '    check result process::arg(1) {\n'
             '        ok(path) -> {\n'
             '            pilot saved = path.clone()\n'
             '            check result relay_result(fs::read(path)) {\n'
             '                ok(text) -> {\n'
             '                    if path != saved { give back 71 }\n'
             '                    pilot saved_text = text.clone()\n'
             '                    pilot number = relay_maybe(text.to_int())\n'
             '                    if text != saved_text { give back 72 }\n'
             '                    say text\n'
             '                    check number {\n'
             '                        got value -> { say value; give back 0 }\n'
             '                        nobody -> { say "nobody"; give back 1 }\n'
             '                    }\n'
             '                }\n'
             '                err(message) -> {\n'
             '                    if message.length() < 1 { give back 73 }\n'
             '                    say "read-error"\n'
             '                    give back 2\n'
             '                }\n'
             '            }\n'
             '        }\n'
             '        err(message) -> {\n'
             '            if message.length() < 1 { give back 74 }\n'
             '            say "arg-error"\n'
             '            give back 3\n'
             '        }\n'
             '    }\n'
             '    give back 70\n'
             '}\n',
 'process_count_only': '-- Deliberately no Word nodes or formatting calls: descriptor203 still '
                       'needs setup.\n'
                       'task main() -> int { give back process::args_count() }\n',
 'argument_parser': 'task relay_result(value: result<word,word>) -> result<word,word> { give back '
                    'value }\n'
                    'task relay_maybe(value: maybe<int>) -> maybe<int> { give back value }\n'
                    'task main() -> int {\n'
                    '    say process::args_count()\n'
                    '    check result relay_result(process::arg(1)) {\n'
                    '        ok(text) -> {\n'
                    '            pilot saved = text.clone()\n'
                    '            pilot parsed = relay_maybe(text.to_int())\n'
                    '            if text != saved { give back 71 }\n'
                    '            say text\n'
                    '            check parsed {\n'
                    '                got number -> { say number; give back 0 }\n'
                    '                nobody -> { say "nobody"; give back 2 }\n'
                    '            }\n'
                    '        }\n'
                    '        err(message) -> {\n'
                    '            if message.length() < 1 { give back 72 }\n'
                    '            say "arg-error"\n'
                    '            give back 3\n'
                    '        }\n'
                    '    }\n'
                    '    give back 70\n'
                    '}\n',
 'argument_bounds': 'task relay(value: result<word,word>) -> result<word,word> { give back value '
                    '}\n'
                    'task emit(value: result<word,word>) -> void {\n'
                    '    check result value {\n'
                    '        ok(text) -> { say text }\n'
                    '        err(message) -> { say message }\n'
                    '    }\n'
                    '}\n'
                    'task main() -> int {\n'
                    '    say process::args_count()\n'
                    '    check result process::arg(0) {\n'
                    '        ok(program) -> { if program.length() < 1 { give back 71 }; say '
                    '"index0" }\n'
                    '        err(_) -> { give back 72 }\n'
                    '    }\n'
                    '    pilot first = process::arg(1)\n'
                    '    pilot second = process::arg(1)\n'
                    '    emit(relay(first))\n'
                    '    emit(relay(second))\n'
                    '    emit(process::arg(-1))\n'
                    '    emit(process::arg(9223372036854775807))\n'
                    '    emit(process::arg(process::args_count()))\n'
                    '    give back 0\n'
                    '}\n'}

CASES = ({'id': 'echo-empty',
  'program': 'fs_echo',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'empty 雪.txt', 'bytes_hex': ''},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6f6b0a0a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'echo-sized-utf8-nul',
  'program': 'fs_echo',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file',
              'relative_path': 'text 中😀.bin',
              'bytes_hex': '4100c3a9e4b8adf09f9880'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6f6b0a4100c3a9e4b8adf09f98800a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'echo-embedded-newline',
  'program': 'fs_echo',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file',
              'relative_path': 'newline.txt',
              'bytes_hex': '6c696e650a76616c7565'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6f6b0a6c696e650a76616c75650a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'echo-missing',
  'program': 'fs_echo',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'absent', 'relative_path': 'missing.txt'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6572720a636f756c64206e6f74206f70656e2066696c6573797374656d2066696c650a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'echo-directory',
  'program': 'fs_echo',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'directory', 'relative_path': 'directory'},
  'platforms': ['linux', 'darwin'],
  'stdout_hex': '6572720a66696c6573797374656d2070617468206973206e6f742061207265616461626c6520726567756c61722066696c650a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'echo-fifo',
  'program': 'fs_echo',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'fifo', 'relative_path': 'pipe'},
  'platforms': ['linux', 'darwin'],
  'stdout_hex': '6572720a66696c6573797374656d2070617468206973206e6f742061207265616461626c6520726567756c61722066696c650a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'echo-invalid-utf8',
  'program': 'fs_echo',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'invalid.bin', 'bytes_hex': 'eda080'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6572720a66696c6573797374656d2066696c65206973206e6f742076616c6964205554462d380a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'echo-empty-path',
  'program': 'fs_echo',
  'argv': [''],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6572720a66696c6573797374656d207061746820697320656d7074790a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'echo-missing-argument',
  'program': 'fs_echo',
  'argv': [],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6172672d6572726f720a',
  'stderr_hex': '',
  'status': 3},
 {'id': 'parse-zero',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'zero 雪.txt', 'bytes_hex': '30'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '300a300a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'parse-leading-plus',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file',
              'relative_path': 'leading-plus 雪.txt',
              'bytes_hex': '2b3030303432'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '2b30303034320a34320a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'parse-minimum',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file',
              'relative_path': 'minimum 雪.txt',
              'bytes_hex': '2d39323233333732303336383534373735383038'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '2d393232333337323033363835343737353830380a2d393232333337323033363835343737353830380a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'parse-maximum',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file',
              'relative_path': 'maximum 雪.txt',
              'bytes_hex': '39323233333732303336383534373735383037'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '393232333337323033363835343737353830370a393232333337323033363835343737353830370a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'parse-empty',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'empty 雪.txt', 'bytes_hex': ''},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '0a6e6f626f64790a',
  'stderr_hex': '',
  'status': 1},
 {'id': 'parse-sized-nul',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'sized-nul 雪.txt', 'bytes_hex': '340032'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '3400320a6e6f626f64790a',
  'stderr_hex': '',
  'status': 1},
 {'id': 'parse-junk',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'junk 雪.txt', 'bytes_hex': '343278'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '3432780a6e6f626f64790a',
  'stderr_hex': '',
  'status': 1},
 {'id': 'parse-overflow',
  'program': 'fs_parse',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file',
              'relative_path': 'overflow 雪.txt',
              'bytes_hex': '39323233333732303336383534373735383038'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '393232333337323033363835343737353830380a6e6f626f64790a',
  'stderr_hex': '',
  'status': 1},
 {'id': 'discard-ok',
  'program': 'fs_discard_scopes',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'discard-ok', 'bytes_hex': ''},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6f6b2d69676e6f7265640a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'rebind-ok',
  'program': 'fs_move_rebind',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'rebind-ok', 'bytes_hex': ''},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6f6b2d726562696e640a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'loop-ok',
  'program': 'fs_loop_edges',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'regular-file', 'relative_path': 'loop-ok', 'bytes_hex': ''},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6c6f6f702d646f6e650a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'discard-err',
  'program': 'fs_discard_scopes',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'absent', 'relative_path': 'discard-err'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6572722d69676e6f7265640a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'rebind-err',
  'program': 'fs_move_rebind',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'absent', 'relative_path': 'rebind-err'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6572722d726562696e640a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'loop-err',
  'program': 'fs_loop_edges',
  'argv': ['@fixture-path'],
  'fixture': {'kind': 'absent', 'relative_path': 'loop-err'},
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '6c6f6f702d646f6e650a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'count-program-only',
  'program': 'process_count_only',
  'argv': [],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '',
  'stderr_hex': '',
  'status': 1},
 {'id': 'count-one-empty',
  'program': 'process_count_only',
  'argv': [''],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '',
  'stderr_hex': '',
  'status': 2},
 {'id': 'count-five-mixed',
  'program': 'process_count_only',
  'argv': ['', 'space value', 'quote"value', 'backslash\\', 'Aé中😀'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '',
  'stderr_hex': '',
  'status': 6},
 {'id': 'nul-path',
  'program': 'fs_nul_path',
  'argv': [],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '66696c6573797374656d207061746820636f6e7461696e73204e554c0a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'argument-zero',
  'program': 'argument_parser',
  'argv': ['0'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a300a300a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'argument-empty',
  'program': 'argument_parser',
  'argv': [''],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a0a6e6f626f64790a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'argument-minimum',
  'program': 'argument_parser',
  'argv': ['-9223372036854775808'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a2d393232333337323033363835343737353830380a2d393232333337323033363835343737353830380a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'argument-maximum',
  'program': 'argument_parser',
  'argv': ['9223372036854775807'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a393232333337323033363835343737353830370a393232333337323033363835343737353830370a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'argument-leading-plus',
  'program': 'argument_parser',
  'argv': ['+00042'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a2b30303034320a34320a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'argument-junk',
  'program': 'argument_parser',
  'argv': ['42x'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a3432780a6e6f626f64790a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'argument-space',
  'program': 'argument_parser',
  'argv': [' 42'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a2034320a6e6f626f64790a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'argument-overflow',
  'program': 'argument_parser',
  'argv': ['9223372036854775808'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a393232333337323033363835343737353830380a6e6f626f64790a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'argument-unicode-digit',
  'program': 'argument_parser',
  'argv': ['٤'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320ad9a40a6e6f626f64790a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'argument-sign-only',
  'program': 'argument_parser',
  'argv': ['+'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a2b0a6e6f626f64790a',
  'stderr_hex': '',
  'status': 2},
 {'id': 'argument-missing',
  'program': 'argument_parser',
  'argv': [],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '310a6172672d6572726f720a',
  'stderr_hex': '',
  'status': 3},
 {'id': 'bounds-empty',
  'program': 'argument_bounds',
  'argv': [''],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a696e646578300a0a0a70726f6365737320617267756d656e7420696e646578206973206f7574206f662072616e67650a70726f6365737320617267756d656e7420696e646578206973206f7574206f662072616e67650a70726f6365737320617267756d656e7420696e646578206973206f7574206f662072616e67650a',
  'stderr_hex': '',
  'status': 0},
 {'id': 'bounds-unicode',
  'program': 'argument_bounds',
  'argv': ['Aé中😀'],
  'fixture': None,
  'platforms': ['linux', 'darwin', 'win32'],
  'stdout_hex': '320a696e646578300a41c3a9e4b8adf09f98800a41c3a9e4b8adf09f98800a70726f6365737320617267756d656e7420696e646578206973206f7574206f662072616e67650a70726f6365737320617267756d656e7420696e646578206973206f7574206f662072616e67650a70726f6365737320617267756d656e7420696e646578206973206f7574206f662072616e67650a',
  'stderr_hex': '',
  'status': 0})

DESCRIPTOR_SOURCE = '''task inspect(path: word) -> int {
    pilot contents = fs::read(path)
    pilot parsed = path.to_int()
    pilot argument = process::arg(1)
    pilot count = process::args_count()
    check result argument { ok(_) -> {} err(_) -> {} }
    check result contents { ok(_) -> {} err(_) -> {} }
    check parsed { got _ -> {} nobody -> {} }
    give back count
}
task main() -> int { give back inspect("4") }
'''


def contract_cases():
    rows = []
    def add(name, mode, source, expected="", identity=""):
        rows.append({"name": name, "mode": mode, "source": source,
                     "expected": expected, "identity": identity})
    for mode in ("descriptors", "identity", "op", "result", "abi", "arity", "loan-kind", "loan-type"):
        add(mode, mode, DESCRIPTOR_SOURCE, identity="builtin::system::process_arg")
    add("live-identity", "live-identity", DESCRIPTOR_SOURCE,
        "invalid scalar sum intrinsic identity", "builtin::system::process_arg")
    add("count-only", "setup", "task main() -> int { give back process::args_count() }\n")
    add("process-in-helper", "setup", "task count() -> int { give back process::args_count() }\ntask main() -> int { give back count() }\n")
    add("parser-fs-library", "no-setup", "task inspect(path: word) -> maybe<int> { pilot pending = fs::read(path); give back path.to_int() }\n")
    add("qualified-process", "shadow", "task process::arg(index: int) -> int { give back index }\ntask main() -> int { give back process::arg(7) }\n", identity="builtin::system::process_arg")
    add("qualified-fs", "shadow", "task fs::read(path: word) -> word { give back path }\ntask main() -> int { pilot text = fs::read(\"ordinary\"); say text; give back 0 }\n", identity="builtin::system::fs_read")
    add("parameter-process", "ordinary-native-reject", "task inspect(process: int) -> int { give back process::arg(1) }\ntask main() -> int { give back inspect(0) }\n", "native rvalue not yet supported: Unknown", "builtin::system::process_arg")
    add("local-fs", "ordinary-native-reject", "task main() -> int { pilot fs = 1; pilot value = fs::read(\"x\"); give back 0 }\n", "native rvalue not yet supported: Unknown", "builtin::system::fs_read")
    add("root-process", "ordinary-native-reject", "fixed pilot process: int = 1\ntask main() -> int { give back process::arg(1) }\n", "native rvalue not yet supported: Unknown", "builtin::system::process_arg")
    add("import-fs", "ordinary-native-reject", "use user::filesystem as fs\ntask main() -> int { pilot value = fs::read(\"x\"); give back 0 }\n", "native rvalue not yet supported: Unknown", "builtin::system::fs_read")
    add("named-process", "admission-reject", "task main() -> int { pilot value = process::arg(index: 1); give back 0 }\n")
    add("named-fs", "admission-reject", "task main() -> int { pilot value = fs::read(path: \"x\"); give back 0 }\n")
    add("process-library", "native-reject", "task count() -> int { give back process::args_count() }\n", "native typed process operations require a generated zero-argument entry")
    add("parameter-main", "native-reject", "task main(seed: int) -> int { give back seed }\n", "native main parameters are not yet supported")
    add("foreign-maybe", "ffi-native-reject", "extern [C] { task take(value: maybe<int>) -> int }\ntask main() -> int { give back 0 }\n", "native scalar sum C ABI is not yet supported")
    add("raw-maybe", "native-reject", "task inspect(value: *mut maybe<int>) -> void {}\ntask main() -> int { give back 0 }\n", "native scalar sum raw storage contracts are not yet supported")
    add("private-fs-symbol", "native-reject", "extern [C] { task freak_v4_fs_read() -> std::ffi::c_isize }\ntask main() -> int { give back 0 }\n", "native private runtime symbol conflict: @freak_v4_fs_read")
    return tuple(rows)


def require(condition, message):
    if not condition: raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""): digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def data_digest():
    return hashlib.sha256(canonical_bytes({"programs": PROGRAMS, "cases": CASES, "contracts": contract_cases(), "bridge_counts": BRIDGE_COUNTS})).hexdigest()


def validate_data():
    require(len(PROGRAMS) == 9 and len(CASES) == 40 and len(contract_cases()) == 25, "closed scenario cardinality")
    require(len({case["id"] for case in CASES}) == 40, "duplicate scenario")
    require({case["program"] for case in CASES} == set(PROGRAMS), "program/closed scenario mismatch")
    require({host: sum(host in case["platforms"] for case in CASES) for host in COUNTS} == COUNTS, "closed host scenario count")
    for case in CASES:
        require(set(case) == {"id", "program", "argv", "fixture", "platforms", "stdout_hex", "stderr_hex", "status"}, "scenario schema drift")
        require(type(case["status"]) is int and 0 <= case["status"] <= 255 and case["stderr_hex"] == "", "semantic status/channel drift")
        require(all(type(value) is str and "\0" not in value for value in case["argv"]), "OS argv cannot carry NUL")
        require(not any(p not in COUNTS for p in case["platforms"]), "unknown host")
        for channel in ("stdout_hex", "stderr_hex"):
            raw = bytes.fromhex(case[channel]); raw.decode("utf-8")
            require(b"\r" not in raw, "line normalization cannot hide intended CR bytes")
        fixture = case["fixture"]
        if fixture is not None:
            require(set(fixture) in ({"kind", "relative_path"}, {"kind", "relative_path", "bytes_hex"}), "fixture schema")
            path = Path(fixture["relative_path"])
            require(path.name == fixture["relative_path"] and path.name not in ("", ".", ".."), "fixture must be one safe name")
            require(fixture["kind"] in ("regular-file", "absent", "directory", "fifo"), "unknown fixture kind")
            if fixture["kind"] == "regular-file": bytes.fromhex(fixture["bytes_hex"])
    require(data_digest() == DATA_SHA, "closed sources/oracles/contract table changed")


def assert_exact(actual, status, stdout, stderr, host):
    require(type(actual.returncode) is int and type(actual.stdout) is str and type(actual.stderr) is str, "unexpected result shape")
    observed_stdout = actual.stdout.encode("utf-8")
    observed_stderr = actual.stderr.encode("utf-8")
    if host == "win32":
        observed_stdout = observed_stdout.replace(b"\r\n", b"\n")
        observed_stderr = observed_stderr.replace(b"\r\n", b"\n")
    require((actual.returncode, observed_stdout, observed_stderr) == (status, stdout, stderr), "exact status/stdout/stderr oracle failed")


def extract_module(actual, host):
    text = actual.stdout.replace("\r\n", "\n") if host == "win32" else actual.stdout
    begin, end = "@@LLVM-MODULE-BEGIN\n", "@@LLVM-MODULE-END\n"
    require(actual.returncode == 0 and actual.stderr == "" and text.startswith(PREFIX + begin) and text.endswith(end), "typed compiler protocol")
    require(text.count(begin) == text.count(end) == 1, "module marker uniqueness")
    module = text[len(PREFIX + begin):-len(end)]
    require(module.strip() != "", "empty typed module")
    return module


def validate_module(module, program):
    require(program in PROGRAMS, "unknown module/program")
    wrapper = re.findall(r"define i32 @main\([^\n]*\) \{([^}]+)\}", module, re.S)
    require(len(wrapper) == 1 and wrapper[0].count("call void @freak_llvm_setup_args(") == 1, "one native wrapper/legacy setup")
    main_calls = list(re.finditer(r"(?m)^\s*%[\w.]+ = call (?:ccc )?i64 @freak\.user\.main\(\)\s*$", wrapper[0]))
    require(len(main_calls) == 1, "one default-C zero-argument user main call")
    arg_count, parser_count, fs_count, argc_count = BRIDGE_COUNTS[program]
    needs_process = arg_count + argc_count > 0
    setup = "call void @freak_v4_process_setup_args(i64 %argc.ext, i64 %argv.int)"
    require(module.count("call void @freak_v4_process_setup_args(") == int(needs_process) and
            module.count("declare void @freak_v4_process_setup_args(i64, i64)") == int(needs_process), "module-level typed setup once")
    if needs_process:
        require(wrapper[0].count(setup) == 1 and wrapper[0].index("call void @freak_llvm_setup_args(") < wrapper[0].index(setup) < main_calls[0].start(), "entry setup order")
    definitions = {"%freak_result_word_word": "%freak_result_word_word = type { i1, i64 }", "%freak_maybe_int": "%freak_maybe_int = type { i1, i64 }"}
    for carrier, definition in definitions.items():
        require(module.count(definition) == int(carrier in module), "distinct exact carrier definition")
    symbols = (("freak_v4_word_parse_int_checked", parser_count), ("freak_v4_process_arg_checked", arg_count), ("freak_v4_fs_read", fs_count))
    for symbol, expected_count in symbols:
        calls = list(re.finditer(r"call void @" + symbol + r"\(i64 [^,\n]+, ptr (%[\w.]+), ptr (%[\w.]+)\)", module))
        referenced = "@" + symbol in module
        require(module.count("declare void @" + symbol + "(i64, ptr, ptr)") == int(referenced), "exact private void prototype")
        require(len(calls) == expected_count == module.count("call void @" + symbol + "("), "closed bridge call prototype/evaluation count")
        require("call i64 @" + symbol not in module and "call %freak_" + symbol not in module, "no fabricated bridge return ABI")
        for call in calls:
            tag, payload = call.groups()
            require(tag != payload and tag.startswith("%sum.out.") and payload.startswith("%sum.out."), "two distinct closed output slots")
            for slot in (tag, payload):
                require(module.count(slot + " = alloca i64") == 1 and module.count("load i64, ptr " + slot + "\n") == 1, "one static slot and explicit payload/tag load")
                require(module.rfind("store i64 0, ptr " + slot, 0, call.start()) >= 0, "slot initialized before bridge")
    require(module.count("call i64 @freak_v4_process_args_count()") == argc_count and
            module.count("declare i64 @freak_v4_process_args_count()") == int(argc_count > 0), "exact scalar count calls/prototype")
    legacy_free, unused_declarations = re.subn(r"(?m)^declare i64 @freak_v4_word_to_int\(i64\)\n", "", module)
    require(unused_declarations <= 1, "one unused legacy word conversion prototype")
    require("@freak_v4_process_arg(" not in module and "@freak_fs_read_checked" not in module and "@freak_v4_word_to_int" not in legacy_free, "legacy helper cannot substitute typed bridge")


def source_names(root=None):
    if root is None: root = ROOT
    names = [*OWNED_NAMES, SUPPORT_NAME, GUARD_NAME,
             *("src/compiler/v4/crates/" + crate + "/src/lib.fk" for crate in CRATES),
             *("freakc/runtime/" + name for name in (*RUNTIME_SOURCES, *RUNTIME_HEADERS))]
    names += [str(path.relative_to(root)).replace("\\", "/") for path in sorted((root / "freakc").rglob("*.py"))]
    require(len(names) == len(set(names)), "source inventory duplicate")
    require(len(names) <= 256 and any(name == "freakc/__main__.py" for name in names), "bounded complete bootstrap Python inventory")
    for name in names:
        path = root / name
        require(path.is_file() and not path.is_symlink(), "source missing or alias: " + name)
    return tuple(names)


def source_hashes(): return {name: sha(ROOT / name) for name in source_names()}


def load_support(frozen, names, role):
    path = frozen / SUPPORT_NAME
    require(sha(path) == SUPPORT_SHA, "accepted guard/retention support identity")
    name = "v4_typed_os_support_" + role
    require(name not in sys.modules, "fresh support namespace")
    module = types.ModuleType(name); module.__file__ = str(ROOT / SUPPORT_NAME)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), module.__file__, "exec"), module.__dict__)
    module.OWNED_SOURCE_NAMES = tuple(n for n in names if n != GUARD_NAME)
    module.source_hashes = source_hashes
    module.COMPILE_SECONDS = 120
    module.COMPILE_MIB = 1024 if role == "bootstrap" else 512
    module.RUN_SECONDS = 60 if role == "compiler" else 30
    module.RUN_MIB = 64 if role == "compiler" else 128
    module.OUTPUT_MIB = 1
    return module


def load_checks(frozen):
    require(sys.dont_write_bytecode, "native gate requires Python -B")
    reject_bytecode(frozen)
    require(not any(name == "freakc" or name.startswith("freakc.") for name in sys.modules), "bootstrap import namespace already populated")
    name = "v4_typed_os_frozen_checks"
    require(name not in sys.modules, "fresh absent guard namespace")
    module = types.ModuleType(name); module.__file__ = str(frozen / GUARD_NAME)
    sys.modules[name] = module
    sys.path.insert(0, str(frozen))
    exec(compile((frozen / GUARD_NAME).read_bytes(), module.__file__, "exec"), module.__dict__)
    require(tuple(module.CRATE_ORDER) == CRATES and tuple(module.V4_NATIVE_RUNTIME_SOURCES) == RUNTIME_SOURCES, "compiler/runtime closed inventories")
    for key, value in tuple(sys.modules.items()):
        if key == "freakc" or key.startswith("freakc."):
            file = getattr(value, "__file__", None)
            require(file is not None and Path(file).resolve().is_relative_to(frozen.resolve()), "foreign bootstrap module import")
    return module


def reject_bytecode(frozen):
    require(not any(path.name == "__pycache__" or path.suffix in (".pyc", ".pyo") for path in frozen.rglob("*")),
            "frozen bootstrap bytecode/cache is forbidden")


@contextmanager
def sanitizer_environment(support, sanitize, exitcode=86):
    require(type(exitcode) is int and exitcode in (85, 86), "closed sanitizer exit code")
    with support.sanitizer_environment(False):
        if sanitize:
            os.environ["ASAN_OPTIONS"] = f"halt_on_error=1:detect_leaks=1:exitcode={exitcode}"
            os.environ["UBSAN_OPTIONS"] = f"halt_on_error=1:print_stacktrace=1:exitcode={exitcode}"
        yield


def host_target():
    machine = platform.machine().lower()
    targets = {("linux", "x86_64"): "x86_64-unknown-linux-gnu", ("linux", "amd64"): "x86_64-unknown-linux-gnu", ("linux", "aarch64"): "aarch64-unknown-linux-gnu", ("linux", "arm64"): "aarch64-unknown-linux-gnu", ("darwin", "aarch64"): "aarch64-apple-darwin", ("darwin", "arm64"): "aarch64-apple-darwin", ("win32", "x86_64"): "x86_64-w64-windows-gnu", ("win32", "amd64"): "x86_64-w64-windows-gnu"}
    require((sys.platform, machine) in targets, "registered executed-host TargetSpec required")
    return targets[(sys.platform, machine)]


def fixture_facts(directory, host):
    facts = {}
    for case in CASES:
        if host not in case["platforms"] or case["fixture"] is None: continue
        fixture = case["fixture"]; path = directory / fixture["relative_path"]
        kind = fixture["kind"]
        if kind == "absent": require(not path.exists(), "absent filesystem fixture materialized")
        elif kind == "regular-file": require(path.is_file() and not path.is_symlink() and path.read_bytes() == bytes.fromhex(fixture["bytes_hex"]), "exact binary fixture")
        elif kind == "directory": require(path.is_dir() and not path.is_symlink(), "directory fixture")
        elif kind == "fifo":
            import stat
            require(stat.S_ISFIFO(path.lstat().st_mode), "real nonblocking FIFO fixture")
        facts[fixture["relative_path"]] = {"kind": kind, "sha256": sha(path) if kind == "regular-file" else None}
    require(set(path.name for path in directory.iterdir()) == {name for name, row in facts.items() if row["kind"] != "absent"}, "closed fixture tree")
    return facts


def create_fixtures(directory, host):
    directory.mkdir(exist_ok=False)
    specifications = {}
    for case in CASES:
        if host in case["platforms"] and case["fixture"] is not None:
            fixture = case["fixture"]
            name = fixture["relative_path"]
            require(name not in specifications or specifications[name] == fixture, "conflicting shared fixture")
            specifications[name] = fixture
    for name, fixture in specifications.items():
        path = directory / name
        if fixture["kind"] == "regular-file": path.write_bytes(bytes.fromhex(fixture["bytes_hex"]))
        elif fixture["kind"] == "directory": path.mkdir()
        elif fixture["kind"] == "fifo": os.mkfifo(path)
    return fixture_facts(directory, host)


def validate_capability(actual, kind, host):
    if kind in ("C", "LLVM"):
        assert_exact(actual, 87 if kind == "C" else 86, b"", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode(), host)
        return
    require(host == "linux" and actual.returncode == (86 if kind == "asan-heap" else 85) and actual.stdout == "", "sanitizer exact death status/channel")
    text = actual.stderr
    if kind == "asan-heap": require("ERROR: AddressSanitizer: heap-buffer-overflow" in text and "SUMMARY: AddressSanitizer: heap-buffer-overflow" in text, "real ASan heap diagnostic")
    else: require(kind in ("ubsan-overflow", "ubsan-shift") and "runtime error:" in text and "SUMMARY: UndefinedBehaviorSanitizer:" in text and ("signed integer overflow" if kind == "ubsan-overflow" else "shift exponent") in text, "real UBSan diagnostic")

CAPABILITY_SOURCE = r'''#include "freak_runtime.h"
#include "freak_v4_word_runtime.h"
#include <stdint.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc != 2) return 9;
    if (!strcmp(argv[1], "C")) {
        volatile freak_word value = freak_word_from_int(1234);
        (void)value;
        return 0;
    }
    if (!strcmp(argv[1], "LLVM")) {
        volatile int64_t value = freak_v4_word_from_int(1234);
        (void)value;
        return 0;
    }
    if (!strcmp(argv[1], "asan-heap")) {
        volatile char *value = malloc(1);
        if (!value) return 10;
        value[0] = 1;
        return value[1];
    }
    if (!strcmp(argv[1], "ubsan-overflow")) {
        volatile int value = INT_MAX;
        volatile int one = 1;
        return value + one;
    }
    if (!strcmp(argv[1], "ubsan-shift")) {
        volatile unsigned value = 1;
        volatile unsigned shift = sizeof(unsigned) * CHAR_BIT;
        return value << shift;
    }
    return 11;
}
'''


def observed(result):
    return {"status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def result_object(row):
    require(type(row) is dict and set(row) == {"status", "stdout", "stderr"}, "closed observed result schema")
    return types.SimpleNamespace(returncode=row["status"], stdout=row["stdout"], stderr=row["stderr"])


def validate_report(report, sanitize):
    validate_data()
    host = report.get("platform")
    require(host in COUNTS and report.get("sanitized") is sanitize and (not sanitize or host == "linux"), "host/mode report boundary")
    require(report.get("complete") is True and report.get("data_sha256") == DATA_SHA and report.get("scope") == SCOPE, "no complete proof without closed protocol")
    require(report.get("compiler_process_contract") == {"seconds":60, "memory_mib":64, "live_handles":1024}, "SDK contract changed")
    require(report.get("guarded_job_counts") == {"bootstrap":2, "compiler":34,
            "native_and_clang":53 + 3 * COUNTS[host] + (15 if sanitize else 6)}, "exact guarded stage counts")
    sources = report.get("source_hashes", {})
    require(sources and sources == report.get("final_source_hashes") == report.get("final_frozen_source_hashes"), "complete source conservation")
    require(report.get("fixture_facts") == report.get("final_fixture_facts"), "fixture conservation")
    require(report.get("artifact_hashes") == report.get("final_artifact_hashes") and report.get("binary_hashes") == report.get("final_binary_hashes"), "produced file conservation")
    work = Path(report.get("work", ""))
    require(work.is_absolute(), "absolute retained evidence root")
    suffix = ".exe" if host == "win32" else ""
    expected_images = {str(work / ("typed-os-" + kind + suffix)) for kind in ("contract", "execute")}
    expected_images |= {str(work / (name + f".O{opt}" + (".obj" if host == "win32" else ".o"))) for opt in OPTS for name in RUNTIME_SOURCES}
    expected_images |= {str(work / (f"capability-O{opt}" + suffix)) for opt in OPTS}
    expected_images |= {str(work / (name + f"-O{opt}" + suffix)) for opt in OPTS for name in PROGRAMS}
    expected_artifacts = {str(work / ("typed-os-" + kind + ".c")) for kind in ("contract", "execute")}
    expected_artifacts |= {str(work / ("contract-" + case["name"] + ".fk")) for case in contract_cases()}
    expected_artifacts |= {str(work / (name + extension)) for name in PROGRAMS for extension in (".fk", ".ll")}
    expected_artifacts.add(str(work / "typed-os-capability.c"))
    require(set(report["binary_hashes"]) == expected_images and len(expected_images) == 53 and
            set(report["artifact_hashes"]) == expected_artifacts and len(expected_artifacts) == 46,
            "complete closed generated-source/module/image inventory")
    require(all(re.fullmatch(r"[0-9a-f]{64}", value) for value in (*report["binary_hashes"].values(), *report["artifact_hashes"].values(), *sources.values())), "persisted SHA256 shape")
    contracts = report.get("contracts", [])
    require([row.get("name") for row in contracts] == [row["name"] for row in contract_cases()], "closed contract matrix")
    for expected, actual in zip(contract_cases(), contracts):
        require(actual.get("source_sha256") == hashlib.sha256(expected["source"].encode()).hexdigest(), "contract source identity")
        assert_exact(result_object(actual["actual"]), 0,
                     ("typed-os-entry-contract mode=" + expected["mode"] + "=passed\n").encode(), b"", host)
    emissions = report.get("emissions", [])
    require([row.get("name") for row in emissions] == list(PROGRAMS), "closed emission matrix")
    for row in emissions:
        require(row.get("source_sha256") == hashlib.sha256(PROGRAMS[row["name"]].encode()).hexdigest() and re.fullmatch(r"[0-9a-f]{64}", row.get("module_sha256", "")), "source/module emission identity")
    cases = [case for case in CASES if host in case["platforms"]]
    programs = report.get("programs", [])
    expected = [(opt, case) for opt in OPTS for case in cases]
    require([(row.get("optimization"), row.get("id")) for row in programs] == [(opt, case["id"]) for opt,case in expected], "closed native matrix")
    for row, (_, case) in zip(programs, expected):
        assert_exact(result_object(row["actual"]), case["status"], bytes.fromhex(case["stdout_hex"]), bytes.fromhex(case["stderr_hex"]), host)
        require(row.get("audits") == ["C", "LLVM"], "both native ownership audit build flags")
    controls = report.get("controls", [])
    kinds = ("C", "LLVM", "asan-heap", "ubsan-overflow", "ubsan-shift") if sanitize else ("C", "LLVM")
    require([(row.get("optimization"), row.get("kind")) for row in controls] == [(opt,kind) for opt in OPTS for kind in kinds], "complete actual capability controls")
    for row in controls: validate_capability(result_object(row["actual"]), row["kind"], host)


def run_gate(clang, directory, frozen, report, supports):
    validate_data()
    support, sdk_support, bootstrap_support = supports
    fixtures = directory / "fixtures"
    report["fixture_facts"] = create_fixtures(fixtures, sys.platform)
    class Pins(support.Conservation):
        def __init__(self):
            super().__init__(clang, frozen, report)
            self.artifacts = {}
        def check(self):
            super().check()
            reject_bytecode(frozen)
            validate_data()
            require(fixture_facts(fixtures, sys.platform) == report["fixture_facts"], "fixture conservation drift")
            require(all(sha(path) == digest for path, digest in self.artifacts.items()), "produced source/module conservation")
        def track(self, path):
            self.check()
            require(path not in self.artifacts, "duplicate produced artifact identity")
            self.artifacts[path] = sha(path)
            self.check()
        def final_pins(self):
            self.check()
            report["artifact_hashes"] = {str(path):digest for path,digest in self.artifacts.items()}
            report["final_artifact_hashes"] = {str(path):sha(path) for path in self.artifacts}
            report["final_fixture_facts"] = fixture_facts(fixtures, sys.platform)
            super().final_pins()
    pins = Pins(); pins.check()
    checks = load_checks(frozen); pins.check()
    runner = support.Runner(checks, directory / "jobs", pins)
    sdk = sdk_support.Runner(checks, directory / "sdk-jobs", pins)
    bootstrap = bootstrap_support.Runner(checks, directory / "bootstrap-jobs", pins)
    for job_directory in (runner.directory, sdk.directory, bootstrap.directory): job_directory.mkdir(exist_ok=False)
    version = runner.run([str(clang), "--version"], "compiler-version", compiling=True)
    target = runner.run([str(clang), "-dumpmachine"], "compiler-target", compiling=True)
    require(version.returncode == target.returncode == 0 and "clang" in version.stdout.lower(), "Clang identity")
    target_text = target.stdout.replace("\r\n", "\n") if sys.platform == "win32" else target.stdout
    require(re.fullmatch(r"[^\s]+\n?", target_text), "compiler target identity")
    report["compiler"].update(version=version.stdout, target=target_text.rstrip("\n"))
    target_name = host_target(); report["target"] = target_name
    flat = checks.flattened_crates()
    compilers = {}
    for kind in ("contract", "execute"):
        fixture = frozen / ("src/compiler/v4/tests/typed_os_entry_" + kind + "_smoke.fk")
        pins.check()
        source, ui = checks.transpile_fixture(flat, fixture)
        require(not ui, "compiler fixture cannot require UI")
        pins.check()
        c_path = directory / ("typed-os-" + kind + ".c")
        c_path.write_text(source, encoding="utf-8"); pins.track(c_path)
        binary = directory / ("typed-os-" + kind + (".exe" if sys.platform == "win32" else ""))
        result = bootstrap.run([str(clang), "-O0", "-w", "-DFREAK_ARRAY_LIVE_LIMIT=1024", str(c_path), str(frozen / "freakc/runtime/freak_runtime.c"), "-I" + str(frozen / "freakc/runtime"), "-o", str(binary), *checks.runtime_platform_link_args()], "bootstrap-" + kind, compiling=True)
        require(result.returncode == 0, "typed compiler bootstrap failed")
        pins.admit_binary(binary); compilers[kind] = binary
    for case in contract_cases():
        source = directory / ("contract-" + case["name"] + ".fk")
        source.write_text(case["source"], encoding="utf-8"); pins.track(source)
        result = sdk.run([str(compilers["contract"]), case["mode"], str(source), target_name, case["expected"], case["identity"]], "contract-" + case["name"])
        assert_exact(result, 0, ("typed-os-entry-contract mode=" + case["mode"] + "=passed\n").encode(), b"", sys.platform)
        report["contracts"].append({"name":case["name"], "source_sha256":sha(source), "actual":observed(result)})
        print("typed OS contract " + case["name"] + ": exact protocol passed; final pins pending", flush=True)
    modules = {}
    for name, source_text in PROGRAMS.items():
        source = directory / (name + ".fk")
        source.write_text(source_text, encoding="utf-8"); pins.track(source)
        result = sdk.run([str(compilers["execute"]), str(source), target_name], "emit-" + name)
        module = extract_module(result, sys.platform); validate_module(module, name)
        llvm = directory / (name + ".ll")
        llvm.write_bytes(module.encode()); pins.track(llvm); modules[name] = llvm
        report["emissions"].append({"name":name,"source_sha256":sha(source),"module_sha256":sha(llvm)})
        print("typed OS emission " + name + ": v9 restore/seals verified; native pending", flush=True)
    probe = directory / "typed-os-capability.c"; probe.write_text(CAPABILITY_SOURCE); pins.track(probe)
    for opt in OPTS:
        flags = ["--target=" + target_name, f"-O{opt}", "-I" + str(frozen / "freakc/runtime"), *AUDIT_FLAGS]
        if report["sanitized"]: flags.extend(SANITIZER_FLAGS)
        objects = []
        for name in RUNTIME_SOURCES:
            output = directory / (name + f".O{opt}" + (".obj" if sys.platform == "win32" else ".o"))
            result = runner.run([str(clang), *flags, "-c", str(frozen / "freakc/runtime" / name), "-o", str(output)], f"runtime-O{opt}-" + name, compiling=True)
            require(result.returncode == 0, "native private runtime object build failed")
            pins.admit_binary(output); objects.append(str(output))
        capability = directory / (f"capability-O{opt}" + (".exe" if sys.platform == "win32" else ""))
        result = runner.run([str(clang), *flags, str(probe), *objects, "-o", str(capability), *checks.runtime_platform_final_link_args()], f"capability-link-O{opt}", compiling=True)
        require(result.returncode == 0, "native capability link failed"); pins.admit_binary(capability)
        kinds = ("C", "LLVM", "asan-heap", "ubsan-overflow", "ubsan-shift") if report["sanitized"] else ("C", "LLVM")
        for kind in kinds:
            with sanitizer_environment(support, report["sanitized"], 85 if kind.startswith("ubsan-") else 86):
                result = runner.run([str(capability), kind], f"capability-O{opt}-" + kind)
            validate_capability(result, kind, sys.platform)
            report["controls"].append({"optimization":opt,"kind":kind,"actual":observed(result)})
        binaries = {}
        for name, llvm in modules.items():
            output = directory / (name + f"-O{opt}" + (".exe" if sys.platform == "win32" else ""))
            result = runner.run([str(clang), *flags, str(llvm), *objects, "-o", str(output), *checks.runtime_platform_final_link_args()], f"link-O{opt}-" + name, compiling=True)
            require(result.returncode == 0 and result.stdout == result.stderr == "", "native program link exact status/channel")
            pins.admit_binary(output); binaries[name] = output
        for case in CASES:
            if sys.platform not in case["platforms"]: continue
            argv = [str(fixtures / case["fixture"]["relative_path"]) if value == "@fixture-path" else value for value in case["argv"]]
            result = runner.run([str(binaries[case["program"]]), *argv], f"execute-O{opt}-" + case["id"])
            assert_exact(result, case["status"], bytes.fromhex(case["stdout_hex"]), bytes.fromhex(case["stderr_hex"]), sys.platform)
            report["programs"].append({"optimization":opt,"id":case["id"],"audits":["C","LLVM"],"actual":observed(result)})
        pins.check()
        print(f"typed OS O{opt}: {COUNTS[sys.platform]} exact semantic cases and {len(kinds)} actual death controls; final pins pending", flush=True)
    pins.final_pins()
    report["guarded_job_counts"] = {"bootstrap":bootstrap.serial,"compiler":sdk.serial,"native_and_clang":runner.serial}
    validate_report(dict(report, complete=True), report["sanitized"])
    return pins


def main(argv=None):
    require(os.environ.get(GRANT_NAME) == GRANT_VALUE, "exact root compiler/native lease required before source/tool access")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args(argv)
    if sys.platform not in COUNTS or (not args.plain and sys.platform != "linux"): parser.error("plain gate needs Linux/macOS/Windows; ASan+UBSan is mandatory on Linux")
    if not args.clang: parser.error("Clang C driver is required; capabilities cannot be skipped")
    selected = Path(shutil.which(args.clang) or args.clang).absolute()
    clang = selected.resolve(strict=True)
    if clang.name.lower() in ("cl", "cl.exe", "clang-cl", "clang-cl.exe"): parser.error("Clang C driver required")
    directory = args.work.resolve()
    if directory.is_relative_to(ROOT): parser.error("external virgin evidence directory required")
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()): parser.error("stale evidence cannot satisfy the typed gate")
    report = {"complete":False,"platform":sys.platform,"sanitized":not args.plain,"scope":SCOPE,"data_sha256":DATA_SHA,"work":str(directory),
              "compiler_process_contract":{"seconds":60,"memory_mib":64,"live_handles":1024},
              "contracts":[],"emissions":[],"programs":[],"controls":[]}
    path = directory / "report.json"; path.write_text(json.dumps(report, indent=2) + "\n")
    support = None
    try:
        validate_data()
        report["source_hashes"] = source_hashes()
        report["compiler"] = {"selected":str(selected),"path":str(clang),"sha256":sha(clang)}
        frozen = directory / "frozen-source"
        for name, digest in report["source_hashes"].items():
            copy = frozen / name; copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes((ROOT / name).read_bytes())
            require(sha(copy) == digest, "source changed while freezing")
        names = tuple(report["source_hashes"])
        support = load_support(frozen, names, "native")
        sdk = load_support(frozen, names, "compiler")
        bootstrap = load_support(frozen, names, "bootstrap")
        with sanitizer_environment(support, not args.plain):
            pins = run_gate(clang, directory, frozen, report, (support, sdk, bootstrap))
        pins.final_pins()
        candidate = dict(report, complete=True); validate_report(candidate, not args.plain)
        pending = directory / "report.pending.json"; pending.write_text(json.dumps(candidate, indent=2) + "\n")
        pins.check(); os.replace(pending, path); pins.check(); report["complete"] = True
    except BaseException as primary:
        try:
            if support is not None:
                evidence = support._Evidence()
                evidence.attempt("typed-os-failure-attribution", lambda: report.update(complete=False, failure=support.exception_descriptor(primary)))
                evidence.attempt("typed-os-failure-publication", lambda: path.write_text(json.dumps(report, indent=2) + "\n"))
                evidence.attach(primary)
            else:
                for action in (lambda: report.update(complete=False), lambda: path.write_text(json.dumps(report, indent=2) + "\n")):
                    try: action()
                    except BaseException: pass
        except BaseException:
            pass
        raise
    print("TYPED_OS_ENTRY_GATE_PASS", flush=True)
    return 0


DATA_SHA = "ff90d9dc7e9681076c9c2e6061bfc340c9a71600262a715582a12f521f7f399d"

if __name__ == "__main__": raise SystemExit(main())
