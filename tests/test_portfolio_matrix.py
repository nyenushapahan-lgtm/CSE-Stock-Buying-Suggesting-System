import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd

from src.services.charts.charts import Charts
from src.windows.main_window.PortPolioMatrix import PortPolioMatrix


class PortfolioMatrixTests(unittest.TestCase):
    def test_selection_renders_chart_for_selected_company(self):
        matrix = PortPolioMatrix.__new__(PortPolioMatrix)
        matrix.bestCompaniesComboBox = SimpleNamespace(currentText=lambda: "Alpha Corp")
        matrix.logMsg = Mock()
        matrix.read_db = Mock()
        matrix.read_db.getting_top_gainers.return_value = (
            True,
            "ok",
            [{"name": "Alpha Corp", "symbol": "ALPHA"}],
        )
        matrix.addCandleChart = Mock()
        matrix.load_company_dataset = Mock(return_value=["data"])

        matrix._PortPolioMatrix__gettingCompanyDetails()

        matrix.addCandleChart.assert_called_once_with(symbol="ALPHA")
        matrix.load_company_dataset.assert_not_called()

    def test_empty_company_data_returns_none(self):
        matrix = PortPolioMatrix.__new__(PortPolioMatrix)
        matrix.logMsg = Mock()
        matrix.read_db = Mock()
        matrix.read_db.gettingCompanyFullDetails.return_value = (True, "ok", [])

        result = matrix.load_company_dataset(symbol="ALPHA")

        self.assertIsNone(result)
        matrix.logMsg.error_message.assert_called_once_with(message="No trading data found for ALPHA")

    def test_chart_timestamp_conversion_uses_milliseconds(self):
        charts = Charts()
        value = pd.Timestamp("2024-01-02 00:00:00", tz="UTC")

        self.assertEqual(charts._to_msecs(value), int(value.timestamp() * 1000))


if __name__ == "__main__":
    unittest.main()
