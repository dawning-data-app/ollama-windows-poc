import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Iterable, Union
from unittest import mock
from urllib import error

import client
# 讓 get_type_hints 可在此模組解析 HttpResult 內的遞迴 forward reference。
from client import JsonValue as JsonValue


class ClientTests(unittest.TestCase):
    def invoke(
        self, replies: Iterable[Union[client.HttpResult, Exception]]
    ) -> tuple[client.ExitCode, str, str, mock.MagicMock]:
        output = io.StringIO()
        errors = io.StringIO()
        with mock.patch.object(client, "_json_request", side_effect=replies) as call:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = client.run("http://127.0.0.1:11434", "tinyllama:latest", "Hi", 5)
        return code, output.getvalue(), errors.getvalue(), call

    def test_generated_response(self) -> None:
        code, output, _, call = self.invoke([
            (200, {"models": [{"name": "tinyllama:latest"}]}),
            (200, {"response": " Hello! "}),
        ])
        self.assertEqual(code, 0)
        self.assertIn("GENERATED HTTP 200: Hello!", output)
        self.assertEqual(call.call_args_list[1].args[2], {
            "model": "tinyllama:latest", "prompt": "Hi", "stream": False,
        })

    def test_ollama_error_proves_reachability_but_exits_nonzero(self) -> None:
        code, output, _, _ = self.invoke([
            (200, {"models": []}),
            (404, {"error": "model not found"}),
        ])
        self.assertEqual(code, 2)
        self.assertIn("OLLAMA_API_ERROR HTTP 404", output)

    def test_wrong_service_does_not_prove_reachability(self) -> None:
        code, _, errors, call = self.invoke([(200, {"hello": "world"})])
        self.assertEqual(code, 3)
        self.assertIn("INVALID_RESPONSE", errors)
        self.assertEqual(call.call_count, 1)

    def test_transport_failure(self) -> None:
        code, _, errors, _ = self.invoke([client.TransportError("connection refused")])
        self.assertEqual(code, 3)
        self.assertIn("TRANSPORT_ERROR", errors)

    def test_empty_generation_is_invalid(self) -> None:
        code, _, errors, _ = self.invoke([(200, {"models": []}), (200, {"response": " "})])
        self.assertEqual(code, 3)
        self.assertIn("INVALID_RESPONSE", errors)

    def test_http_error_json_body_is_preserved(self) -> None:
        response = error.HTTPError(
            "http://127.0.0.1:11434/api/generate", 404, "Not Found", {},
            io.BytesIO(json.dumps({"error": "model not found"}).encode()),
        )
        with mock.patch.object(client, "_open", side_effect=response):
            status, body = client._json_request("http://127.0.0.1:11434/api/generate", 5, {"model": "x"})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "model not found")

    def test_non_json_body_is_invalid(self) -> None:
        fake_response = mock.MagicMock()
        fake_response.status = 200
        fake_response.read.return_value = b"<html>not Ollama</html>"
        fake_response.__enter__.return_value = fake_response
        with mock.patch.object(client, "_open", return_value=fake_response):
            with self.assertRaises(client.InvalidResponse):
                client._json_request("http://127.0.0.1:11434/api/tags", 5)

    def test_reads_only_base_url_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("# local settings\nOTHER=value\nOLLAMA_BASE_URL=http://host.example:11434\n")
            self.assertEqual(client._env_base_url(path), "http://host.example:11434")

    def test_cli_url_overrides_env_file(self) -> None:
        with mock.patch.object(client, "_env_base_url", return_value="http://from-env:11434"):
            with mock.patch.object(client, "run", return_value=0) as run:
                self.assertEqual(client.main(["--base-url", "http://override:11434"]), 0)
        self.assertEqual(run.call_args.args[0], "http://override:11434")

    def test_env_file_sets_default_url(self) -> None:
        with mock.patch.object(client, "_env_base_url", return_value="http://from-env:11434"):
            with mock.patch.object(client, "run", return_value=0) as run:
                self.assertEqual(client.main([]), 0)
        self.assertEqual(run.call_args.args[0], "http://from-env:11434")


if __name__ == "__main__":
    unittest.main()
