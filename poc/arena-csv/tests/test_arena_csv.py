import csv
from pathlib import Path
import tempfile
import unittest

from arena_csv import COLUMNS, SOURCE_FILES, CsvSnapshotError, read_snapshot


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.row = ["測試廠商", "", "", "測試活動", "娛樂"]
        for month in SOURCE_FILES:
            self.write_month(month)

    def write_month(self, month, rows=None):
        path = self.root / SOURCE_FILES[month]
        if rows is None:
            day = month.replace("-", "") + "01"
            rows = [COLUMNS, [self.row[0], day, day, *self.row[3:]]]
        with path.open("w", encoding="big5", newline="") as output:
            csv.writer(output).writerows(rows)

    def test_returns_ordered_original_rows_once_and_v2_source(self):
        result = read_snapshot(self.root, ["2026-08", "2026-01", "2026-08"])
        self.assertEqual(result["available_months"], list(SOURCE_FILES))
        self.assertEqual(result["missing_months"], [])
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(
            result["rows"][0],
            {**dict(zip(COLUMNS, ["測試廠商", "20260101", "20260101", "測試活動", "娛樂"])),
             "source_file": "臺北小巨蛋場地租用資訊_202601_V2.csv", "source_line": 2},
        )
        self.assertEqual(result["rows"][1]["source_file"], SOURCE_FILES["2026-08"])

    def test_uncovered_is_distinct_from_incomplete_snapshot(self):
        result = read_snapshot(self.root, ["2026-11"])
        self.assertEqual(result["missing_months"], ["2026-11"])
        self.assertEqual(result["rows"], [])
        (self.root / SOURCE_FILES["2026-07"]).unlink()
        with self.assertRaisesRegex(CsvSnapshotError, SOURCE_FILES["2026-07"]):
            read_snapshot(self.root, ["2026-11"])

    def test_rejects_invalid_months(self):
        for months in ([], ["2025-12"], ["2026-13"], ["../202601"], ["2026-01"] * 13):
            with self.subTest(months=months), self.assertRaisesRegex(ValueError, "YYYY-MM"):
                read_snapshot(self.root, months)

    def test_rejects_wrong_header_invalid_dates_or_invalid_encoding(self):
        month = "2026-07"
        path = self.root / SOURCE_FILES[month]
        for rows in (
            [COLUMNS[:-1]],
            [COLUMNS, ["測試", "20260731", "20260701", "測試", "娛樂"]],
            [COLUMNS, ["測試", "20260801", "20260801", "測試", "娛樂"]],
            [COLUMNS, ["測試", "20260799", "20260799", "測試", "娛樂"]],
        ):
            with self.subTest(rows=rows):
                self.write_month(month, rows)
                with self.assertRaisesRegex(CsvSnapshotError, "格式錯誤"):
                    read_snapshot(self.root, [month])
        path.write_bytes(b"\xff\xff")
        with self.assertRaisesRegex(CsvSnapshotError, "格式錯誤"):
            read_snapshot(self.root, [month])

    def test_source_line_is_start_of_multiline_record(self):
        month = "2026-07"
        row = ["測試", "20260701", "20260701", "測試\n活動", "娛樂"]
        self.write_month(month, [COLUMNS, row, row])
        result = read_snapshot(self.root, [month])
        self.assertEqual([record["source_line"] for record in result["rows"]], [2, 4])
        self.assertEqual(result["rows"][0]["活動名稱"], "測試\n活動")

    def test_mapped_filename_cannot_redirect_to_another_file(self):
        month = "2026-07"
        path = self.root / SOURCE_FILES[month]
        path.unlink()
        try:
            path.symlink_to(self.root / SOURCE_FILES["2026-08"])
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {error}")
        with self.assertRaisesRegex(CsvSnapshotError, SOURCE_FILES[month]):
            read_snapshot(self.root, [month])


if __name__ == "__main__":
    unittest.main()
