import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from src.services.DB_Handler.InsertData import InsertData


class InsertDataTests(unittest.TestCase):
    def test_api_and_csv_headers_use_the_same_cleaning_path(self):
        api_frame = pd.DataFrame(
            [
                {
                    "trade_date": "2026-10-23",
                    "symbol": " AAA ",
                    "name": "Alpha",
                    "open": 10,
                    "high": 12,
                    "low": 9,
                    "closingPrice": 11,
                    "sharevolume": 100,
                    "turnover": 1100,
                    "percentageChange": 10,
                }
            ]
        )
        csv_frame = pd.DataFrame(
            [
                {
                    "trade_date": "2026-10-23",
                    "symbol": "AAA",
                    "name": "Alpha",
                    "open": 10,
                    "high": 12,
                    "low": 9,
                    "close": 11,
                    "volume": 100,
                    "turnover": 1100,
                    "pct_change": 10,
                }
            ]
        )

        pd.testing.assert_frame_equal(
            InsertData.clean_market_data(api_frame),
            InsertData.clean_market_data(csv_frame),
        )

    def test_database_column_headers_are_accepted_from_csv(self):
        database_columns_frame = pd.DataFrame(
            [
                {
                    "trade_date": "2026-10-23",
                    "symbol": "AAA",
                    "name": "Alpha",
                    "open_price": 10,
                    "high": 12,
                    "low": 9,
                    "close_price": 11,
                    "volume": 100,
                    "turnover": 1100,
                    "pct_change": 10,
                }
            ]
        )
        expected_frame = pd.DataFrame(
            [
                {
                    "trade_date": "2026-10-23",
                    "symbol": "AAA",
                    "name": "Alpha",
                    "open": 10,
                    "high": 12,
                    "low": 9,
                    "close": 11,
                    "volume": 100,
                    "turnover": 1100,
                    "pct_change": 10,
                }
            ]
        )

        pd.testing.assert_frame_equal(
            InsertData.clean_market_data(database_columns_frame),
            InsertData.clean_market_data(expected_frame),
        )

    def test_csv_upload_cleans_rows_and_inserts_through_shared_method(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "market_data.csv"
            pd.DataFrame(
                [
                    {
                        "trade_date": "2026-10-23",
                        "symbol": " AAA ",
                        "name": "Alpha",
                        "open": 10,
                        "high": 12,
                        "low": 9,
                        "close": 11,
                        "volume": 100,
                    },
                    {
                        "trade_date": "invalid",
                        "symbol": "BAD",
                        "name": "Invalid date",
                        "open": 10,
                        "high": 12,
                        "low": 9,
                        "close": 11,
                        "volume": 100,
                    },
                ]
            ).to_csv(csv_path, index=False)

            importer = InsertData.__new__(InsertData)
            importer.query_obj = Mock()
            importer.query_obj.insertCSV.return_value = (True, "ok", None)

            success, message, _ = importer.insert_csv_file(str(csv_path))

        self.assertTrue(success, message)
        self.assertIn("1 market data rows", message)
        inserted_rows = importer.query_obj.insertCSV.call_args.kwargs["values"]
        self.assertEqual(
            inserted_rows,
            [("2026-10-23", "AAA", "Alpha", 10, 12, 9, 11, 100, 0, 0)],
        )

    def test_csv_upload_reports_missing_required_columns(self):
        importer = InsertData.__new__(InsertData)
        importer.query_obj = Mock()

        success, message, _ = importer.insert_dataframe(
            pd.DataFrame([{"symbol": "AAA"}])
        )

        self.assertFalse(success)
        self.assertIn("missing required columns", message)
        importer.query_obj.insertCSV.assert_not_called()


if __name__ == "__main__":
    unittest.main()
