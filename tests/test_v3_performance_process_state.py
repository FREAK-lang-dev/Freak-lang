"""Pure process-state oracle tests; no subprocess or native code is launched."""
import errno
import subprocess
import unittest
from unittest.mock import mock_open, patch

import v3_performance_lab as performance


def stat_record(state=b"Z", name=b"child", pid=123):
    # Fields through starttime plus the remaining current Linux stat fields.
    return str(pid).encode() + b" (" + name + b") " + state + b" 0" * 49 + b"\n"


class ProcessStateOracle(unittest.TestCase):
    def setUp(self):
        for attribute in ("run", "Popen"):
            guard = patch.object(subprocess, attribute,
                                 side_effect=AssertionError("unexpected child process"))
            guard.start()
            self.addCleanup(guard.stop)
        guard = patch.object(performance.os, "kill",
                             side_effect=AssertionError("unexpected real PID probe"))
        guard.start()
        self.addCleanup(guard.stop)

    def probe(self, record, expected, platform="linux"):
        reader = mock_open(read_data=record)
        with patch.object(performance.sys, "platform", platform), \
                patch.object(performance.os, "kill") as kill, \
                patch("builtins.open", reader):
            self.assertEqual(performance._process_is_running(123), expected)
        kill.assert_called_once_with(123, 0)
        if platform.startswith("linux"):
            reader.assert_called_once_with("/proc/123/stat", "rb")
            reader().read.assert_called_once_with(4097)
            reader().__exit__.assert_called_once()
        else:
            reader.assert_not_called()

    def test_zombie_and_unusual_comm_are_stopped(self):
        for name in (b"child", b"has spaces", b"nested (name))", b"a) Z 1\n(b", b"\xff"):
            with self.subTest(name=name):
                self.probe(stat_record(name=name), False)

    def test_live_stopped_and_unknown_states_remain_running(self):
        for state in (b"R", b"S", b"D", b"T", b"t", b"I", b"X", b"?", b"ZZ"):
            with self.subTest(state=state):
                self.probe(stat_record(state), True)
        self.probe(stat_record(b"S", name=b"pretend) Z 0 0"), True)

    def test_malformed_truncated_or_oversized_metadata_is_conservative(self):
        records = (b"", b"123 (child) Z 0\n", stat_record(pid=124),
                   stat_record().replace(b"123 (", b"123 "), stat_record()[:-1],
                   stat_record().replace(b" 0", b" --1", 1),
                   stat_record().replace(b" 0", b" bad", 1),
                   stat_record(name=b"x" * 4096))
        for record in records:
            with self.subTest(record=record[:60]):
                self.probe(record, True)

    def test_missing_and_permission_probe_outcomes_do_not_read_metadata(self):
        for platform in ("linux", "darwin", "freebsd14"):
            for error, expected in ((ProcessLookupError(), False), (PermissionError(), True)):
                with self.subTest(platform=platform, error=type(error).__name__), \
                        patch.object(performance.sys, "platform", platform), \
                        patch.object(performance.os, "kill", side_effect=error) as kill, \
                        patch("builtins.open") as reader:
                    self.assertEqual(performance._process_is_running(123), expected)
                    kill.assert_called_once_with(123, 0)
                    reader.assert_not_called()

    def test_unexpected_kill_error_still_propagates(self):
        with patch.object(performance.sys, "platform", "linux"), \
                patch.object(performance.os, "kill", side_effect=OSError(errno.EIO, "probe")), \
                self.assertRaises(OSError):
            performance._process_is_running(123)

    def test_unavailable_procfs_and_exit_race_remain_conservative(self):
        for error in (FileNotFoundError(), ProcessLookupError(), PermissionError(), OSError()):
            with self.subTest(error=type(error).__name__), \
                    patch.object(performance.sys, "platform", "linux"), \
                    patch.object(performance.os, "kill", side_effect=[None, ProcessLookupError()]), \
                    patch("builtins.open", side_effect=error) as reader:
                self.assertTrue(performance._process_is_running(123))
                self.assertFalse(performance._process_is_running(123))
                reader.assert_called_once()
        reader = mock_open()
        reader().read.side_effect = PermissionError()
        with patch.object(performance.sys, "platform", "linux"), \
                patch.object(performance.os, "kill"), patch("builtins.open", reader):
            self.assertTrue(performance._process_is_running(123))
        reader().__exit__.assert_called_once()

    def test_non_linux_posix_retains_kill_probe_without_procfs_or_ps(self):
        for platform in ("darwin", "freebsd14", "aix"):
            with self.subTest(platform=platform):
                self.probe(stat_record(), True, platform)

    def test_containment_accepts_zombie_but_still_rejects_live_pid(self):
        for state in (b"Z", b"S"):
            with self.subTest(state=state), \
                    patch.object(performance.sys, "platform", "linux"), \
                    patch.object(performance.os, "kill"), \
                    patch("builtins.open", mock_open(read_data=stat_record(state))), \
                    patch.object(performance.time, "monotonic", side_effect=[0.0, 10.0]), \
                    patch.object(performance.time, "sleep",
                                 side_effect=AssertionError("unexpected real wait")):
                if state == b"Z":
                    performance._assert_pid_stopped(123, "mock child")
                else:
                    with self.assertRaisesRegex(AssertionError, "survived containment cleanup"):
                        performance._assert_pid_stopped(123, "mock child")


if __name__ == "__main__":
    unittest.main()
