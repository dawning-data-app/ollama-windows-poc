"""Serve the same read-only MCP tool on Mac and Windows."""

import argparse
from collections import Counter
from hmac import compare_digest
import logging
import os
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from arena_csv import CsvRead, read_snapshot

LOG = logging.getLogger("arena_csv_mcp")


class ToolResult(CsvRead):
    read_id: str


class CsvMCP(FastMCP):
    async def call_tool(self, name, arguments):
        # FastMCP 1.x otherwise lets its validator discard extra arguments.
        if name == "read_arena_csv" and arguments.keys() != {"months"}:
            raise ToolError("read_arena_csv 只接受 months 參數。")
        return await super().call_tool(name, arguments)


class ArenaTokenVerifier(TokenVerifier):
    def __init__(self, token: str):
        self.token = token.encode("utf-8")

    async def verify_token(self, token: str) -> AccessToken | None:
        if compare_digest(self.token, token.encode("utf-8")):
            return AccessToken(token=token, client_id="arena-csv-poc", scopes=["arena:read"])
        return None


def create_server(root: Path, token: str, port: int) -> FastMCP:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("ARENA_CSV_DATA_DIR 必須是既有資料夾。")
    if not token or not token.isascii() or not token.isprintable() or any(char.isspace() for char in token):
        raise ValueError("ARENA_CSV_MCP_TOKEN 必須是有效的非空 ASCII Bearer token。")

    server = CsvMCP(
        "臺北小巨蛋場地租用資料集",
        host="127.0.0.1",
        port=port,
        stateless_http=True,
        json_response=True,
        token_verifier=ArenaTokenVerifier(token),
        auth=AuthSettings(
            issuer_url=f"http://127.0.0.1:{port}",
            resource_server_url=None,
            required_scopes=["arena:read"],
        ),
    )

    @server.tool()
    def read_arena_csv(months: list[str]) -> ToolResult:
        """讀取臺北小巨蛋場地租用 CSV。months 是 2026 年 YYYY-MM 清單。回傳來源、租用紀錄與未涵蓋月份。"""
        read_id = uuid4().hex
        try:
            result = read_snapshot(root, months)
        except ValueError as error:
            LOG.warning("read_id=%s outcome=error detail=%s", read_id, error)
            raise ToolError(f"{error}（read_id={read_id}）") from None
        file_counts = Counter(row["source_file"] for row in result["rows"])
        LOG.info(
            "read_id=%s months=%s available=%s missing=%s files=%s",
            read_id, sorted(set(months)), result["available_months"], result["missing_months"], dict(file_counts),
        )
        return {**result, "read_id": read_id}

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port 必須介於 1 和 65535。")
    root = os.environ.get("ARENA_CSV_DATA_DIR")
    if not root:
        parser.error("請設定 ARENA_CSV_DATA_DIR。")
    try:
        server = create_server(Path(root), os.environ.get("ARENA_CSV_MCP_TOKEN", ""), args.port)
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
