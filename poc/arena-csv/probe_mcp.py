"""Verify the hosted Taipei Arena MCP through the official SDK client."""

import asyncio
from collections import defaultdict
import json
import os
from secrets import token_urlsafe
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

TOOL = "read_arena_csv"
PREFIX = "臺北小巨蛋場地租用資訊_"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify_unauthorized(url, headers):
    request = Request(
        url,
        data=b'{}',
        headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            raise RuntimeError(f"未授權請求意外取得 HTTP {response.status}")
    except HTTPError as error:
        require(error.code == 401, f"未授權請求預期 HTTP 401，實際 {error.code}")


def check_rows(result, expected):
    require(not result["missing_months"], "有預期來源卻回報未涵蓋")
    actual = defaultdict(list)
    for row in result["rows"]:
        actual[row["source_file"]].append(row["source_line"])
    require(dict(actual) == expected, f"來源檔或行號不符：{dict(actual)}")


async def probe(url, token):
    receipts = {}
    async with streamablehttp_client(
        url, headers={"Authorization": f"Bearer {token}"}, timeout=15, sse_read_timeout=20,
    ) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            require([tool.name for tool in tools.tools] == [TOOL], "MCP 工具清單不符")
            for months, expected in (
                (["2026-01"], {f"{PREFIX}202601_V2.csv": list(range(2, 7))}),
                (["2026-07", "2026-08"], {
                    f"{PREFIX}202607.csv": list(range(2, 6)),
                    f"{PREFIX}202608.csv": list(range(2, 8)),
                }),
                (["2026-11"], None),
            ):
                result = await session.call_tool(TOOL, {"months": months})
                require(not result.isError and result.structuredContent, f"{months} 查詢失敗")
                data = result.structuredContent
                require(data["available_months"] == [f"2026-{month:02d}" for month in range(1, 11)], "清冊不符")
                require(bool(data["read_id"]), "缺少 read_id")
                if expected is None:
                    require(data["missing_months"] == months and not data["rows"], "11 月應回報未涵蓋與空列")
                else:
                    check_rows(data, expected)
                receipts[",".join(months)] = {
                    "read_id": data["read_id"], "rows": len(data["rows"]), "missing_months": data["missing_months"],
                }

            invalid_month = await session.call_tool(TOOL, {"months": ["2025-12"]})
            require(invalid_month.isError, "服務接受了非法月份")
            extra_path = await session.call_tool(TOOL, {"months": ["2026-07"], "path": "arbitrary.csv"})
            require(extra_path.isError, "服務接受了額外路徑參數")

    verify_unauthorized(url, {})
    verify_unauthorized(url, {"Authorization": f"Bearer {token_urlsafe(32)}"})
    print(json.dumps({"tool": TOOL, "reads": receipts, "invalid_inputs": "rejected", "unauthorized": "HTTP 401"}))


if __name__ == "__main__":
    asyncio.run(probe(os.environ["ARENA_CSV_MCP_URL"], os.environ["ARENA_CSV_MCP_TOKEN"]))
