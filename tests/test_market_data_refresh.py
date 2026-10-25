import unittest

import pandas as pd

from src.services.MarketDataRefresh import merge_market_data, normalize_market_data


class MarketDataRefreshTests(unittest.TestCase):
    def test_merge_preserves_history_and_replaces_refreshed_duplicate(self):
        existing = pd.DataFrame(
            [
                {
                    "trade_date": "2026-10-22",
                    "symbol": "AAA",
                    "name": "Old Name",
                    "open": 9,
                    "high": 10,
                    "low": 8,
                    "close": 9,
                    "volume": 10,
                    "turnover": 90,
                    "pct_change": 0,
                },
                {
                    "trade_date": "2026-10-21",
                    "symbol": "BBB",
                    "name": "Beta",
                    "open": 5,
                    "high": 6,
                    "low": 4,
                    "close": 5,
                    "volume": 20,
                    "turnover": 100,
                    "pct_change": 0,
                },
            ]
        )
        refreshed = normalize_market_data(
            pd.DataFrame(
                [
                    {
                        "trade_date": "2026-10-22",
                        "symbol": "AAA",
                        "name": "Updated Name",
                        "open": 9,
                        "high": 11,
                        "low": 8,
                        "closingPrice": 10,
                        "sharevolume": 12,
                        "turnover": 120,
                        "percentageChange": 1,
                    },
                    {
                        "trade_date": "2026-10-23",
                        "symbol": "AAA",
                        "name": "Updated Name",
                        "open": 10,
                        "high": 12,
                        "low": 9,
                        "closingPrice": 11,
                        "sharevolume": 15,
                        "turnover": 165,
                        "percentageChange": 10,
                    },
                ]
            )
        )

        merged = merge_market_data(existing, refreshed)

        self.assertEqual(len(merged), 3)
        updated_row = merged.loc[
            (merged["trade_date"] == "2026-10-22") & (merged["symbol"] == "AAA")
        ].iloc[0]
        self.assertEqual(updated_row["name"], "Updated Name")
        self.assertEqual(updated_row["close"], 10)
        self.assertIn("BBB", merged["symbol"].tolist())
        self.assertEqual(merged["trade_date"].max(), "2026-10-23")


if __name__ == "__main__":
    unittest.main()
