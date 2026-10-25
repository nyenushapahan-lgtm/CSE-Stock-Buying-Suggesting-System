import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from src.services.main_window.MainData import MainData
from src.windows.main_window.MainWindow import MainWindow


class MainDataTests(unittest.TestCase):
    def test_sector_volumes_fall_back_to_latest_bundled_dataset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            prices_path = temp_path / "prices.csv"
            mapping_path = temp_path / "mapping.csv"
            cash_path = temp_path / "sector_volumes.json"

            pd.DataFrame(
                [
                    {"trade_date": "2024-01-01", "symbol": "AAA", "volume": 5},
                    {"trade_date": "2024-01-01", "symbol": "BBB", "volume": 2},
                    {"trade_date": "2024-01-02", "symbol": "AAA", "volume": 7},
                    {"trade_date": "2024-01-02", "symbol": "BBB", "volume": 3},
                    {"trade_date": "2024-01-02", "symbol": "UNKNOWN", "volume": 99},
                ]
            ).to_csv(prices_path, index=False)
            pd.DataFrame(
                [
                    {"symbol": "AAA", "sector_name": "Banks"},
                    {"symbol": "BBB", "sector_name": "Technology"},
                ]
            ).to_csv(mapping_path, index=False)

            main_data = MainData.__new__(MainData)
            main_data.CASH_FILE = str(cash_path)
            main_data.CASH_DURATION = timedelta(days=1)
            main_data.SECTOR_VOLUME_DATA_FILE = str(prices_path)
            main_data.SECTOR_MAPPING_DATA_FILE = str(mapping_path)
            main_data.db_read = Mock()
            main_data.db_read.getting_all_sector_volumes.return_value = (
                False,
                "sector volume query failed",
                None,
            )
            main_data.readIndustryGroupName = Mock(
                return_value=(False, "sector table is unavailable", None)
            )

            success, message, volumes = main_data.getSectorWiseInvestmentsDetails()

            self.assertTrue(success)
            self.assertIn("2024-01-02", message)
            self.assertEqual(volumes, {"Banks": 7, "Technology": 3})
            self.assertEqual(main_data._load_from_cash(), volumes)

    def test_top_gainer_prices_fall_back_to_bundled_data_and_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            prices_path = temp_path / "prices.csv"
            cash_path = temp_path / "close_prices.json"
            rows = []
            for day in range(6):
                rows.extend(
                    [
                        {
                            "trade_date": f"2024-01-{day + 1:02}",
                            "symbol": "AAA",
                            "name": "Alpha",
                            "close": 10 + day,
                            "pct_change": 1,
                        },
                        {
                            "trade_date": f"2024-01-{day + 1:02}",
                            "symbol": "BBB",
                            "name": "Beta",
                            "close": 20 - day,
                            "pct_change": -1,
                        },
                    ]
                )
            pd.DataFrame(rows).to_csv(prices_path, index=False)

            main_data = MainData.__new__(MainData)
            main_data.CLOSE_PRICE_CASH_FILE = str(cash_path)
            main_data.CLOSE_PRICE_CASH_DURATION = timedelta(days=1)
            main_data.SECTOR_VOLUME_DATA_FILE = str(prices_path)
            main_data.findTop10Gainers = Mock(
                return_value=(False, "database unavailable", None)
            )

            success, message, dataset = main_data.loadClosedPrices()

            self.assertTrue(success)
            self.assertIn("2024-01-06", message)
            self.assertEqual(dataset[1], ["AAA", "BBB"])
            self.assertEqual(
                [point["close_price"] for point in dataset[0][0]],
                [10, 11, 12, 13, 14, 15],
            )
            self.assertEqual(main_data._load_close_prices_from_cash(), dataset)

            main_data.SECTOR_VOLUME_DATA_FILE = str(temp_path / "missing.csv")
            cached_success, cached_message, cached_dataset = main_data.loadClosedPrices()

            self.assertTrue(cached_success)
            self.assertIn("Cached", cached_message)
            self.assertEqual(cached_dataset, dataset)

    def test_dashboard_startup_loads_top_gainer_chart(self):
        main_window = MainWindow.__new__(MainWindow)
        main_window.showTop10Gainers = Mock()
        main_window.loadSuggestionsTable = Mock()
        main_window.loadSectorWiseInvestmentData = Mock()
        main_window.loadTimeSeriesData = Mock()
        main_window.logMsg = Mock()

        main_window.run_startup_tasks()

        main_window.loadTimeSeriesData.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
