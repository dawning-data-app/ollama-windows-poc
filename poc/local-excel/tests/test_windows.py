"""Native Windows regressions; no policy provisioning or model calls."""

from ctypes import wintypes
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

if os.name == "nt":
    import _winapi
    import windows_boundary
    import windows_job
    import windows_poc
    import windows_watchdog


@unittest.skipUnless(os.name == "nt", "requires native Windows")
class WindowsTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.run = Path(folder.name).resolve()
        self.workspace = self.run / "workspace"
        self.workspace.mkdir()
        self.evidence = self.run / "evidence"
        self.evidence.mkdir()

    def test_all_entrypoints_fail_before_network_or_process_without_policy(self):
        for interface in ("cli", "official", "chamber"):
            (self.run / "manifest.json").write_text(
                json.dumps({"windows": True, "interface": interface}), encoding="utf-8",
            )
            with (self.subTest(interface=interface), patch("poc.api") as api,
                  patch("windows_job.launch") as launch):
                with self.assertRaisesRegex(RuntimeError, "approved AppContainer"):
                    windows_poc.guarded_backend(self.run, interface, [])
                api.assert_not_called()
                launch.assert_not_called()

    def test_win32_quoting_and_job_stop_include_descendant(self):
        marker = self.workspace / "銷售 資料.txt"
        script = (
            "import pathlib, subprocess, sys, time\n"
            "child = subprocess.Popen([sys.executable, '-I', '-c', 'import time; time.sleep(30)'])\n"
            "pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding='utf-8')\n"
            "time.sleep(30)\n"
        )
        with (open(os.devnull, "rb") as stdin, tempfile.TemporaryFile() as stdout,
              tempfile.TemporaryFile() as stderr):
            with windows_job.launch([sys.executable, "-I", "-c", script, marker.name],
                                    self.workspace, os.environ, stdio=(stdin, stdout, stderr)) as process:
                expires = time.monotonic() + 5
                while not marker.is_file() or marker.stat().st_size == 0:
                    self.assertLess(time.monotonic(), expires)
                    self.assertIsNone(process.poll(50))
                pid = int(marker.read_text(encoding="utf-8"))
                open_process = windows_job.bind(windows_job.kernel, "OpenProcess", wintypes.HANDLE,
                                                wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
                child = windows_job.require(open_process(0x00100000, False, pid))
                try:
                    process.stop(124)
                    self.assertEqual(process.poll(3000), 124)
                    self.assertEqual(windows_job.wait(child, 3000), 0)
                finally:
                    windows_job.close(child)

    def test_deadline_stops_live_owned_job_and_records_identity(self):
        with (open(os.devnull, "rb") as stdin, tempfile.TemporaryFile() as stdout,
              tempfile.TemporaryFile() as stderr):
            with windows_job.launch([sys.executable, "-I", "-c", "import time; time.sleep(30)"],
                                    self.workspace, os.environ, stdio=(stdin, stdout, stderr)) as process:
                expected = process.identity()
                sample = {
                    "available_ram": 14 * windows_watchdog.GIB,
                    "commit_headroom": 16 * windows_watchdog.GIB, "pagefile_mib": 0, "gpu_error": [],
                }
                with patch("windows_watchdog.sample", return_value=sample):
                    code = windows_watchdog.supervise(process, self.run, os.environ["SystemRoot"],
                                                       time.monotonic() + 0.4)
                self.assertEqual(code, 124)
                self.assertEqual(process.poll(1000), 124)
        receipt = json.loads((self.evidence / "stops.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(receipt["pid"], expected["pid"])
        self.assertEqual(receipt["created_filetime"], expected["created_filetime"])
        self.assertIn("deadline", receipt["reason"])

    def test_explicit_gui_finish_stops_only_the_owned_job(self):
        with (open(os.devnull, "rb") as stdin, tempfile.TemporaryFile() as stdout,
              tempfile.TemporaryFile() as stderr):
            with windows_job.launch([sys.executable, "-I", "-c", "import time; time.sleep(30)"],
                                    self.workspace, os.environ, stdio=(stdin, stdout, stderr)) as process:
                sample = {"available_ram": 14 * windows_watchdog.GIB,
                          "commit_headroom": 16 * windows_watchdog.GIB, "pagefile_mib": 0, "gpu_error": []}
                with (patch("windows_watchdog.sample", return_value=sample),
                      patch("windows_poc.model.stop") as stop_model):
                    code = windows_watchdog.supervise(process, self.run, os.environ["SystemRoot"],
                                                       time.monotonic() + 2, stop_requested=lambda: True,
                                                       requested_code=0, on_stop=stop_model)
                    stop_model.assert_not_called()
                self.assertEqual(code, 0)
                self.assertEqual(process.poll(1000), 0)

    def test_watchdog_identifies_listener_pid_and_exact_ipv4_address(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            self.assertEqual(windows_watchdog.listeners(port),
                             [{"address": "127.0.0.1", "pid": os.getpid()}])

    def test_run_reparse_point_cannot_be_read_by_evaluator(self):
        target = self.evidence / "canary"
        target.mkdir()
        junction = self.workspace / "outside-link"
        _winapi.CreateJunction(str(target), str(junction))
        try:
            with self.assertRaisesRegex(ValueError, "reparse point"):
                windows_boundary.safe_path(self.run, junction / "canary.txt")
        finally:
            junction.rmdir()

    def test_resource_floors_and_pagefile_growth(self):
        guard = windows_watchdog.ResourceStops()
        sample = {"available_ram": 4 * windows_watchdog.GIB,
                  "commit_headroom": 13 * windows_watchdog.GIB, "pagefile_mib": 0, "gpu_error": []}
        self.assertIsNone(guard.observe(0, sample))
        self.assertIn("RAM", guard.observe(5, sample))
        guard = windows_watchdog.ResourceStops()
        sample["available_ram"] = 11 * windows_watchdog.GIB
        self.assertIsNone(guard.observe(0, sample))
        sample["pagefile_mib"] = 512
        self.assertIn("Pagefile", guard.observe(30, sample))


if __name__ == "__main__":
    unittest.main()
