"""Minimal Ollama HTTP connectivity probe (Python standard library only)."""

import argparse
import json
import socket
import sys
from pathlib import Path
from urllib import error, parse, request


class TransportError(Exception):
    pass


class InvalidResponse(Exception):
    pass


def _open(req, timeout):
    # A local or LAN Ollama request should not use a configured HTTP proxy.
    return request.build_opener(request.ProxyHandler({})).open(req, timeout=timeout)


def _json_request(url, timeout, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(
        url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    try:
        with _open(req, timeout) as response:
            status = response.status
            body = response.read()
    except error.HTTPError as exc:
        status = exc.code
        body = exc.read()
    except (error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        raise TransportError(str(exc)) from exc

    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidResponse("response is not valid JSON") from exc
    if not isinstance(result, dict):
        raise InvalidResponse("response is not a JSON object")
    return status, result


def _base_url(value):
    parsed = parse.urlsplit(value)
    if (
        parsed.scheme != "http"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise argparse.ArgumentTypeError("use an HTTP origin such as http://127.0.0.1:11434")
    try:
        port = parsed.port
    except ValueError as exc:
        raise argparse.ArgumentTypeError("invalid port") from exc
    if port is None:
        raise argparse.ArgumentTypeError("include the Ollama port, usually 11434")
    return value.rstrip("/")


def _env_base_url(path=None):
    """Read only OLLAMA_BASE_URL from the local, untracked .env file."""
    env_path = path or Path(__file__).resolve().with_name(".env")
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    for line in lines:
        key, separator, value = line.strip().partition("=")
        if separator and key == "OLLAMA_BASE_URL":
            return value.strip().strip('"\'')
    return None


def run(base_url, model, prompt, timeout):
    try:
        tags_status, tags = _json_request(f"{base_url}/api/tags", timeout)
        if tags_status != 200 or not isinstance(tags.get("models"), list):
            raise InvalidResponse("/api/tags did not return an Ollama model list")

        status, result = _json_request(
            f"{base_url}/api/generate",
            timeout,
            {"model": model, "prompt": prompt, "stream": False},
        )
    except TransportError as exc:
        print(f"TRANSPORT_ERROR: {exc}", file=sys.stderr)
        return 3
    except InvalidResponse as exc:
        print(f"INVALID_RESPONSE: {exc}", file=sys.stderr)
        return 3

    api_error = result.get("error")
    if isinstance(api_error, str) and api_error.strip():
        print(f"OLLAMA_API_ERROR HTTP {status}: {api_error}")
        return 2
    generated = result.get("response")
    if status == 200 and isinstance(generated, str) and generated.strip():
        print(f"GENERATED HTTP {status}: {generated.strip()}")
        return 0
    print(f"INVALID_RESPONSE: /api/generate returned HTTP {status} without response or error", file=sys.stderr)
    return 3


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", type=_base_url, help="overrides OLLAMA_BASE_URL in .env")
    parser.add_argument("--model", default="tinyllama:latest")
    parser.add_argument("--prompt", default="Reply with one short greeting.")
    parser.add_argument("--timeout", type=float, default=120.0, help="timeout in seconds per request")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        base_url = args.base_url or _base_url(_env_base_url() or "http://127.0.0.1:11434")
    except (OSError, UnicodeError, argparse.ArgumentTypeError) as exc:
        parser.error(f"invalid .env: {exc}")
    return run(base_url, args.model, args.prompt, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
