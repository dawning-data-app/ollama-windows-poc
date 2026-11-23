"""Read the fixed Taipei Arena rental snapshot without modifying it."""

import csv
from datetime import date
from pathlib import Path
from typing import TypedDict

COLUMNS = ("廠商", "租用起始日", "租用結束日", "活動名稱", "活動類型")
MONTHS = tuple(f"2026-{month:02d}" for month in range(1, 13))
SOURCE_FILES = {
    month: f"臺北小巨蛋場地租用資訊_{month.replace('-', '')}{'_V2' if month == MONTHS[0] else ''}.csv"
    for month in MONTHS[:10]
}


class CsvSnapshotError(ValueError):
    """A file expected in the snapshot could not be used."""


class CsvRead(TypedDict):
    available_months: list[str]
    missing_months: list[str]
    rows: list[dict[str, str | int]]


def source_path(root: Path, filename: str) -> Path:
    path = root / filename
    try:
        if path.resolve(strict=True) == path and path.is_file():
            return path
    except (OSError, RuntimeError):
        pass
    raise CsvSnapshotError(f"來源不完整：{filename} 遺失或無法讀取。")


def parse_date(value: str) -> date:
    if len(value) != 8 or not value.isascii() or not value.isdecimal():
        raise ValueError("預期 YYYYMMDD")
    return date.fromisoformat(value)


def read_file(path: Path, month: str) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    line = 1
    try:
        with path.open(encoding="big5", newline="") as source:
            reader = csv.reader(source, strict=True)
            if tuple(next(reader, ())) != COLUMNS:
                raise ValueError("欄位不符合來源表頭")
            while True:
                line = reader.line_num + 1
                values = next(reader, None)
                if values is None:
                    break
                if len(values) != len(COLUMNS) or not all(values):
                    raise ValueError("欄位數量或欄值不完整")
                start, end = (parse_date(value) for value in values[1:3])
                if start > end or any(day.isoformat()[:7] != month for day in (start, end)):
                    raise ValueError("租用起訖日與月檔不符")
                row: dict[str, str | int] = dict(zip(COLUMNS, values, strict=True))
                row.update(source_file=path.name, source_line=line)
                rows.append(row)
    except (OSError, csv.Error, ValueError):
        raise CsvSnapshotError(f"來源不完整：{path.name} 第 {line} 行附近無法讀取或格式錯誤。") from None
    return rows


def read_snapshot(root: Path, months: list[str]) -> CsvRead:
    if not 1 <= len(months) <= len(MONTHS) or any(month not in MONTHS for month in months):
        raise ValueError("請提供 1–12 個 2026 年的月份，格式為 YYYY-MM。")

    sources = {month: source_path(root, filename) for month, filename in SOURCE_FILES.items()}
    requested = sorted(set(months))
    return {
        "available_months": list(sources),
        "missing_months": [month for month in requested if month not in sources],
        "rows": [
            row
            for month in requested
            if month in sources
            for row in read_file(sources[month], month)
        ],
    }
