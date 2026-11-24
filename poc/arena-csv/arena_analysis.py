"""Compute compact, reproducible summaries of verified Arena CSV rows."""

from calendar import monthrange
from collections import Counter, defaultdict
from datetime import date, timedelta
from itertools import groupby
from typing import Literal

from arena_csv import COLUMNS, SOURCE_FILES, CsvRead, parse_date

Operation = Literal["counts", "overlaps", "uncovered"]


def summarize(snapshot: CsvRead, months: list[str], operation: Operation) -> dict:
    covered = sorted(set(months).intersection(snapshot["available_months"]))
    rows = snapshot["rows"]
    files = {month: SOURCE_FILES[month] for month in covered}
    if operation == "counts":
        types = Counter(str(row[COLUMNS[4]]) for row in rows)
        counts = Counter(str(row["source_file"]) for row in rows)
        by_month = {month: counts[filename] for month, filename in files.items()}
        highest = max(by_month.values(), default=None)
        return {
            "by_type": dict(sorted(types.items())),
            "by_month": by_month,
            "total_rows": len(rows),
            "peak_months": [month for month, count in by_month.items() if count == highest],
            "peak_count": highest,
            "source_files": list(files.values()),
        }

    bookings = defaultdict(list)
    for row in rows:
        start = parse_date(str(row[COLUMNS[1]]))
        end = parse_date(str(row[COLUMNS[2]]))
        source = {
            "event": row[COLUMNS[3]],
            "source_file": row["source_file"],
            "source_line": row["source_line"],
        }
        for offset in range((end - start).days + 1):
            bookings[start + timedelta(days=offset)].append(source)

    if operation == "overlaps":
        return {
            "dates": [
                {"date": day.isoformat(), "count": len(records), "records": records}
                for day, records in sorted(bookings.items()) if len(records) >= 2
            ],
            "source_files": list(files.values()),
        }

    ranges = []
    for month in covered:
        year, month_number = map(int, month.split("-"))
        last_day = monthrange(year, month_number)[1]
        days = (date(year, month_number, day) for day in range(1, last_day + 1))
        for has_record, group in groupby(days, key=bookings.__contains__):
            if not has_record:
                gap = list(group)
                ranges.append({"start": gap[0].isoformat(), "end": gap[-1].isoformat(), "days": len(gap)})
    return {
        "ranges": ranges,
        "total_days": sum(gap["days"] for gap in ranges),
        "source_rows": [
            {"source_file": row["source_file"], "source_line": row["source_line"]} for row in rows
        ],
        "source_files": list(files.values()),
        "rental_availability": "unknown",
        "evidence_scope": "未被 CSV 租用紀錄涵蓋，實際可租性待確認。",
    }
