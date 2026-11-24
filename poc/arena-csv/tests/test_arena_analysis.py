import unittest

from arena_analysis import summarize
from arena_csv import COLUMNS, SOURCE_FILES, CsvRead


def record(month, start, end, title, category, line):
    row = dict(zip(COLUMNS, ("示例廠商", start, end, title, category), strict=True))
    return {**row, "source_file": SOURCE_FILES[month], "source_line": line}


class ArenaAnalysisTests(unittest.TestCase):
    def test_counts_preserve_ties_and_include_covered_empty_month(self):
        months = ["2026-07", "2026-08", "2026-09", "2026-11"]
        snapshot: CsvRead = {
            "available_months": months[:3],
            "missing_months": months[3:],
            "rows": [
                record("2026-07", "20260701", "20260702", "示例甲", "體育", 2),
                record("2026-08", "20260801", "20260801", "示例乙", "娛樂", 2),
            ],
        }

        result = summarize(snapshot, months, "counts")

        self.assertEqual(result["by_type"], {"體育": 1, "娛樂": 1})
        self.assertEqual(result["by_month"], {"2026-07": 1, "2026-08": 1, "2026-09": 0})
        self.assertEqual(result["peak_months"], months[:2])
        self.assertEqual(result["peak_count"], 1)
        self.assertEqual(result["total_rows"], 2)

    def test_inclusive_overlap_and_gaps_keep_source_and_availability(self):
        month = "2026-08"
        snapshot: CsvRead = {
            "available_months": [month],
            "missing_months": [],
            "rows": [
                record(month, "20260803", "20260805", "示例甲", "體育", 2),
                record(month, "20260805", "20260807", "示例乙", "娛樂", 3),
            ],
        }

        overlap = summarize(snapshot, [month], "overlaps")["dates"]
        gaps = summarize(snapshot, [month], "uncovered")

        self.assertEqual([(item["date"], item["count"]) for item in overlap], [("2026-08-05", 2)])
        self.assertEqual([row["source_line"] for row in overlap[0]["records"]], [2, 3])
        self.assertEqual(gaps["ranges"], [
            {"start": "2026-08-01", "end": "2026-08-02", "days": 2},
            {"start": "2026-08-08", "end": "2026-08-31", "days": 24},
        ])
        self.assertEqual(gaps["total_days"], 26)
        self.assertEqual(gaps["rental_availability"], "unknown")


if __name__ == "__main__":
    unittest.main()
