"""Native Windows regressions; no policy provisioning or model calls."""

from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
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

    def test_portless_official_cli_reaches_policy_check(self):
        (self.run / "manifest.json").write_text(
            json.dumps({"windows": True, "interface": "official"}), encoding="utf-8",
        )
        with (patch.object(sys, "argv", ["windows_poc.py", "official", str(self.run)]),
              patch.dict(os.environ, {"OPENCODE_CALLER": "vscode"}, clear=True),
              patch("pathlib.Path.cwd", return_value=self.workspace),
              patch("sys.stderr") as stderr, patch("windows_poc.run_backend") as backend):
            self.assertEqual(windows_poc.main(), 2)
        self.assertIn("approved AppContainer", stderr.write.call_args_list[0].args[0])
        backend.assert_not_called()

    def test_official_port_must_match_extension(self):
        port = 40000
        with (patch("pathlib.Path.cwd", return_value=self.workspace),
              patch.dict(os.environ, {"_EXTENSION_OPENCODE_PORT": str(port)}, clear=True),
              patch("windows_poc.guarded_backend") as backend):
            for invalid in (None, 40001, 1024):
                with self.subTest(port=invalid), self.assertRaisesRegex(ValueError, "extension"):
                    windows_poc.official(self.run, invalid)
            backend.assert_not_called()
            windows_poc.official(self.run, port)
        args = ["--hostname", "127.0.0.1", "--port", str(port),
                "--agent", "excel", "--model", f"ollama/{windows_poc.poc.MODEL}"]
        backend.assert_called_once_with(self.run, "official", args, port=port)

    def test_portless_official_backend_keeps_arguments_and_checks_caller(self):
        with (patch("pathlib.Path.cwd", return_value=self.workspace),
              patch.dict(os.environ, {}, clear=True),
              patch("windows_poc.guarded_backend") as backend):
            with self.assertRaisesRegex(ValueError, "extension"):
                windows_poc.official(self.run)
            backend.assert_not_called()
            os.environ["OPENCODE_CALLER"] = "vscode"
            windows_poc.official(self.run)
        args = ["--agent", "excel", "--model", f"ollama/{windows_poc.poc.MODEL}"]
        backend.assert_called_once_with(self.run, "official", args, port=None)

    def test_portless_finish_and_export_check_process_identity(self):
        with (windows_job.launch([sys.executable, "-I", "-c", "import time; time.sleep(30)"],
                                 self.workspace, os.environ) as process,
              patch("windows_poc.checked_run", return_value=(self.run, {"interface": "official"}, {})),
              patch("windows_watchdog.listeners") as listeners,
              patch("windows_poc.control_command") as control):
            receipt = {"run": self.run.name, "port": None, **process.identity()}
            mismatched = {**receipt, "created_filetime": receipt["created_filetime"] - 1}
            path = self.evidence / "launch.json"
            path.write_text(json.dumps(mismatched), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "active GUI backend"):
                windows_poc.finish_gui(self.run)
            self.assertFalse((self.evidence / "finish.request").exists())

            path.write_text(json.dumps(receipt), encoding="utf-8")
            windows_poc.finish_gui(self.run)
            self.assertTrue((self.evidence / "finish.request").is_file())
            with self.assertRaisesRegex(RuntimeError, "Stop the owned OpenCode"):
                windows_poc.export_session(self.run, ["session", "list"])
            control.assert_not_called()

            process.stop(0)
            self.assertEqual(process.poll(3000), 0)
            self.assertIs(windows_poc.export_session(self.run, ["session", "list"]), control.return_value)
            listeners.assert_not_called()

    def test_backend_lease_creates_shared_directory_and_stays_exclusive(self):
        root = self.run / "poc-local"
        model_store = root / "models"
        model_store.mkdir(parents=True)
        lease = root / "evidence/active-opencode.json"
        with patch("windows_poc.model.store", return_value=model_store):
            with windows_poc.backend_lease(self.run, {}):
                self.assertEqual(json.loads(lease.read_text(encoding="utf-8"))["run"], self.run.name)
                with self.assertRaises(FileExistsError), windows_poc.backend_lease(self.run, {}):
                    self.fail("A second backend acquired the lease")
                self.assertTrue(lease.is_file())
            self.assertFalse(lease.exists())

    def test_prepare_seeds_and_verifies_isolated_ripgrep_cache(self):
        ripgrep = self.evidence / "rg.exe"
        ripgrep.write_bytes(b"fixture ripgrep")
        digest = windows_poc.poc.sha256(ripgrep)
        paths = dict.fromkeys(("python", "uv", "opencode", "bash", "code", "ollama", "ripgrep",
                               "uv_cache", "uv_root", "opencode_root", "git_root", "python_root"), str(ripgrep))

        def command(argv, run, name, timeout, env):
            if name == "opencode-version":
                self.assertEqual((Path(env["XDG_CACHE_HOME"]) / "opencode/bin/rg.exe").read_bytes(),
                                 ripgrep.read_bytes())
                (run / "evidence/opencode-version.stdout").write_text("1.19.5", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0)

        deadline = datetime.now(timezone.utc) + timedelta(minutes=1)
        with (patch("windows_poc.tools_at", return_value=paths),
              patch("windows_poc.poc.command", side_effect=command) as run_command):
            with self.assertRaisesRegex(ValueError, "Bundled Windows ripgrep"):
                windows_poc.prepare("official", "sales", self.run, self.run, self.run, deadline)
            run_command.assert_not_called()
            with patch("windows_poc.RIPGREP_SHA", digest):
                run = windows_poc.prepare("official", "sales", self.run, self.run, self.run, deadline)
                manifest = windows_poc.poc.read_json(run / "manifest.json")
                cache = run / "cache/opencode/bin/rg.exe"
                self.assertEqual(windows_poc.poc.sha256(cache), digest)
                cache.write_bytes(b"modified")
                with self.assertRaisesRegex(RuntimeError, "ripgrep cache"):
                    windows_poc.verify_inputs(run, manifest)

    def test_vscode_home_is_fresh_and_excludes_provider_keys(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fixture-only", "OPENCODE_CONFIG_CONTENT": "unexpected"}):
            env = windows_poc.gui_environment(self.run)
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("OPENCODE_CONFIG_CONTENT", env)
        self.assertEqual(Path(env["USERPROFILE"]), self.run / "vscode-home")
        self.assertTrue(Path(env["LOCALAPPDATA"]).is_dir())
        self.assertTrue(Path(env["TEMP"]).is_dir())

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
