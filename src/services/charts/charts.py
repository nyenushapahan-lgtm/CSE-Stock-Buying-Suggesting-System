# Cleaned imports

from PySide6.QtCore import QDate, QFile, QTime, Qt, QMargins, QDateTime
from PySide6.QtGui import QCursor, QIcon, QPainter, QBrush, QColor

from PySide6.QtCharts import (QCandlestickSeries, QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, 
                              QValueAxis, QLineSeries, QDateTimeAxis,QCandlestickSeries,QCandlestickSet)

from PySide6.QtWidgets import (QGridLayout, QSizePolicy, QSplitter, QToolTip, QWidget, QApplication, QMainWindow, QTableWidgetItem, 
                               QMessageBox, QButtonGroup, QFrame, QVBoxLayout, QHBoxLayout, 
                               QLabel, QProgressBar, QPushButton, QHeaderView, QTableWidget,QSizePolicy)
import pandas as pd
from src.services.logger import Logging

import mplfinance as mpf
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class Charts:
    """
    Use Chart Widgets
    """
    def __init__(self):
        self.logMsg = Logging()
        
    def showTimeSeriesChart(self, trendDataList, stockName,title="Best Performing Companies History !"):
        """
            Show Time Series Data Points.\n <b>This helps to compare price trends directly.</b>
        """

        # ✅ Add this at start
        if isinstance(stockName, str):
            stockName = [stockName]
            trendDataList = [trendDataList]

        if len(trendDataList) != len(stockName):
            raise ValueError("Data and names must match in length")
        

        try:
            chart = QChart()
            chart.setTitle(title)
            chart.setTheme(QChart.ChartTheme.ChartThemeBlueCerulean)

            #add colors
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
            
            all_prices = []
            min_price, max_price = float('inf'), float('-inf')
            min_timestamp, max_timestamp = None, None

            for idx, (trendData, name) in enumerate(zip(trendDataList, stockName)):
                series = QLineSeries()
                series.setName(name)

                pen = series.pen()
                pen.setColor(QColor(colors[idx % len(colors)]))
                pen.setWidth(2)
                series.setPen(pen)

                if not trendData:
                    chart.addSeries(series)
                    continue

                frame = pd.DataFrame(trendData)
                if 'date' in frame.columns and 'close_price' in frame.columns:
                    frame['date'] = pd.to_datetime(frame['date'], errors='coerce')
                    frame = frame.dropna(subset=['date', 'close_price'])

                    if not frame.empty:
                        frame['close_price'] = pd.to_numeric(frame['close_price'], errors='coerce')
                        frame = frame.dropna(subset=['close_price'])
                        frame = frame.sort_values('date').drop_duplicates(
                            subset=['date'],
                            keep='last',
                        )

                if frame.empty:
                    chart.addSeries(series)
                    continue

                timestamps = []
                prices = []

                for _, row in frame.iterrows():
                    # Method 1: Using QDate + QDateTime (Recommended)
                    qdate = QDate(row['date'].year, row['date'].month, row['date'].day)
                    dt = QDateTime(qdate, QTime(0, 0, 0))
                    msecs = dt.toMSecsSinceEpoch()
                    
                    price = float(row['close_price'])
                    timestamps.append(msecs)
                    prices.append(price)
                    series.append(msecs, price)
                    min_timestamp = msecs if min_timestamp is None else min(min_timestamp, msecs)
                    max_timestamp = msecs if max_timestamp is None else max(max_timestamp, msecs)

                series.setPointLabelsColor(QColor(colors[idx % len(colors)]))
                
                series.hovered.connect(lambda point, state, s_name=name: 
                                    self.handle_line_hover(s_name, point, state))

                all_prices.extend(prices)
                min_price = min(min_price, float(min(prices)))
                max_price = max(max_price, float(max(prices)))

                chart.addSeries(series)

            # Setup axes
            axis_x = QDateTimeAxis()
            if min_timestamp is not None and max_timestamp is not None:
                axis_x.setFormat(
                    "dd MMM"
                    if max_timestamp - min_timestamp <= 90 * 24 * 60 * 60 * 1000
                    else "MMM yyyy"
                )
                if min_timestamp == max_timestamp:
                    min_timestamp -= 12 * 60 * 60 * 1000
                    max_timestamp += 12 * 60 * 60 * 1000
                axis_x.setRange(
                    QDateTime.fromMSecsSinceEpoch(min_timestamp),
                    QDateTime.fromMSecsSinceEpoch(max_timestamp),
                )
            else:
                axis_x.setFormat("dd MMM")
            axis_x.setTitleText("Trading date")
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)

            axis_y = QValueAxis()
            padding = (max_price - min_price) * 0.05 if max_price != min_price else 10
            axis_y.setRange(max(0, min_price - padding), max_price + padding)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

            for series in chart.series():
                series.attachAxis(axis_x)
                series.attachAxis(axis_y)

            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            chart_view.setMinimumHeight(250)
            chart_view.setMinimumWidth(400)
            chart_view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
            return chart_view



        except Exception as e:
            self.logMsg.error_message(
                message=f"Error generating time series chart: {str(e)}"
                )
            

    def showGridTimeSeriesCharts(self, trendDataList, stockNames):
        """
        Creates a grid of small charts (2 columns, N rows)
        """
        try:
            # Determine grid size
            n_stocks = len(trendDataList)
            cols = 2
            rows = (n_stocks + cols - 1) // cols
            
            # Create container widget
            container = QWidget()
            layout = QGridLayout(container)
            
            for idx, (trendData, name) in enumerate(zip(trendDataList, stockNames)):
                # Create individual chart (reuse your original method)
                chart_view = self.showTimeSeriesChart(trendData, name)
                
                # Make it smaller
                chart_view.setMinimumHeight(250)
                chart_view.setMinimumWidth(400)
                
                # Add to grid
                row = idx // cols
                col = idx % cols
                layout.addWidget(chart_view, row, col)
            
            return container
            
        except Exception as e:
            self.logMsg.error_message(message=f"Error: {str(e)}")
    

    def showNormalizedComparisonChart(self, trendDataList, stockNames):
        """
        Shows relative performance (percentage change from first data point)
        """
        try:
            chart = QChart()
            chart.setTitle("Relative Performance Comparison (Base = 100)")
            chart.setTheme(QChart.ChartTheme.ChartThemeDark)
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            
            for idx, (trendData, name) in enumerate(zip(trendDataList, stockNames)):
                series = QLineSeries()
                series.setName(name)

                if not trendData:
                    chart.addSeries(series)
                    continue

                frame = pd.DataFrame(trendData)
                if 'date' in frame.columns and 'close_price' in frame.columns:
                    frame['date'] = pd.to_datetime(frame['date'], errors='coerce')
                    frame = frame.dropna(subset=['date', 'close_price'])
                    frame['close_price'] = pd.to_numeric(frame['close_price'], errors='coerce')
                    frame = frame.dropna(subset=['close_price'])

                if frame.empty:
                    chart.addSeries(series)
                    continue

                first_price = float(frame['close_price'].iloc[0]) if not frame.empty else None
                if first_price is None:
                    chart.addSeries(series)
                    continue

                timestamps = []
                for value in frame['date']:
                    qdate = QDate(value.year, value.month, value.day)
                    dt = QDateTime(qdate, QTime(0, 0, 0))
                    timestamps.append(dt.toMSecsSinceEpoch())
                normalized_prices = (frame['close_price'].to_numpy(dtype=float) / first_price) * 100

                for msecs, normalized_price in zip(timestamps.tolist(), normalized_prices.tolist()):
                    series.append(msecs, normalized_price)

                pen = series.pen()
                pen.setColor(QColor(colors[idx % len(colors)]))
                pen.setWidth(2)
                series.setPen(pen)
                chart.addSeries(series)
            
            # Setup axes (Y-axis shows percentage)
            axis_x = QDateTimeAxis()
            axis_x.setFormat("yyyy-MM-dd")
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            
            axis_y = QValueAxis()
            axis_y.setTitleText("Performance (%)")
            axis_y.setRange(80, 120)  # Or calculate dynamically
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            
            for series in chart.series():
                series.attachAxis(axis_x)
                series.attachAxis(axis_y)
            
            chart.legend().setVisible(True)
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            return chart_view
            
        except Exception as e:
            self.logMsg.error_message(message=f"Error: {str(e)}")

    def showStockDashboard(self, trendDataList, stockNames):
        """
        Creates a dashboard with summary stats and mini charts
        """
        # Calculate key metrics for each stock
        metrics = []
        for trendData in trendDataList:
            prices = [float(item['close_price']) for item in trendData if item.get('close_price')]
            if prices:
                metrics.append({
                    'start': prices[0],
                    'end': prices[-1],
                    'change': ((prices[-1] - prices[0]) / prices[0]) * 100,
                    'high': max(prices),
                    'low': min(prices)
                })
        
        # Create a table/UI showing metrics + mini chart for each
        # (Implementation depends on your UI framework)

    def showSectorBarChart(self, sectorData):
        try:
            chart = QChart()
            chart.setTitle("Sector Wise Investment")
            chart.setTheme(QChart.ChartTheme.ChartThemeBlueCerulean)
            chart.setMargins(QMargins(-5, 0, 0, 0))
            
            sectorNames, investmentValues = [], []
            for item in (sectorData or []):
                sectorNames.append(str(item.get("sector_name", "")))
                investmentValues.append(float(item.get("investment_value", 0)))

            if not investmentValues: return None

            max_raw = max(investmentValues)
            divisor = 1_000_000_000 if max_raw >= 1_000_000_000 else 1_000_000 if max_raw >= 1_000_000 else 1
            
            bar_set = QBarSet("Investment")
            for val in investmentValues: bar_set.append(val / divisor)

            # Connect hover signal to show detailed tooltip on bar hover
            bar_set.hovered.connect(
                lambda status, index, names=sectorNames, vals=investmentValues: self.handle_bar_hover(status, index, names, vals)
            )

            series = QBarSeries()
            series.append(bar_set)
            #series.setLabelsVisible(True)
            chart.addSeries(series)

            axis_x = QBarCategoryAxis()
            axis_x.append(sectorNames)
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setRange(0, (max_raw / divisor) * 1.2)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            chart_view.setMinimumHeight(200)
            return chart_view
        except Exception as e:
            self.logMsg.error_message(message=f"Error: {str(e)}")

    def createCandlestickChart_01(self,dataframe,stockName):
        """
            Generates a Candlestick chart with volume using mplfinance.
            Returns a FigureCanvas widget that can be embedded into PySide6 layouts.
        """
        try:
            #define the visual style for the chart
            mc = mpf.make_marketcolors(up='g', down='r', edge='inherit', wick='inherit', volume='in')
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--',y_on_right=True)

            #Generate the matplotlib figure
            #returnfig=True is strictly required so we can grab the 'fig' object
            fig, axes = mpf.plot(
                dataframe,
                type='candle',
                volume=True,
                mav=(7,20),
                style=s,
                returnfig=True,
                figsize=(8,5),
                title=f"{stockName} -  Analysis (5D)",
                tight_layout=True
            )

            #wrap the figure in qt canvas
            chart_canvas = FigureCanvas(fig)

            #apply the same sizing policies as your QChartView
            chart_canvas.setMinimumHeight(300)
            chart_canvas.setMinimumWidth(400)
            chart_canvas.setSizePolicy(
                QSizePolicy.Policy.Expanding,  # Horizontal
                QSizePolicy.Policy.Expanding   # Vertical
            )

            #return the canvas to be embedded in your PySide6 layout
            return chart_canvas
        
        except Exception as e:
            self.logMsg.error_message(message=f"Error generating candlestick chart: {str(e)}")
            return None
        
    def _apply_chart_theme(self, chart, title_color="#F5F7FA", axis_color="#D9E2EC"):
        chart.setTheme(QChart.ChartTheme.ChartThemeBlueCerulean)
        chart.setBackgroundBrush(QBrush(QColor("#111827")))
        chart.setPlotAreaBackgroundBrush(QBrush(QColor("#1F2937")))
        chart.setTitleBrush(QBrush(QColor(title_color)))

        for axis in chart.axes():
            if hasattr(axis, "setLabelsBrush"):
                axis.setLabelsBrush(QBrush(QColor(axis_color)))
            if hasattr(axis, "setTitleBrush"):
                axis.setTitleBrush(QBrush(QColor(axis_color)))
            if hasattr(axis, "setGridLineColor"):
                axis.setGridLineColor(QColor("#374151"))

    def _to_msecs(self, value):
        if pd.isna(value):
            return None
        if hasattr(value, "to_pydatetime"):
            value = value.to_pydatetime()
        if hasattr(value, "timestamp"):
            return int(value.timestamp() * 8000)
        return int(value)

    def createCandlestickChart_02(self,dataframe,stockName):
        """
        Generates an interactive Candlestick chart using native PySide6 QtCharts.
        Requires no external web engines and runs purely in C++/Qt.
        """
        try:
            # Check if dataframe is None or empty
            if dataframe is None or dataframe.empty:
                if hasattr(self, 'logMsg'):
                    self.logMsg.error_message(message=f"No trading data found for {stockName}")
                return None
            
            # 1. Initialize the Chart
            chart = QChart()
            chart.setTitle(f"{stockName} - Price Action Analysis")
            chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            self._apply_chart_theme(chart)

            if 'Close' in dataframe.columns:
                dataframe['SMA_7'] = dataframe['Close'].rolling(window=5).mean()
            
            # 2. Setup the Candlestick Series
            series = QCandlestickSeries()
            series.setName(stockName)
            series.setIncreasingColor(QColor("#26A69A")) # Modern Green
            series.setDecreasingColor(QColor("#EF5350")) # Modern Red
            
            # We need these to scale the Y-axis properly later
            min_price = float('inf')
            max_price = float('-inf')



            # 3. Populate the series with data from the Pandas DataFrame
            for timestamp_index, row in dataframe.iterrows():
                o = float(row['Open'])
                h = float(row['High'])
                l = float(row['Low'])
                c = float(row['Close'])
                
                # Qt expects the timestamp in milliseconds since Epoch
                msecs = self._to_msecs(timestamp_index)

                # Create a single candlestick set and add it
                candlestickSet = QCandlestickSet(o, h, l, c, msecs)

                #connect the hover signal to show tooltips
                candlestickSet.hovered.connect(lambda set: self.handle_candle_hover(
                    stockName=stockName,
                    set=tuple((o, h, l, c)),
                    status=True
                    ))
                series.append(candlestickSet)

                # Track min/max for axis scaling
                min_price = min(min_price, l)
                max_price = max(max_price, h)

            chart.addSeries(series)

            # 4. Setup X Axis (Time)
            axis_x = QDateTimeAxis()
            axis_x.setFormat("MMM-dd") # e.g., Mar-01
            axis_x.setTitleText("Date")
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)

            # 5. Setup Y Axis (Price)
            axis_y = QValueAxis()
            axis_y.setTitleText("Price (LKR)")
            
            # Add a 5% padding to the top and bottom of the chart so candles don't touch the edges
            padding = (max_price - min_price) * 0.05 if max_price != min_price else 10
            axis_y.setRange(max(0, min_price - padding), max_price + padding)
            
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)

            #--SMA Visulas integration
            sma_series = QLineSeries()
            sma_series.setName("SMA 7")
            sma_series.setColor(QColor("#45B7D1"))  # Modern Blue

            for date, row in dataframe.iterrows():
                if 'SMA_7' in row and pd.notna(row['SMA_7']):
                    msecs = self._to_msecs(date)
                    if msecs is not None:
                        sma_series.append(msecs, float(row['SMA_7']))
            
            chart.addSeries(sma_series)
            sma_series.attachAxis(axis_x)
            sma_series.attachAxis(axis_y)

            # 6. Final Polish
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            chart_view.setMinimumHeight(350)
            chart_view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )

            return chart_view

        except Exception as e:
            if hasattr(self, 'logMsg'):
                self.logMsg.error_message(message=f"Error generating native Qt candlestick chart: {str(e)}")
            else:
                print(f"Error generating native Qt candlestick chart: {str(e)}")
            return None
    
    def createVolumeChart(self,dataframe):
        try:
            volume_chart = QChart()
            self._apply_chart_theme(volume_chart)
            volume_series = QBarSeries()
            volume_set = QBarSet("Volume")

            #style for volume bars
            volume_set.setBrush(QBrush(QColor("#789098"))) # Modern Gray

            vol_col = 'Volume' if 'Volume' in dataframe.columns else ('volume' if 'volume' in dataframe.columns else None)
            if vol_col:
                for vol in dataframe[vol_col]:
                    volume_set.append(float(vol or 0))

            volume_series.append(volume_set)
            volume_chart.addSeries(volume_series)

            #Hide x axis labels for volume chart
            axis_x = QDateTimeAxis()
            axis_x.setFormat("MMM-dd")
            axis_x.setVisible(False)
            volume_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            volume_series.attachAxis(axis_x)

            #Setup Y axis for volume
            axis_y = QValueAxis()
            axis_y.setTitleText("Volume")
            volume_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            volume_series.attachAxis(axis_y)

            return volume_chart,axis_x

        except Exception as e:
            self.logMsg.error_message(message=f"Error generating volume chart: {str(e)}")
            return None, None

    def addCandleAndVolumeChart(self,dataframe,stockName):
        """Add candlestick and volume charts to the main chart view."""
        
        try:
            #Generate Price chart
            price_chart_view = self.createCandlestickChart_02(dataframe, stockName)
            
            # Check if price_chart_view is None (when there's an error or no data)
            if price_chart_view is None:
                self.logMsg.error_message(message=f"No trading data found for {stockName}")
                return None
            
            price_chart = price_chart_view.chart()

            #Generate Volume chart
            volume_chart, vol_axis_x = self.createVolumeChart(dataframe)
            volume_chart_view = QChartView(volume_chart)

            price_axis_x = price_chart.axes(Qt.Orientation.Horizontal)[0]
            price_axis_x.rangeChanged.connect(vol_axis_x.setRange)

            price_chart_view.setMinimumHeight(260)
            price_chart_view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            volume_chart_view.setMinimumHeight(120)
            volume_chart_view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.MinimumExpanding,
            )

            #Use QSplitter to stack the charts vertically
            splitter = QSplitter(Qt.Orientation.Vertical)
            splitter.setContentsMargins(4, 4, 4, 6)
            splitter.setHandleWidth(8)
            splitter.setChildrenCollapsible(False)
            splitter.addWidget(price_chart_view)
            splitter.addWidget(volume_chart_view)
            splitter.setSizes([320, 120])
            splitter.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            return splitter

        except Exception as e:
            self.logMsg.error_message(message=f"Error adding candlestick and volume charts: {str(e)}")
            return None
        
    def handle_candle_hover(self, stockName, status, set):
        """
        status: boolean, True if mouse entered the candle, False if left
        set: the specific QCandlestickSet being hovered
        """
        try:
            if status:
                #Create a tooltip with the OHLC values
                tooltip_text = (
                    f"<b>{stockName}</b><br/>"
                    f"Open: {set[0]:.2f}<br/>"
                    f"High: {set[1]:.2f}<br/>"
                    f"Low: {set[2]:.2f}<br/>"
                    f"Close: {set[3]:.2f}"
                )

                QToolTip.showText(QCursor.pos(), tooltip_text)
            
            else:
                QToolTip.hideText()
            
        except Exception as e:
            self.logMsg.error_message(message=f"Error in handle_candle_hover: {str(e)}")

    def handle_line_hover(self, stockName, point, state):
        """
        Show tooltip with date and price value when hovering over a line chart data point
        """
        try:
            if state:
                dt = QDateTime.fromMSecsSinceEpoch(int(point.x()))
                date_str = dt.toString("yyyy-MM-dd")
                tooltip_text = (
                    f"<b>{stockName}</b><br/>"
                    f"Date: {date_str}<br/>"
                    f"Price: {point.y():.2f} LKR"
                )
                QToolTip.showText(QCursor.pos(), tooltip_text)
            else:
                QToolTip.hideText()
        except Exception as e:
            self.logMsg.error_message(message=f"Error in handle_line_hover: {str(e)}")

    def handle_bar_hover(self, status, index, sectorNames, investmentValues):
        """
        Show tooltip with sector name and investment value when hovering over a bar chart item
        """
        try:
            if status and 0 <= index < len(sectorNames):
                sector_name = sectorNames[index]
                val = investmentValues[index]
                tooltip_text = (
                    f"<b>Sector: {sector_name}</b><br/>"
                    f"Investment Value: {val:,.2f}"
                )
                QToolTip.showText(QCursor.pos(), tooltip_text)
            else:
                QToolTip.hideText()
        except Exception as e:
            self.logMsg.error_message(message=f"Error in handle_bar_hover: {str(e)}")
