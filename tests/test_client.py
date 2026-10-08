import contextlib
import io
import json
import unittest
from unittest import mock
from urllib import error

import client


class ClientTests(unittest.TestCase):
    def invoke(self, replies):
        output = io.StringIO()
        errors = io.StringIO()
        with mock.patch.object(client, "_json_request", side_effect=replies) as call:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = client.run("http://127.0.0.1:11434", "tinyllama:latest", "Hi", 5)
        return code, output.getvalue(), errors.getvalue(), call

    def test_generated_response(self):
        code, output, _, call = self.invoke([
            (200, {"models": [{"name": "tinyllama:latest"}]}),
            (200, {"response": " Hello! "}),
        ])
        self.assertEqual(code, 0)
        self.assertIn("GENERATED HTTP 200: Hello!", output)
        self.assertEqual(call.call_args_list[1].args[2], {
            "model": "tinyllama:latest", "prompt": "Hi", "stream": False,
        })

    def test_ollama_error_proves_reachability_but_exits_nonzero(self):
        code, output, _, _ = self.invoke([
            (200, {"models": []}),
            (404, {"error": "model not found"}),
        ])
        self.assertEqual(code, 2)
        self.assertIn("OLLAMA_API_ERROR HTTP 404", output)

    def test_wrong_service_does_not_prove_reachability(self):
        code, _, errors, call = self.invoke([(200, {"hello": "world"})])
        self.assertEqual(code, 3)
        self.assertIn("INVALID_RESPONSE", errors)
        self.assertEqual(call.call_count, 1)

    def test_transport_failure(self):
        code, _, errors, _ = self.invoke([client.TransportError("connection refused")])
        self.assertEqual(code, 3)
        self.assertIn("TRANSPORT_ERROR", errors)

    def test_empty_generation_is_invalid(self):
        code, _, errors, _ = self.invoke([(200, {"models": []}), (200, {"response": " "})])
        self.assertEqual(code, 3)
        self.assertIn("INVALID_RESPONSE", errors)

    def test_http_error_json_body_is_preserved(self):
        response = error.HTTPError(
            "http://127.0.0.1:11434/api/generate", 404, "Not Found", {},
            io.BytesIO(json.dumps({"error": "model not found"}).encode()),
        )
        with mock.patch.object(client, "_open", side_effect=response):
            status, body = client._json_request("http://127.0.0.1:11434/api/generate", 5, {"model": "x"})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "model not found")

    def test_non_json_body_is_invalid(self):
        fake_response = mock.MagicMock()
        fake_response.status = 200
        fake_response.read.return_value = b"<html>not Ollama</html>"
        fake_response.__enter__.return_value = fake_response
        with mock.patch.object(client, "_open", return_value=fake_response):
            with self.assertRaises(client.InvalidResponse):
                client._json_request("http://127.0.0.1:11434/api/tags", 5)


if __name__ == "__main__":
    unittest.main()
