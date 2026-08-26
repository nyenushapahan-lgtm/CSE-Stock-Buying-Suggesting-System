import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication, QWidget

from src.windows.main_window.MainWindow import MainWindow
from src.windows.main_window.SectorPeformance import SectorPerformance


class SectorPerformanceTests(unittest.TestCase):
    def test_only_sectors_with_company_data_are_added(self):
        sector_window = SectorPerformance.__new__(SectorPerformance)
        sector_window.logMsg = Mock()
        sector_window.read_db = Mock()
        sector_window.mainData_obj = Mock()
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

        sector_window.sectorComboBox.addItems.assert_called_once_with(["Tech"])
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

        main_window.loadSectorWiseInvestmentData()

        main_window.chart_obj.showSectorBarChart.assert_called_once_with(
            sectorData=[{"sector_name": "Tech", "investment_value": 0}]
        )
        app.quit()


if __name__ == "__main__":
    unittest.main()
