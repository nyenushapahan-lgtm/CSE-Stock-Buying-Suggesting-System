import unittest
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
from PySide6.QtWidgets import QApplication, QTableWidget, QWidget

from src.windows.main_window.MainWindow import MainWindow
from src.windows.main_window.SectorPeformance import SectorPerformance
from src.services.charts.charts import Charts


class SectorPerformanceTests(unittest.TestCase):
    def test_cached_sector_names_are_cleaned_before_combo_population(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sector_names_path = Path(temp_dir) / "sectors.json"
            sector_names_path.write_text(
                json.dumps({"data": ["Tech", "", "Health"]}),
                encoding="utf-8",
            )
            sector_window = SectorPerformance.__new__(SectorPerformance)
            sector_window.logMsg = Mock()
            sector_window.read_db = Mock()
            sector_window.mainData_obj = Mock()
            sector_window.SECTOR_NAME_CASH_FILE = str(sector_names_path)
            sector_window.mainData_obj.readIndustryGroupName.return_value = (True, "ok", ["Tech", "", "Health"])
            sector_window.read_db.gettingSectorWiseCompanyClosePrice.side_effect = [
                (True, "ok", {"AAPL": []}),
                (True, "ok", {}),
            ]
            sector_window.sectorComboBox = SimpleNamespace(
                clear=Mock(),
                addItems=Mock(),
                setCurrentIndex=Mock(),
                currentIndexChanged=SimpleNamespace(connect=Mock(), disconnect=Mock()),
                currentText=lambda: "Tech",
            )
            sector_window.timeSeriesChartWidget = SimpleNamespace(layout=lambda: None)
            sector_window.sectorWiseDetailTable = Mock()
            sector_window.charts = Mock()
            sector_window.charts.showTimeSeriesChart.return_value = None
            sector_window.showSectorTable = Mock()

            sector_window._SectorPerformance__addSectorsToComboBoxWidget()

        sector_window.sectorComboBox.addItems.assert_called_once_with(["Tech", "Health"])
        sector_window.sectorComboBox.setCurrentIndex.assert_called_once_with(0)

    def test_load_sector_wise_investment_data_keeps_zero_values(self):
        app = QApplication.instance() or QApplication([])
        main_window = MainWindow.__new__(MainWindow)
        main_window.sectorPerformChartWidget = QWidget()
        main_window.chart_obj = Mock()
        main_window.chart_obj.showSectorBarChart.return_value = QWidget()
        main_window.mainData_obj = Mock()
        main_window.mainData_obj.getSectorWiseInvestmentsDetails.return_value = (True, "ok", {"Tech": 0})
        main_window.logMsg = Mock()
        main_window.lblBarChart = None

        main_window.loadSectorWiseInvestmentData()

        main_window.chart_obj.showSectorBarChart.assert_called_once_with(
            sectorData=[{"sector_name": "Tech", "investment_value": 0}]
        )
        app.quit()

    def test_sector_time_series_uses_bundled_data_then_cash_cache(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            prices_path = temp_path / "prices.csv"
            mapping_path = temp_path / "mapping.csv"
            cash_path = temp_path / "sector_history.json"
            pd.DataFrame(
                [
                    {"trade_date": "2026-10-22", "symbol": "AAA", "close": 10},
                    {"trade_date": "2026-10-23", "symbol": "AAA", "close": 11},
                    {"trade_date": "2026-10-22", "symbol": "BBB", "close": 20},
                    {"trade_date": "2026-10-23", "symbol": "BBB", "close": 22},
                ]
            ).to_csv(prices_path, index=False)
            pd.DataFrame(
                [
                    {"symbol": "AAA", "sector_name": "Banks"},
                    {"symbol": "BBB", "sector_name": "Utilities"},
                    {"symbol": "NO_DATA", "sector_name": "Inactive"},
                ]
            ).to_csv(mapping_path, index=False)

            sector_window = SectorPerformance.__new__(SectorPerformance)
            sector_window.logMsg = Mock()
            sector_window.read_db = Mock()
            sector_window.read_db.gettingSectorWiseCompanyClosePrice.return_value = (
                False,
                "sectorized_table is unavailable",
                {},
            )
            sector_window.sectorComboBox = SimpleNamespace(currentText=lambda: "Banks")
            sector_window.timeSeriesChartWidget = QWidget()
            sector_window.sectorWiseDetailTable = QTableWidget()
            sector_window.charts = Charts()
            sector_window.SECTOR_HISTORY_CASH_FILE = str(cash_path)
            sector_window.SECTOR_NAME_CASH_FILE = str(temp_path / "missing_sectors.json")
            sector_window.SECTOR_HISTORY_CASH_DURATION = timedelta(days=1)
            sector_window.SECTOR_VOLUME_DATA_FILE = str(prices_path)
            sector_window.SECTOR_MAPPING_DATA_FILE = str(mapping_path)

            self.assertEqual(
                sector_window._load_sector_names_from_mapping(),
                ["Banks", "Utilities"],
            )
            sector_window._SectorPerformance__sectorComboBoxChanged(index=0)

            layout = sector_window.timeSeriesChartWidget.layout()
            chart_view = layout.itemAt(0).widget()
            self.assertEqual(len(chart_view.chart().series()), 1)
            self.assertEqual(chart_view.chart().series()[0].count(), 2)
            self.assertEqual(chart_view.chart().axes()[0].format(), "dd MMM")
            self.assertEqual(sector_window.sectorWiseDetailTable.rowCount(), 1)
            with cash_path.open(encoding="utf-8") as cache_file:
                self.assertIn("Banks", json.load(cache_file)["data"])

            sector_window.SECTOR_VOLUME_DATA_FILE = str(temp_path / "missing.csv")
            sector_window._SectorPerformance__sectorComboBoxChanged(index=0)

            layout = sector_window.timeSeriesChartWidget.layout()
            chart_view = layout.itemAt(0).widget()
            self.assertEqual(len(chart_view.chart().series()), 1)
            self.assertEqual(chart_view.chart().series()[0].count(), 2)
        app.quit()


if __name__ == "__main__":
    unittest.main()
