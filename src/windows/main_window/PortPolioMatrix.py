from src.services import logger
from src.services.charts.charts import Charts
from src.services.main_window.MainData import MainData
from src.services.DB_Handler.ReadData import ReadOperation
from PySide6.QtWidgets import QVBoxLayout

from PySide6.QtCharts import (QChart, QChartView, QCandlestickSeries, 
                              QCandlestickSet, QDateTimeAxis, QValueAxis)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QSizePolicy

import pandas as pd


class PortPolioMatrix:
    def __init__(self,main_window_obj):
        #creating main window object
        self.main_window_obj = main_window_obj

        #creating main data object
        self.mainData_obj = MainData()

        #creating chart object
        self.charts = Charts()

        #creating log messages
        self.logMsg = logger.Logging()
        
        #creating object for read operation
        self.read_db = ReadOperation()

        try:
            #selecting the chart widget from main window
            self.ppMatrixChartWidget = self.main_window_obj.ppMatrixChartWidget

            #best performing companies combo box
            self.bestCompaniesComboBox = self.main_window_obj.bestCompaniesComboBox

        except Exception as e:
            self.logMsg.error_message("Error in selecting the chart widget from main window: " + str(e))
            self.ppMatrixChartWidget = None
            self.bestCompaniesComboBox = None

        #setting best companies for the combo box
        self.__settingBestCompanies()

        if getattr(self, "bestCompaniesComboBox", None) is not None:
            try:
                self.bestCompaniesComboBox.currentIndexChanged.connect(self.__gettingCompanyDetails)
            except Exception as e:
                self.logMsg.error_message(message="Error connecting combo box selection: " + str(e))

            self._show_default_company_chart()

    def addCandleChart(self, symbol='HNBX.0000'):
        """<h3>Compare One Company stock price </h3>
        \n<p> details Using Matplotlib Candlestick Chart.
        This function is used to add a candlestick chart to the Portfolio Matrix section 
        of the main window.</p>"""

        #passing test dataset
        test_df = self.load_company_dataset(symbol=symbol)

        chart_widget = self.charts.addCandleAndVolumeChart(test_df, symbol)

        if chart_widget is not None:
            #creating layout for the chart widget
            layout = self.ppMatrixChartWidget.layout()

            #creating a new layout if the chart widget does not have any layout
            if layout is None:
                layout = QVBoxLayout(self.ppMatrixChartWidget)
                layout.setContentsMargins(1, 1, 1, 1)
                self.ppMatrixChartWidget.setLayout(layout)

            else:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            
            # Add the Matplotlib canvas to the layout just like a normal Qt Widget
            #layout.addWidget(chart_canvas)
            layout.addWidget(chart_widget)

    
    def load_company_dataset(self,symbol=''):
        """
        Returns a hardcoded Pandas DataFrame formatted for mplfinance.
        Ready for immediate testing without external CSV files.
        """
        try:
            success, dMessage, dataset = self.read_db.gettingCompanyFullDetails(symbol=symbol)

            if not success:
                self.logMsg.error_message(message=dMessage)
                return None

            if not dataset:
                self.logMsg.error_message(message=f"No trading data found for {symbol}")
                return None

            company_dataset = []

            for item in dataset:
                if not item:
                    continue

                company_dataset.append({
                    "Date": item.get('trade_date').strftime("%Y-%m-%d") if item.get('trade_date') else None,
                    "Open": float(item.get('open_price', 0)),
                    "High": float(item.get('high', 0)),
                    "Low": float(item.get('low', 0)),
                    "Close": float(item.get('close_price', 0)),
                    "Volume": int(item.get('volume', 0))
                })

            if not company_dataset:
                self.logMsg.error_message(message=f"No valid trading data found for {symbol}")
                return None

        except Exception as e:
            self.logMsg.error_message(message="Error : get_test_dataframe() " + str(e))
            return None

        # 2. Convert to DataFrame
        df = pd.DataFrame(company_dataset)

        if 'Date' not in df.columns:
            self.logMsg.error_message(message=f"Missing Date column for {symbol}")
            return None

        # 3. Convert 'Date' column to Datetime objects and set as index
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        if df.empty:
            self.logMsg.error_message(message=f"No valid dates found for {symbol}")
            return None

        df.set_index('Date', inplace=True)

        #calculate the SMA (Simple Moving Average)
        df['SMA_7'] = df['Close'].rolling(window=5).mean()

        return df
    
    def _show_default_company_chart(self):
        """Show the candle chart for the first available company on startup."""
        if not getattr(self, "bestCompaniesComboBox", None):
            return

        try:
            success, dMessage, dataset = self.read_db.getting_top_gainers()
            if not success:
                self.logMsg.error_message(message=dMessage)
                return

            first_company = next((item for item in dataset if item.get('name')), None)
            if not first_company:
                return

            self.bestCompaniesComboBox.setCurrentText(first_company['name'])
            self.addCandleChart(symbol=first_company.get('symbol', ''))

        except Exception as e:
            self.logMsg.error_message(message="Error : show_default_company_chart():" + str(e))
            return

    def __settingBestCompanies(self):
        """Setting best companies for the combo box"""

        if not getattr(self, "bestCompaniesComboBox", None):
            return

        try:
            success, dMessage, dataset = self.read_db.getting_top_gainers()

            if not success:
                self.bestCompaniesComboBox.clear()
                self.bestCompaniesComboBox.addItems(["No Data"])
                self.logMsg.error_message(message=dMessage)
                return

            #send log message
            self.logMsg.error_message(message=dMessage)

            #formatting
            company_names = [item['name'] for item in dataset if item.get('name')]

            #setting the best companies to the combo box
            self.bestCompaniesComboBox.clear()
            self.bestCompaniesComboBox.addItems(company_names)

            #when changed the combo box value, call the function to update the chart
            #self.bestCompaniesComboBox.currentIndexChanged.connect(self.__gettingCompanyDetails)

        except Exception as e:
            self.logMsg.error_message(message="Error : settingBestCompanies():" + str(e))
            return

    def __gettingCompanyDetails(self):
        """Using Company Symbol Return Company Full Details from the database and update the chart"""
        if not getattr(self, "bestCompaniesComboBox", None):
            return

        company_name = self.bestCompaniesComboBox.currentText()

        if not company_name:
            self.logMsg.error_message(message="No company selected")
            return

        try:
            success, dMessage, dataset = self.read_db.getting_top_gainers()

            if not success:
                self.bestCompaniesComboBox.clear()
                self.bestCompaniesComboBox.addItems(["No Data"])
                self.logMsg.error_message(message=dMessage)
                return

            #send log message
            self.logMsg.error_message(message=dMessage)

            symbol = None

            for item in dataset:
                if item.get('name') == company_name:
                    symbol = item.get('symbol')
                    break

            if not symbol:
                self.logMsg.error_message(message="No symbol found for selected company")
                return

            #load dataset for the selected company and render the candle chart
            self.addCandleChart(symbol=symbol)

        except Exception as e:
            self.logMsg.error_message(message="Error : gettingCompanyDetails():" + str(e))
            return
    
