#!/usr/bin/env python3
"""Mandatory singleton-fault proof for cold query/expansion admission.

Compiles current crates with test-only array interposition. The four separate FK
smokes cover handle-pressure boundaries and component behavior. Requires Clang;
uses no historical git objects, downloads, or production runtime edits.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

CYCLES = 3
COMPILE_TIMEOUT = 120
COMPILE_MEMORY_MIB = 1024
RUNTIME_TIMEOUT = 60
RUNTIME_MEMORY_MIB = 64
ARRAY_LIMIT = 1024
FINAL_LINE = "single-fault positions=query17+expand4+joint21 cycles=3 later-success=true bootstrap-row=true cold-facts=true handles-conserved=true recovery=true"
PROBE_SOURCE = r'''
/* Test-only interposition: fail exactly one call; subsequent allocations succeed. */
#include "freak_runtime.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static int fault_at;
static int calls;
static int skip_bootstrap;
static int64_t injected_array_new(void);
static void injected_array_push(int64_t handle, freak_word item);
#define freak_array_new injected_array_new
#define freak_array_push injected_array_push
#define main cold_generated_main
#include "cold_init_generated.c"
#undef main
#undef freak_array_push
#undef freak_array_new

static int64_t injected_array_new(void) {
    if (fault_at && ++calls == fault_at) return -1;
    return freak_array_new();
}
static void injected_array_push(int64_t handle, freak_word item) {
    if (skip_bootstrap) { skip_bootstrap = 0; return; }
    freak_array_push(handle, item);
}
static int64_t *query_fields[] = {
    &v4_query_keys, &v4_query_inputs, &v4_query_outputs, &v4_query_states,
    &v4_query_entry_generations, &v4_query_entry_last_generations, &v4_query_entry_last_events,
    &v4_query_dep_from, &v4_query_dep_to, &v4_query_generation_reasons,
    &v4_query_invalidated_keys, &v4_query_invalidated_generations, &v4_query_invalidated_reasons,
    &v4_query_telemetry_keys, &v4_query_telemetry_hits, &v4_query_telemetry_misses, &v4_query_telemetry_stores,
    &v4_query_entry_len, &v4_query_dep_len, &v4_query_hit_total, &v4_query_miss_total,
    &v4_query_store_total, &v4_query_ready, &v4_query_revision
};
static int64_t *expand_fields[] = {
    &v4_expand_files, &v4_expand_trees, &v4_expand_provenance_kinds,
    &v4_expand_generations, &v4_expand_file_len, &v4_expand_ready,
    &v4_session_semantic_restore_generation_value
};
static void save(int64_t **fields, size_t n, int64_t *before) {
    for (size_t i = 0; i < n; ++i) before[i] = *fields[i];
}
static void unchanged(int64_t **fields, size_t n, const int64_t *before) {
    for (size_t i = 0; i < n; ++i) assert(*fields[i] == before[i]);
}
static void seed_expand(void) {
    v4_expand_files = -201;
    v4_expand_trees = -202;
    v4_expand_provenance_kinds = -203;
    v4_expand_generations = -204;
    v4_expand_file_len = 23;
    v4_expand_ready = 0;
    v4_session_semantic_restore_generation_value = 47;
}
static void recover_query(const int64_t *before, int64_t capacity) {
    assert(freak_v4_query_try_init() && v4_query_ready == 1);
    for (size_t i = 0; i < 17; ++i) {
        assert(*query_fields[i] >= 0);
        assert(freak_array_len(*query_fields[i]) == (i == 9 ? 1 : 0));
        for (size_t j = 0; j < i; ++j) assert(*query_fields[i] != *query_fields[j]);
    }
    assert(freak_word_eq(freak_array_get(v4_query_generation_reasons, 0), freak_word_lit("bootstrap")));
    for (size_t i = 17; i < 24; ++i) if (i != 22) assert(*query_fields[i] == before[i]);
    assert(freak_v4_cold_query_capacity() == capacity - 17);
    freak_v4_query_rollback_cold_init(before[0], before[1], before[2], before[3], before[4], before[5], before[6], before[7], before[8], before[9], before[10], before[11], before[12], before[13], before[14], before[15], before[16]);
    unchanged(query_fields, 24, before);
    assert(freak_v4_cold_query_capacity() == capacity);
}
static void recover_expand(const int64_t *before, int64_t capacity) {
    assert(freak_v4_expand_try_init() && v4_expand_ready == 1 && v4_expand_file_len == 0);
    for (size_t i = 0; i < 4; ++i) {
        assert(*expand_fields[i] >= 0 && freak_array_len(*expand_fields[i]) == 0);
        for (size_t j = 0; j < i; ++j) assert(*expand_fields[i] != *expand_fields[j]);
    }
    assert(v4_session_semantic_restore_generation_value == before[6]);
    assert(freak_v4_cold_query_capacity() == capacity - 4);
    freak_v4_expand_rollback_cold_init(before[0], before[1], before[2], before[3], before[4]);
    unchanged(expand_fields, 7, before);
    assert(freak_v4_cold_query_capacity() == capacity);
}
static void recover_joint(const int64_t *query_before, const int64_t *expand_before, int64_t capacity) {
    /* Successful recovery uses ordinary empty counters. Failure sentinels
       detect exact preservation at the private bootstrap boundary. */
    v4_query_entry_len = v4_query_dep_len = v4_query_hit_total = v4_query_miss_total = v4_query_store_total = 0;
    v4_query_revision = 1;
    freak_word result = freak_v4_expand_snapshot_restore_with_queries(freak_word_lit(
        "expand-snapshot|format=freak-expand-snapshot-v1|files=0\nend|freak-expand-snapshot-v1"));
    assert(freak_word_eq(result, freak_word_lit("expand-snapshot-restore ok=1 files=0 skipped-other=0 live-files=0 query-invalidations=0")));
    assert(v4_query_ready == 1 && v4_expand_ready == 1 && v4_query_revision == 2);
    assert(v4_query_entry_len == 0 && v4_query_dep_len == 0 && v4_query_hit_total == 0 && v4_query_miss_total == 0 && v4_query_store_total == 0);
    assert(v4_expand_file_len == 0 && v4_session_semantic_restore_generation_value == expand_before[6] + 1);
    for (size_t i = 0; i < 17; ++i) assert(*query_fields[i] >= 0);
    for (size_t i = 0; i < 4; ++i) assert(*expand_fields[i] >= 0);
    assert(freak_v4_cold_query_capacity() == capacity - 21);
    /* Explicit fixture cleanup after a successful restore. Production only
       rolls back failures before any generation has advanced. */
    freak_v4_query_rollback_cold_init(query_before[0], query_before[1], query_before[2], query_before[3], query_before[4], query_before[5], query_before[6], query_before[7], query_before[8], query_before[9], query_before[10], query_before[11], query_before[12], query_before[13], query_before[14], query_before[15], query_before[16]);
    for (size_t i = 17; i < 24; ++i) *query_fields[i] = query_before[i];
    freak_v4_expand_rollback_cold_init(expand_before[0], expand_before[1], expand_before[2], expand_before[3], expand_before[4]);
    v4_session_semantic_restore_generation_value = expand_before[6];
    unchanged(query_fields, 24, query_before);
    unchanged(expand_fields, 7, expand_before);
    assert(freak_v4_cold_query_capacity() == capacity);
}
int main(void) {
    int64_t query_before[24], expand_before[7];
    int64_t capacity = freak_v4_cold_query_capacity();
    assert(capacity == 1023);
    for (int cycle = 0; cycle < 3; ++cycle) {
        for (int position = 1; position <= 17; ++position) {
            freak_v4_cold_query_seed_sentinels(); save(query_fields, 24, query_before);
            calls = 0; fault_at = position;
            assert(!freak_v4_query_try_init());
            assert(calls == 17); /* subsequent allocations really succeed */
            fault_at = 0;
            unchanged(query_fields, 24, query_before);
            assert(freak_v4_cold_query_capacity() == capacity);
            recover_query(query_before, capacity);
            printf("fault|query|%d|%d|ok\n", position, cycle);
        }
        freak_v4_cold_query_seed_sentinels(); save(query_fields, 24, query_before);
        skip_bootstrap = 1;
        assert(!freak_v4_query_try_init() && !skip_bootstrap);
        unchanged(query_fields, 24, query_before);
        assert(freak_v4_cold_query_capacity() == capacity);
        recover_query(query_before, capacity);
        printf("fault|bootstrap-row|1|%d|ok\n", cycle);
        for (int position = 1; position <= 4; ++position) {
            seed_expand(); save(expand_fields, 7, expand_before);
            calls = 0; fault_at = position;
            assert(!freak_v4_expand_try_init()); assert(calls == 4); fault_at = 0;
            unchanged(expand_fields, 7, expand_before);
            assert(freak_v4_cold_query_capacity() == capacity);
            recover_expand(expand_before, capacity);
            printf("fault|expand|%d|%d|ok\n", position, cycle);
        }
        for (int position = 1; position <= 21; ++position) {
            freak_v4_cold_query_seed_sentinels(); seed_expand();
            save(query_fields, 24, query_before); save(expand_fields, 7, expand_before);
            v4_expand_snapshot_format = freak_word_lit("freak-expand-snapshot-v1");
            calls = 0; fault_at = position;
            freak_word result = freak_v4_expand_snapshot_restore_with_queries(freak_word_lit(
                "expand-snapshot|format=freak-expand-snapshot-v1|files=0\nend|freak-expand-snapshot-v1"));
            assert(freak_word_eq(result, freak_word_lit(position <= 17 ?
                "expand-snapshot-restore ok=0 reason=query-initialization-resource-exhausted" :
                "expand-snapshot-restore ok=0 reason=expand-initialization-resource-exhausted")));
            assert(calls == (position <= 17 ? 17 : 21)); fault_at = 0;
            unchanged(query_fields, 24, query_before); unchanged(expand_fields, 7, expand_before);
            assert(freak_v4_cold_query_capacity() == capacity);
            recover_joint(query_before, expand_before, capacity);
            printf("fault|joint|%d|%d|ok\n", position, cycle);
        }
    }
    puts("single-fault positions=query17+expand4+joint21 cycles=3 later-success=true bootstrap-row=true cold-facts=true handles-conserved=true recovery=true");
    return 0;
}
'''


def fault_cases() -> list[dict[str, int | str]]:
    return [
        {"kind": kind, "position": position, "cycle": cycle}
        for cycle in range(CYCLES)
        for kind, count in (("query", 17), ("bootstrap-row", 1), ("expand", 4), ("joint", 21))
        for position in range(1, count + 1)
    ]


def expected_output_lines() -> list[str]:
    return [f"fault|{case['kind']}|{case['position']}|{case['cycle']}|ok" for case in fault_cases()] + [FINAL_LINE]


def validate_result(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.returncode != 0:
        raise RuntimeError(f"cold admission fault probe exited {completed.returncode}\n{completed.stderr[-4000:]}")
    if completed.stderr:
        raise RuntimeError(f"unexpected fault probe stderr: {completed.stderr[-4000:]}")
    if completed.stdout.splitlines() != expected_output_lines():
        raise RuntimeError("cold admission fault output omitted, reordered, or changed a mandatory case")


def sha256(data: str | bytes) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", help="Clang executable; otherwise resolved from PATH")
    parser.add_argument("--output-dir", type=Path, help="Retain generated source, native proof, and source/fault manifest here")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    clang = args.clang or shutil.which("clang")
    if not clang:
        parser.error("Clang is required; the proof cannot be skipped")
    out = args.output_dir or Path(tempfile.mkdtemp(prefix="v4-cold-init-admission-"))
    out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root), str(root / "src/compiler/v4")]
    spec = importlib.util.spec_from_file_location("v4_cold_init_check", root / "src/compiler/v4/check_v4.py")
    assert spec is not None and spec.loader is not None
    harness = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = harness
    spec.loader.exec_module(harness)
    fixture = root / "src/compiler/v4/tests/cold_query_admission_smoke.fk"
    base = harness.flattened_crates()
    source_hashes = {str(path.relative_to(root)): sha256(path.read_bytes()) for path in harness.crate_paths()}
    source_hashes[str(fixture.relative_to(root))] = sha256(fixture.read_bytes())
    source_hashes["tests/v4_cold_init_admission.py"] = sha256(Path(__file__).read_bytes())
    runtime = harness.RUNTIME_ROOT / "freak_runtime.c"
    source_hashes[str(runtime.relative_to(root))] = sha256(runtime.read_bytes())
    source_hashes["freakc/runtime/freak_runtime.h"] = sha256((harness.RUNTIME_ROOT / "freak_runtime.h").read_bytes())
    generated, uses_ui = harness.transpile_fixture(base, fixture)
    if uses_ui:
        raise RuntimeError("cold admission fixture unexpectedly requires UI")
    generated_path = out / "cold_init_generated.c"
    generated_path.write_text(generated, encoding="utf-8")
    probe_path = out / "cold_init_probe.c"
    probe_path.write_text(PROBE_SOURCE, encoding="utf-8")
    exe = out / ("cold_init_probe.exe" if sys.platform.startswith("win") else "cold_init_probe")
    command = [clang, "-O0", "-w", f"-DFREAK_ARRAY_LIVE_LIMIT={ARRAY_LIMIT}", str(probe_path), str(runtime),
               "-I" + str(harness.RUNTIME_ROOT), "-o", str(exe), *harness.runtime_platform_link_args()]
    manifest = {
        "source_sha256": source_hashes,
        "flattened_sha256": sha256(base), "generated_sha256": sha256(generated), "probe_sha256": sha256(PROBE_SOURCE),
        "compile_command": command, "compile_timeout_seconds": COMPILE_TIMEOUT, "compile_memory_mib": COMPILE_MEMORY_MIB,
        "runtime_timeout_seconds": RUNTIME_TIMEOUT, "runtime_memory_mib": RUNTIME_MEMORY_MIB, "array_limit": ARRAY_LIMIT,
        "fault_cases": fault_cases(), "status": "pending",
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print("cold init admission compile: " + json.dumps(command), flush=True)
    compiled = harness.run_with_heartbeat(command, label="cold init admission compile",
                                         timeout_seconds=COMPILE_TIMEOUT, memory_limit_mb=COMPILE_MEMORY_MIB)
    (out / "compile.stdout").write_text(compiled.stdout)
    (out / "compile.stderr").write_text(compiled.stderr)
    if compiled.returncode:
        raise RuntimeError("cold admission fault compile failed\n" + compiled.stderr[-4000:])
    executed = harness.run_with_heartbeat([str(exe)], label="cold init admission fault proof",
                                          timeout_seconds=RUNTIME_TIMEOUT, memory_limit_mb=RUNTIME_MEMORY_MIB)
    (out / "runtime.stdout").write_text(executed.stdout)
    (out / "runtime.stderr").write_text(executed.stderr)
    validate_result(executed)
    manifest.update(status="pass", runtime_exit=executed.returncode,
                    stdout_sha256=sha256(executed.stdout), stderr_sha256=sha256(executed.stderr))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(FINAL_LINE, flush=True)
    print(f"cold init admission PASS cases={len(fault_cases())} evidence={manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
