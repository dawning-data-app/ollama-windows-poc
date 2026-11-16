import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import load_workbook
import poc


class FixtureAndSessionTests(unittest.TestCase):
    def test_sales_fixture_matches_independent_oracle(self):
        book = load_workbook(poc.ROOT / "sales.xlsx", read_only=True, data_only=False)
        try:
            rows = list(book["Sales"].values)
            self.assertEqual(rows[0], ("date", "region", "product", "quantity", "unit_price"))
            self.assertEqual(len(rows), 13)
            self.assertTrue(all(not (isinstance(v, str) and v.startswith("=")) for row in rows for v in row))
            amounts = [row[3] * row[4] for row in rows[1:]]
            self.assertEqual(amounts, [100, 400, 300, 800, 500, 1200, 700, 1600, 900, 2000, 1100, 2400])
            oracle = poc.read_json(poc.ROOT / "oracle.json")
            self.assertEqual(sum(amounts), oracle["total_sales"])
            self.assertEqual(sum(amounts[:6]), oracle["monthly_sales"]["2026-01"])
        finally:
            book.close()

    def test_sessions_are_fresh_and_exclude_evaluator_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second = poc.prepare(Path(folder)), poc.prepare(Path(folder))
            self.assertNotEqual(first, second)
            names = {p.name for p in (first / "workspace").iterdir()}
            self.assertEqual(names, {".python-version", "pyproject.toml", "uv.lock", "opencode.json", "prompt.txt", "銷售 資料"})
            self.assertNotIn("12000", (first / "workspace" / "prompt.txt").read_text(encoding="utf-8"))
            self.assertEqual(poc.sha256(first / "workspace" / "uv.lock"), poc.sha256(poc.ROOT / "uv.lock"))
            poc.validate_config(poc.read_json(first / "workspace" / "opencode.json"), poc.MODEL)

    @unittest.skipIf(os.name == "nt", "legacy .venv probe; Windows uses the run-scoped locked runtime")
    def test_real_uv_sync_then_isolated_offline_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            run = poc.prepare(Path(folder))
            ready = poc.command(["uv", "sync", "--locked", "--offline", "--python", "3.12.12"],
                                run, "uv-sync", 60, poc.setup_environment())
            self.assertEqual(ready.returncode, 0)
            result = subprocess.check_output(
                ["uv", "run", "--locked", "--offline", "python", "-c",
                 "import sys,openpyxl; print(sys.executable); print(openpyxl.__version__)"],
                cwd=run / "workspace", env=poc.environment(run), text=True, timeout=30)
            self.assertIn(str(run / "workspace" / ".venv"), result)
            self.assertIn("3.1.5", result)

    def test_negative_fixtures(self):
        with tempfile.TemporaryDirectory() as folder:
            missing, corrupt = poc.prepare(Path(folder), "missing"), poc.prepare(Path(folder), "corrupt")
            self.assertFalse((missing / "workspace" / "銷售 資料").exists())
            self.assertFalse((corrupt / "workspace" / "銷售 資料" / "sales.xlsx").read_bytes().startswith(b"PK"))

    def test_refuses_agent_workspace_inside_evaluation_assets(self):
        with self.assertRaises(ValueError):
            poc.prepare(poc.ROOT / "runs")
        with self.assertRaises(ValueError):
            poc.prepare(poc.REPO_ROOT / "runs")

    def test_environment_does_not_inherit_keys_or_overrides(self):
        with tempfile.TemporaryDirectory() as folder:
            run = poc.prepare(Path(folder))
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only", "OPENCODE_CONFIG_CONTENT": "cloud"}):
                env = poc.environment(run)
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertNotEqual(env["OPENCODE_CONFIG_CONTENT"], "cloud")
            self.assertTrue(env["XDG_CONFIG_HOME"].startswith(str(run)))


class ValidationTests(unittest.TestCase):
    def test_rejects_cloud_models_allowlists_and_endpoints(self):
        for key, value in (("small_model", "openai/example"), ("enabled_providers", ["ollama", "openai"])):
            config = poc.config(poc.MODEL)
            config[key] = value
            with self.assertRaises(ValueError):
                poc.validate_config(config, poc.MODEL)
        config = poc.config(poc.MODEL)
        config["provider"]["ollama"]["options"]["baseURL"] = "https://example.com/v1"
        with self.assertRaises(ValueError):
            poc.validate_config(config, poc.MODEL)

    def test_numeric_types_and_rankings(self):
        for value in (True, "1", float("nan"), float("inf"), 2):
            self.assertTrue(poc.compare_answer(value, 1))
        self.assertTrue(poc.compare_answer(["北", "南"], ["南", "北"]))
        self.assertTrue(poc.compare_answer({"total": 1, "extra": 2}, {"total": 1}))
        self.assertEqual(poc.compare_answer({"total": 1.0}, {"total": 1}), [])

    def test_correct_answer_alone_cannot_pass_e2e(self):
        with tempfile.TemporaryDirectory() as folder:
            run = poc.prepare(Path(folder))
            poc.write_json(run / "workspace" / "answer.json", poc.read_json(poc.ROOT / "oracle.json"))
            result = poc.check(run)
            self.assertFalse(result["e2e_passed"])
            self.assertEqual(result["status"], "not-passed")
            self.assertIn("no completed Python tool execution evidence", result["errors"])

    def test_probe_requires_tools_and_actual_64k(self):
        tags = {"models": [{"name": poc.MODEL, "digest": "test"}]}
        with patch.object(poc, "api", side_effect=[tags, {"capabilities": []}]):
            with self.assertRaisesRegex(ValueError, "tools"):
                poc.preflight(poc.MODEL)
        call = {"message": {"tool_calls": [{"function": {"name": "local_probe", "arguments": {"value": 7}}}]}}
        with patch.object(poc, "api", side_effect=[tags, {"capabilities": ["tools"]}, call, {"choices": []},
                                                   {"models": [{"name": poc.MODEL, "context_length": 32768}]}]):
            with self.assertRaisesRegex(ValueError, "65536"):
                poc.preflight(poc.MODEL)


if __name__ == "__main__":
    unittest.main()
