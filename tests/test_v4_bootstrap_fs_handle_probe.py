"""Focused tests for evidence interpretation; these are not Windows execution."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v4_bootstrap_fs_probe import handle_accounting


def identity(ordinal, handle, kind="Event"):
    return {"type": "handle_identity", "ordinal": ordinal, "handle": handle,
            "type_index": 10 if kind == "Event" else 5, "access": 1, "attributes": 0,
            "handle_count": 1, "pointer_count": 2, "type_ntstatus": 0,
            "type_known": True, "object_type": kind}


def snapshot(ordinal, phase, handles, seen=0):
    return [{"type": "handle_snapshot", "ordinal": ordinal, "phase": phase,
             "process_id": 100, "ntstatus": 0, "complete": True,
             "snapshot_handles": len(handles), "count_before_query": len(handles),
             "count_after_query": len(handles), "count_after_types": len(handles),
             "trace_events_seen": seen}, *[identity(ordinal, handle) for handle in handles]]


def evidence(groups, events=()):
    rows = list(events) + [row for group in groups for row in group]
    rows.append({"type": "handle_diagnostic_summary", "process_information_class": 51,
                 "object_information_class": 2, "object_names_queried": False,
                 "handles_opened_or_duplicated_by_snapshot": False,
                 "production_result_adjusted": False, "snapshot_completed": True,
                 "snapshot_overflow": False, "snapshot_count": len(groups),
                 "snapshot_limit": 24, "handle_limit": 512, "all_types_known": True})
    return rows


def event(ordinal, api, handle=0, other=0, before=1, after=1):
    return {"type": "native", "trace_ordinal": ordinal, "api": api,
            "result": 1, "handle": handle, "other_handle": other,
            "owner_scope": "observer_profile", "phase": "open_parent",
            "handle_counts_valid": True, "handles_before": before, "handles_after": after}


class HandleAccountingTests(unittest.TestCase):
    def test_fourteen_untraced_events_stay_unknown_and_original_false(self):
        handles = list(range(4, 64, 4))
        rows = evidence([snapshot(0, "cold_entry", handles[:1]),
                         snapshot(1, "LookupPrivilegeValueW", handles, 1),
                         snapshot(2, "after_release_tickets", handles, 1),
                         snapshot(3, "query_repeat_after_release", handles, 1)],
                        [event(0, "LookupPrivilegeValueW", before=1, after=15)])
        summary = {"resources_before": 1, "resources_after": 15,
                   "resources_balanced": False, "production_contract_passed": False}
        result = handle_accounting(rows, summary)
        self.assertEqual(result["cold_to_released"]["handle_delta"], 14)
        self.assertEqual(len(result["cold_to_released"]["added"]), 14)
        self.assertEqual({row["owner_label"] for row in result["cold_to_released"]["added"]},
                         {"untraced_acquisition"})
        self.assertFalse(result["production_contract_passed"])
        self.assertEqual(result["api_count_brackets"][0]["api"], "LookupPrivilegeValueW")
        self.assertEqual(result["query_repeat_control"]["added"], [])
        self.assertEqual(summary["resources_after"], 15)

    def test_query_induced_addition_is_visible_without_subtraction(self):
        rows = evidence([snapshot(0, "cold_entry", [4, 8]),
                         snapshot(1, "after_release_tickets", [4, 8]),
                         snapshot(2, "query_repeat_after_release", [4, 8])])
        rows[0]["count_before_query"] = 1
        result = handle_accounting(rows, {"resources_before": 1, "resources_after": 2,
                                         "production_contract_passed": False})
        self.assertFalse(result["query_count_brackets_stable"])
        self.assertTrue(result["original_interval_boundary_counts_match"])
        self.assertEqual(result["cold_to_released"]["handle_delta"], 0)
        self.assertFalse(result["production_result_adjusted"])
        self.assertEqual(result["snapshots"][0]["count_before_query"], 1)

    def test_reused_handle_value_preserves_known_acquisition_generation(self):
        events = [event(0, "CloseHandle", handle=4),
                  event(1, "CreateFileW", handle=4),
                  event(2, "CloseHandle", handle=4),
                  event(3, "OpenProcessToken", other=4)]
        rows = evidence([snapshot(0, "cold_entry", [4]),
                         snapshot(1, "after_release_tickets", [4], 4),
                         snapshot(2, "query_repeat_after_release", [4], 4)], events)
        result = handle_accounting(rows, {"resources_before": 1, "resources_after": 1,
                                         "production_contract_passed": False})
        final = result["snapshots"][1]["identities"][0]
        self.assertEqual(final["owner_label"], "traced_acquisition")
        self.assertEqual(final["traced_owner"]["api"], "OpenProcessToken")
        self.assertEqual(result["owning_acquisitions"][0]["close_trace_ordinal"], 2)
        self.assertEqual(len(result["successful_closes_without_traced_acquisition"]), 1)
        self.assertEqual(len(result["unclosed_traced_acquisitions"]), 1)
        self.assertFalse(result["cold_to_released"]["retained_kernel_object_continuity_proven"])

    def test_inconsistent_count_or_truncated_trace_is_rejected(self):
        rows = evidence([snapshot(0, "cold_entry", [4]),
                         snapshot(1, "after_release_tickets", [4]),
                         snapshot(2, "query_repeat_after_release", [4])])
        summary = {"resources_before": 1, "resources_after": 1, "production_contract_passed": True}
        bad = deepcopy(rows)
        bad[0]["snapshot_handles"] = 2
        with self.assertRaises(AssertionError):
            handle_accounting(bad, summary)
        bad = deepcopy(rows)
        bad.insert(0, event(0, "OpenProcessToken", other=8))
        with self.assertRaises(AssertionError):
            handle_accounting(bad, summary)

    def test_native_bool_success_accepts_every_nonzero_value(self):
        events = [event(0, "DuplicateHandle", handle=4, other=8, before=1, after=2),
                  event(1, "CloseHandle", handle=8, before=2, after=1)]
        for row in events:
            row["result"] = 2
        rows = evidence([snapshot(0, "cold_entry", [4]),
                         snapshot(1, "after_release_tickets", [4], 2),
                         snapshot(2, "query_repeat_after_release", [4], 2)], events)
        result = handle_accounting(rows, {"resources_before": 1, "resources_after": 1,
                                         "production_contract_passed": True})
        self.assertEqual(len(result["owning_acquisitions"]), 1)
        self.assertEqual(result["owning_acquisitions"][0]["close_trace_ordinal"], 1)
        self.assertEqual(result["unclosed_traced_acquisitions"], [])


if __name__ == "__main__":
    unittest.main()
