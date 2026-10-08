#!/usr/bin/env python3
"""Collect real checked-filesystem observations without changing its contract.

This is diagnostic-only: exit zero means the probe and report completed. Read
production_contract_passed for the actual filesystem outcome. BOOT12 remains
the authoritative public bootstrap gate. SDK checks are not native execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from freakc.v4_native_runtime import RUNTIME_FILE_NAMES, runtime_file


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def handle_accounting(rows: list[dict], original_summary: dict) -> dict:
    """Retain table identities and trace ownership without guessing providers.

    Equal table identities can conceal close/reopen reuse between captures.
    Count brackets and a repeated final query are evidence, never corrections
    to the original resource oracle or a claim of kernel-object continuity.
    """
    summaries = [row for row in rows if row["type"] == "handle_diagnostic_summary"]
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary["process_information_class"] == 51 and summary["object_information_class"] == 2
    assert summary["object_names_queried"] is False
    assert summary["handles_opened_or_duplicated_by_snapshot"] is False
    assert summary["production_result_adjusted"] is False
    events = [row for row in rows if row["type"] == "native"]
    assert [row["trace_ordinal"] for row in events] == list(range(len(events)))
    for event in events:
        assert event["owner_scope"] in {"production", "observer_profile", "observer_alternative", "observer_sync"}
        assert type(event["handle_counts_valid"]) is bool
        for field in ("handles_before", "handles_after"):
            assert (type(event[field]) is int and event[field] >= -1) if event["handle_counts_valid"] else event[field] is None
    snapshots = [row for row in rows if row["type"] == "handle_snapshot"]
    assert len(snapshots) == summary["snapshot_count"] <= summary["snapshot_limit"]
    assert [row["ordinal"] for row in snapshots] == list(range(len(snapshots)))
    assert snapshots[0]["phase"] == "cold_entry" and snapshots[-1]["phase"] == "query_repeat_after_release"
    assert {row["phase"] for row in rows if row["type"] == "resource_checkpoint"} <= {row["phase"] for row in snapshots}
    assert len({row["process_id"] for row in snapshots}) == 1
    identities = {row["ordinal"]: [] for row in snapshots}
    for row in rows:
        if row["type"] == "handle_identity":
            assert row["ordinal"] in identities
            assert type(row["type_known"]) is bool
            assert row["type_known"] == (row["object_type"] is not None)
            if row["type_known"]:
                assert row["type_ntstatus"] == 0
            identities[row["ordinal"]].append(row)
    assert summary["snapshot_completed"] == (not summary["snapshot_overflow"] and
                                               all(row["complete"] for row in snapshots))
    assert summary["all_types_known"] == all(row["type_known"] for group in identities.values() for row in group)
    for snapshot in snapshots:
        group = identities[snapshot["ordinal"]]
        assert len(group) <= summary["handle_limit"]
        assert len({row["handle"] for row in group}) == len(group)
        assert type(snapshot["complete"]) is bool
        assert type(snapshot["trace_events_seen"]) is int and 0 <= snapshot["trace_events_seen"] <= len(events)
        assert all(type(snapshot[field]) is int and snapshot[field] >= -1 for field in
                   ("count_before_query", "count_after_query", "count_after_types"))
        if snapshot["complete"]:
            assert snapshot["ntstatus"] == 0 and snapshot["snapshot_handles"] == len(group)
        else:
            assert snapshot["snapshot_handles"] is None and not group
    assert [row["trace_events_seen"] for row in snapshots] == sorted(row["trace_events_seen"] for row in snapshots)
    assert snapshots[-1]["trace_events_seen"] <= len(events)

    def acquired(event: dict) -> int | None:
        if event["api"] == "CreateFileW" and event["result"] == 1:
            return event["handle"]
        if event["api"] == "NtCreateFile" and event["result"] == 0 and event["io_valid"] and event["io_status"] == 0:
            return event["other_handle"]
        if event["api"] in {"ReOpenFile", "OpenFileById", "DuplicateHandle", "OpenProcessToken", "OpenThreadToken"} and event["result"] == 1:
            return event["other_handle"]
        return None

    active: dict[int, dict] = {}
    acquisitions, unknown_closes, overwritten = [], [], []
    position = 0
    cold = {row["handle"] for row in identities[0]}
    views = []
    for snapshot in snapshots:
        while position < snapshot["trace_events_seen"]:
            event = events[position]
            handle = acquired(event)
            if handle is not None:
                record = {"handle": handle, "open_trace_ordinal": position, "api": event["api"],
                          "phase": event["phase"], "owner_scope": event["owner_scope"],
                          "close_trace_ordinal": None}
                if handle in active:
                    overwritten.append({"previous": active[handle], "replacement": record})
                active[handle] = record
                acquisitions.append(record)
            if event["api"] == "CloseHandle" and event["result"] == 1:
                record = active.pop(event["handle"], None)
                if record is not None:
                    record["close_trace_ordinal"] = position
                else:
                    unknown_closes.append({"handle": event["handle"], "trace_ordinal": position,
                                           "phase": event["phase"], "owner_scope": event["owner_scope"]})
            position += 1
        annotated = []
        for identity in identities[snapshot["ordinal"]]:
            record = active.get(identity["handle"])
            annotated.append(dict(identity, owner_label="traced_acquisition" if record else
                                  "present_at_cold_entry_or_reused_value" if identity["handle"] in cold else
                                  "untraced_acquisition", traced_owner=dict(record) if record else None))
        views.append(dict(snapshot, identities=annotated))
    # All operations precede the final pair; otherwise ownership would be an
    # incomplete prefix even though the raw native trace was retained.
    assert position == len(events)

    def key(row: dict) -> tuple:
        return tuple(row[name] for name in ("handle", "type_index", "access", "attributes"))

    def interval(before: dict, after: dict) -> dict:
        result = {"before_ordinal": before["ordinal"], "after_ordinal": after["ordinal"],
                  "before_phase": before["phase"], "after_phase": after["phase"],
                  "comparable": before["complete"] and after["complete"],
                  "retained_kernel_object_continuity_proven": False}
        if result["comparable"]:
            old = {key(row): row for row in before["identities"]}
            new = {key(row): row for row in after["identities"]}
            result.update(added=[new[item] for item in sorted(new.keys() - old.keys())],
                          removed=[old[item] for item in sorted(old.keys() - new.keys())],
                          retained=[new[item] for item in sorted(new.keys() & old.keys())],
                          handle_delta=len(new) - len(old))
        return result

    final = [view for view in views if view["phase"] == "after_release_tickets"]
    assert len(final) == 1
    count_brackets_stable = all(view["complete"] and view["count_before_query"] >= 0 and
                                view["count_before_query"] == view["count_after_query"] ==
                                view["count_after_types"] == view["snapshot_handles"] for view in views)
    boundary_counts_match = (views[0]["count_before_query"] == original_summary["resources_before"] and
                             final[0]["count_before_query"] == original_summary["resources_after"])
    return {"native_summary": summary, "snapshots": views,
            "phase_intervals": [interval(before, after) for before, after in zip(views, views[1:])],
            "cold_to_released": interval(views[0], final[0]),
            "query_repeat_control": interval(final[0], views[-1]),
            "query_count_brackets_stable": count_brackets_stable,
            "original_interval_boundary_counts_match": boundary_counts_match,
            "owning_acquisitions": acquisitions, "owning_trace_overwrites": overwritten,
            "successful_closes_without_traced_acquisition": unknown_closes,
            "unclosed_traced_acquisitions": list(active.values()),
            "api_count_brackets": [row for row in events if row["handle_counts_valid"]],
            "production_contract_passed": original_summary["production_contract_passed"],
            "production_result_adjusted": False,
            "attribution_limit": "Type and table identities identify observed additions. Untraced ownership remains unknown; equal handle/type/access values can conceal reuse. Diagnostic query counts are retained, never subtracted from the original cold oracle."}


def observations(result: subprocess.CompletedProcess, control: bool) -> dict:
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert not result.stderr, result.stderr
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    assert rows and rows[-1]["type"] == "summary"
    summary = rows[-1]
    assert summary["diagnostic_completed"] and not summary["trace_overflow"]
    assert type(summary["production_contract_passed"]) is bool
    tickets = {row["phase"]: row for row in rows if row["type"] == "ticket"}
    expected = {"open_parent", "temp_dir", "open_missing_runtime", "mkdir_runtime", "cleanup_temp"}
    assert {"open_parent", "temp_dir"} <= tickets.keys(), tickets
    if tickets["temp_dir"]["ok"]:
        assert expected <= tickets.keys(), tickets
    for ticket in tickets.values():
        assert all(type(ticket[key]) is bool for key in ("ok", "completed", "missing"))
    truthful = (expected <= tickets.keys() and tickets["open_parent"]["ok"] and tickets["temp_dir"]["ok"] and
                not tickets["open_missing_runtime"]["ok"] and
                tickets["open_missing_runtime"]["missing"] and
                tickets["mkdir_runtime"]["ok"] and tickets["mkdir_runtime"]["completed"] and
                tickets["cleanup_temp"]["ok"] and tickets["cleanup_temp"]["completed"] and
                summary["resources_balanced"])
    assert summary["production_contract_passed"] == truthful
    assert summary["tickets_before"] == summary["tickets_after"] == 0
    if control and tickets["temp_dir"]["ok"]:
        assert "control_existing_runtime" in tickets
        if tickets["control_existing_runtime"]["completed"]:
            assert not summary["production_contract_passed"]
            assert not tickets["mkdir_runtime"]["ok"] and not tickets["mkdir_runtime"]["completed"]
    if sys.platform == "win32":
        events = [row for row in rows if row["type"] == "native"]
        if tickets["open_parent"]["ok"]:
            assert any(row["api"] == "CreateFileW" and row["phase"] == "open_parent" for row in events)
            assert any(row["type"] == "filesystem" for row in rows)
            assert any(row["type"] == "token" for row in rows)
            devices = [row for row in rows if row["type"] == "device_profile"]
            assert len(devices) == 1
            device = devices[0]
            assert device["information_class"] == 4
            if device["completion_valid"]:
                assert device["ntstatus"] == device["io_status"] == 0
                assert device["io_information"] >= 8 and not device["status_pending"]
                assert device["remote"] == bool(device["characteristics"] & 0x10)
                assert device["local_disk"] == (device["device_type"] == 7 and not device["remote"])
            else:
                assert device["remote"] is device["local_disk"] is None
        if tickets["temp_dir"]["ok"]:
            assert any(row["api"] == "NtCreateFile" and row["phase"] == "temp_dir" for row in events)
        if tickets.get("mkdir_runtime", {}).get("completed"):
            assert any(row["api"] == "NtCreateFile" and row["phase"] == "mkdir_runtime" for row in events)
        alternatives = [row for row in rows if row["type"] == "alternative"]
        expected_alternatives = {"held_writable_temp", "duplicate_same_access_temp"}
        if tickets["open_parent"]["ok"]:
            expected_alternatives |= {"reopen_parent_append", "reopen_parent_write",
                                      "nt_empty_parent_append", "nt_empty_parent_write",
                                      "open_by_id_parent_append", "open_by_id_parent_write"}
        if tickets["temp_dir"]["ok"]:
            assert {row["method"] for row in alternatives} == expected_alternatives
        else:
            assert not alternatives
        for row in alternatives:
            assert row["flush_flags"] == row["parameters_size"] == 0
            assert row["durability_proven"] is False
            if row["flush_called"]:
                assert row["opened"] and row["identity_matches"] and row["flush_api_available"]
                assert type(row["ntstatus"]) is int
            else:
                assert row["ntstatus"] is None and not row["completion_valid"]
            if row["completion_valid"]:
                assert row["ntstatus"] == row["io_status"] == 0 and not row["status_pending"]
            else:
                assert row["io_status"] is None
            if row["status_pending"]:
                assert row["ntstatus"] == 0x103 and not row["completion_valid"]
    control_exercised = bool(control and tickets.get("control_existing_runtime", {}).get("completed"))
    return {"summary": summary, "observations": rows,
            "unreached_phases": sorted(expected - tickets.keys()),
            "control_exercised": control_exercised,
            "control_status": "exercised" if control_exercised else "inconclusive" if control else "not_requested"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG", "clang"))
    parser.add_argument("--work", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--windows-sdk", type=Path)
    parser.add_argument("--windows-handle-diagnostics", action="store_true",
                        help="Run additional native Windows handle snapshots after all original cold runs")
    args = parser.parse_args()
    clang = Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    work = (args.work or Path(tempfile.mkdtemp(prefix="freak-v4-fs-probe-"))).resolve()
    if work.is_relative_to(ROOT):
        parser.error("--work must be outside the repository")
    work.mkdir(parents=True, exist_ok=True)
    if any(work.iterdir()):
        parser.error("--work must be empty")
    if args.sanitize and sys.platform != "linux":
        parser.error("this narrow sanitizer proof requires Linux")
    if args.windows_handle_diagnostics and sys.platform != "win32":
        parser.error("--windows-handle-diagnostics requires actual native Windows execution")
    frozen = work / "frozen-source"
    runtime = ROOT / "freakc/runtime"
    mappings = [(runtime_file(runtime,name), frozen / "freakc/runtime" / name)
                for name in RUNTIME_FILE_NAMES]
    for name in ("tests/native_bootstrap_fs_probe.c", "tests/v4_bootstrap_fs_probe.py",
                 "tests/native_bootstrap_fs_handle_probe.inc",
                 "src/compiler/v4/native-runtime.manifest", "freakc/v4_native_runtime.py"):
        mappings.append((ROOT / name,frozen / name))
    inputs = {str(source.relative_to(ROOT)).replace("\\", "/"): sha(source) for source,_ in mappings}
    report = {"diagnostic_completed": False, "production_contract_passed": False,
              "scope": "observational checked FS; BOOT12 remains authoritative",
              "native_platform": sys.platform, "sanitize": args.sanitize,
              "windows_sdk_is_native_execution": False,
              "alternative_scope": "Observational normal native flush only; NTFS directory semantics do not establish portable or crash-tested durability. Original product result is unchanged.",
              "inputs": inputs, "clang": {"path": str(clang), "sha256": sha(clang)},
              "commands": [], "runs": []}
    report["handle_diagnostics"] = {"requested": args.windows_handle_diagnostics, "runs": [],
                                    "snapshot_completed": False,
                                    "scope": "Additional diagnostic processes; original three cold runs and production result are retained unchanged."}
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:halt_on_error=1",
               UBSAN_OPTIONS="halt_on_error=1")
    env.pop("FREAK_FS_PROBE_CONTROL", None)
    env.pop("FREAK_FS_PROBE_HANDLE_DIAGNOSTICS", None)

    def run(command: list[str], label: str, control: bool = False,
            handle_diagnostics: bool = False) -> subprocess.CompletedProcess:
        result = subprocess.run(command, capture_output=True, timeout=90,
                                env=dict(env, **({"FREAK_FS_PROBE_CONTROL": "existing"} if control else {}),
                                         **({"FREAK_FS_PROBE_HANDLE_DIAGNOSTICS": "1"} if handle_diagnostics else {})))
        report["commands"].append({"label": label, "command": command, "exit": result.returncode,
                                   "stdout": result.stdout.decode(errors="replace"),
                                   "stderr": result.stderr.decode(errors="replace")})
        if handle_diagnostics:
            report["commands"][-1].update(stdout_hex=result.stdout.hex(), stderr_hex=result.stderr.hex(),
                                          handle_diagnostics=True)
        return result

    try:
        for source,target in mappings:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            assert sha(target) == inputs[str(source.relative_to(ROOT)).replace("\\", "/")]
        fixture = frozen / "tests/native_bootstrap_fs_probe.c"
        strict = ["-std=c11", "-Werror=implicit-function-declaration", "-Werror=incompatible-pointer-types",
                  "-Werror=int-conversion", "-Werror=return-type", f"-I{frozen / 'freakc/runtime'}"]
        sanitizer = ["-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                     "-fno-omit-frame-pointer", "-g"] if args.sanitize else []
        executable = work / ("fs-probe.exe" if os.name == "nt" else "fs-probe")
        result = run([str(clang), *strict, "-O2", *sanitizer, "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1",
                      str(fixture), "-o", str(executable),
                      *(["-lws2_32", "-lshell32"] if os.name == "nt" else ["-lm"])], "native-build")
        assert result.returncode == 0, result.stderr
        parent = work / "owned parent % ! é 日本"
        parent.mkdir(mode=0o700)
        for control in (False, True):
            result = run([str(executable), str(parent)], "native-existing-control" if control else "native-probe", control)
            data = observations(result, control)
            data["control"] = control; report["runs"].append(data)
            if not control:
                report["production_contract_passed"] = data["summary"]["production_contract_passed"]
        # An actual missing parent stops before mkdir. Preserve both failed
        # tickets/native events and explicitly mark later phases unavailable.
        result = run([str(executable), str(parent / "absent parent")], "native-missing-parent")
        data = observations(result, False)
        assert not data["summary"]["production_contract_passed"]
        assert data["unreached_phases"] == ["cleanup_temp", "mkdir_runtime", "open_missing_runtime"]
        data["control"] = "missing_parent"; report["runs"].append(data)
        if args.windows_handle_diagnostics:
            for control in (False, True, "missing_parent"):
                target = parent / "absent parent" if control == "missing_parent" else parent
                label = "native-handle-" + ("missing-parent" if control == "missing_parent" else
                                            "existing-control" if control else "probe")
                result = run([str(executable), str(target)], label, control is True, True)
                data = observations(result, control is True)
                data["control"] = control
                data["handle_accounting"] = handle_accounting(data["observations"], data["summary"])
                report["handle_diagnostics"]["runs"].append(data)
            report["handle_diagnostics"]["snapshot_completed"] = all(
                data["handle_accounting"]["native_summary"]["snapshot_completed"]
                for data in report["handle_diagnostics"]["runs"])
        if args.windows_sdk:
            cross = [str(clang), "--target=x86_64-w64-windows-gnu",
                     f"--sysroot={args.windows_sdk.resolve()}", *strict]
            result = run([*cross, "-fsyntax-only", str(fixture)], "windows-sdk-syntax")
            assert result.returncode == 0, result.stderr
            result = run([*cross, "-O2", "-c", str(fixture), "-o", str(work / "fs-probe.obj")], "windows-sdk-coff")
            assert result.returncode == 0, result.stderr
            report["windows_coff_sha256"] = sha(work / "fs-probe.obj")
        assert inputs == {str(source.relative_to(ROOT)).replace("\\", "/"): sha(source) for source,_ in mappings}
        assert sha(clang) == report["clang"]["sha256"]
        report["diagnostic_completed"] = True
        print(f"checked FS diagnostic completed on {sys.platform}; production_contract_passed="
              f"{str(report['production_contract_passed']).lower()} (BOOT12 is authoritative)", flush=True)
        return 0
    except Exception as error:
        report["error"] = repr(error)
        raise
    finally:
        report_path = args.report or work / "report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    raise SystemExit(main())
