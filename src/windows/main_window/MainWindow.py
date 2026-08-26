import json
import os
import sys
from PySide6.QtWidgets import (QScrollArea, QSizePolicy, QWidget, QApplication, QMainWindow, QTableWidgetItem, 
                               QMessageBox, QButtonGroup, QFrame, QVBoxLayout, QHBoxLayout, 
                               QLabel, QProgressBar, QPushButton, QHeaderView, QTableWidget)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QMargins, QDateTime
from PySide6.QtGui import QIcon, QPainter, QBrush, QColor

from PySide6.QtCharts import (QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, 
                              QValueAxis, QLineSeries, QDateTimeAxis)

# --- Your Custom Imports ---
from src.services import logger
# from resources.icons import resources_rc  # Uncomment if needed
from src.windows.main_window.ImportDataWindow import ImportDataWindow
from src.services.main_window.MainData import MainData
from src.windows.main_window.CustomWidgets import CustomWidgets
from src.windows.main_window.CustomWidgets.AdvancedAnalysisCardWidget import AdvancedAnalysisCardWidget
from src.windows.main_window.CustomWidgets.SuggestionCardWidget import SuggestionCardWidget

from src.services.charts.charts import Charts
from src.windows.main_window.SectorPeformance import SectorPerformance
from src.windows.main_window.PortPolioMatrix import PortPolioMatrix

# ==========================================
# 3. MAIN WINDOW APPLICATION
# ==========================================
class MainWindow():
    """Responsible for Handling all the Main window Widgets and Fucntions."""
    def __init__(self):
        self.main_window = None

        try:
            self.logMsg = logger.Logging()
            self.loader = QUiLoader()

            ui_file_path = "./resources/ui_files/main_window.ui"
            ui_file = QFile(ui_file_path)

            if not ui_file.open(QFile.ReadOnly):
                QMessageBox.critical(None, "File Error", "Ui File Cannot be Opened!")
                self.logMsg.error_message(message="Ui file Cannot be Opened!")
                sys.exit(-1)

            self.main_window = self.loader.load(ui_file)
            ui_file.close()

            self.main_window.setWindowIcon(QIcon("./resources/icons/icon.png"))
            self.main_window.showMaximized()

            # --- SAFE WIDGET MAPPING ---
            try:
                self.btnDashboard = self.main_window.findChild(QPushButton, "btnDashboard")
                self.btnPortfolio = self.main_window.findChild(QPushButton, "btnPortfolio")
                self.btnSector = self.main_window.findChild(QPushButton, "btnSector")
                self.btnSetting = self.main_window.findChild(QPushButton, "btnSettings")
                self.btnTradeEngine = self.main_window.findChild(QPushButton, "btnTradeEngine")
                
                self.stackedWidget = self.main_window.stackedWidget
                
                # Chart & Table Widgets
                self.tableGainers = self.main_window.findChild(QTableWidget, "tableGainers")
                self.sectorPerformChartWidget = self.main_window.findChild(QWidget, "sectorPerformChartWidget")
                self.top3RecStTrendChartWidget = self.main_window.findChild(QWidget, "top3RecomandedStockTrendChartWidget")
                self.stockPurchaseRecWidget = self.main_window.findChild(QTableWidget, "stockPurchaseRecomandWidget")
                self.sectorWiseDetailTable = self.main_window.findChild(QTableWidget, "sectorWiseDetailTable")
                self.ppMatrixChartWidget = self.main_window.findChild(QWidget, "portpolioMatrixChartWidget")

                #Under the Sector Performance Phase
                self.timeSeriesChartWidget = self.main_window.findChild(QWidget, "timeSeriesChartWidget")
                self.gridChartScrollArea = self.main_window.findChild(QScrollArea,"gridChartScrollArea")

                #sector peformance 
                #Time Series Tab
                self.sectorComboBox = self.main_window.findChild(QWidget,"sectorComboBox")
                self.bestCompaniesComboBox = self.main_window.findChild(QWidget,"bestPerformCompanyComboBox")

                # Container Widgets for Cards
                self.analysisCardContainer = self.main_window.findChild(QWidget, "analysisCardContainer")
                self.advancedAnalysisContainer = self.main_window.findChild(QWidget, "advancedAnalysisContainer")
                
                # Labels
                self.trackedStocksLable = getattr(self.main_window, "trackedStocksLable", None)
                self.actionImport = getattr(self.main_window, "actionImport", None)
                self.actionReload = getattr(self.main_window, "actionReload", None)


            except Exception as e:
                self.logMsg.error_message(f"Widget Mapping Error: {str(e)}")
                QMessageBox.critical(None, "UI Error", "Could not map UI widgets. Check object names in Qt Designer.")
                sys.exit(-1)

            # --- SETUP LOGIC ---
            try:
                #dashboard right side buttons
                self.stackedWidget.setCurrentIndex(0)
                self.btnDashboard.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
                self.btnPortfolio.clicked.connect(lambda: (
                    self.stackedWidget.setCurrentIndex(1),
                    self.PP_obj.addCandleChart()
                    ))
                self.btnSector.clicked.connect(lambda: (
                    self.stackedWidget.setCurrentIndex(2),
                    self.SP_obj.addGridChart(),
                    self.SP_obj.addTimeSeriesChart()
                    ))
                #add other button connections if needed------------------------------------

                #ensure dashboard buttons are clickable and checkable
                self.logMsg.debug_message("Dashboard Buttons are initialized and connected successfully.")
                self.setup_menu_styling()
            
            except Exception as e:
                self.logMsg.error_message(f"Button Setup Error: {str(e)}")

            # Connect menu actions menu items to their respective functions
            if self.actionImport:
                self.actionImport.triggered.connect(self.importing_data)

            # Connect reload menu item to reload data
            if self.actionReload:
                self.actionReload.triggered.connect(self.run_startup_tasks)


            # --- DATA INITIALIZATION ---
            self.mainData_obj = MainData()
            
            #create class obj for charts
            self.chart_obj = Charts()

            #create class object for Sector Performance
            self.SP_obj = SectorPerformance(self)

            #create class object for Portfolio Matrix
            self.PP_obj = PortPolioMatrix(self)
            
            if self.trackedStocksLable:
                success, dMessage, averageSTCount = self.mainData_obj.average_tracked_st_count()
                self.trackedStocksLable.setText(str(f"{averageSTCount:.1f}") if success else "0")
            

            # --- SAFE STARTUP SEQUENCE ---
            self.run_startup_tasks()

        except Exception as e:
            error_text = f"An unexpected error occurred during init : {str(e)}"
            self.logMsg.error_message(message=error_text)
            QMessageBox.critical(None, "Critical Error", error_text)
            sys.exit(-1)

    def run_startup_tasks(self):
        """Executes all data loading methods safely"""
        try:
            self.showTop10Gainers()
            self.loadSectorWiseInvestmentData()
            self.loadTimeSeriesData()
            self.loadSuggestionsTable()
            self.loadAdvancedAnalysisCard("COMB.N0000")

            self.logMsg.info_message("Main window modules loaded successfully.")

        except Exception as e:
            self.logMsg.error_message(f"Startup execution error: {str(e)}")

    def setup_menu_styling(self):
        buttons = [self.btnDashboard, self.btnPortfolio, self.btnSector, self.btnSetting, self.btnTradeEngine]
        self.btn_group = QButtonGroup(self.main_window)
        for btn in buttons:
            if btn:
                btn.setCheckable(True)
                self.btn_group.addButton(btn)

    def importing_data(self):
        self.logMsg.info_message(message="User Clicked the Import menu Item")
        self.importing_data_window = ImportDataWindow()
        self.importing_data_window.show()

    # ---------------------------------------------------------
    # UI COMPONENT LOADERS
    # ---------------------------------------------------------

    def showTop10Gainers(self):
        """Display Top 10 Gainers of the System"""
        if not self.tableGainers: return
        success, dMessage, dataset = self.mainData_obj.findTop10Gainers()

        if not success:
            self.logMsg.error_message(message=dMessage)
            
        self.tableGainers.clearContents()
        self.tableGainers.setRowCount(0)

        # SAFE LOOP: Ensures it won't crash if dataset is None
        for raw_data in (dataset or []):
            current_row = self.tableGainers.rowCount()
            self.tableGainers.insertRow(current_row)
            column_values = list(raw_data.values())
            
            for colm_idx, value in enumerate(column_values):
                display_str = f"{value:.2f}" if isinstance(value, float) else str(value)
                item = QTableWidgetItem(display_str)
                self.tableGainers.setItem(current_row, colm_idx, item)

    def __addSectorsToCash(self, sectorNames):
        """Add the sector names to the cash file for use sector performance charting"""

        try:
            file_path = './resources/cash/sector_dataset_cash.json'

            if os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    #write the initial structure to the cash file
                    json.dump({"data":sectorNames},f)

        except Exception as e:
            self.logMsg.error_message(message="Error in adding sector names to cash file : "+str(e))

    def loadSectorWiseInvestmentData(self):
        if not self.sectorPerformChartWidget: return

        try:
            success,dMessage,dataset = self.mainData_obj.getSectorWiseInvestmentsDetails()

            if not success:
                return success,dMessage,None
            
            # format the dataset while preserving zero values so the chart can render them
            sampleData = []
            #list for sector names
            sectorNames = []

            for key, value in dataset.items():
                if value is None:
                    continue

                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    continue


                #avoid zero values if you want to skip them, but here we keep them for chart rendering
                if numeric_value > 0:
                    #add the sector data to the sampleData list for charting
                    sampleData.append({
                        "sector_name": key,
                        "investment_value": numeric_value
                    })

                    #adding the sector names to the list for cashing
                    sectorNames.append(key)

            #add the sector names to the cash file for use in sector performance charting
            self.__addSectorsToCash(sectorNames)

        except Exception as e:
            self.logMsg.error_message(message="Error in loading Sector Wise Data set : "+str(e))
        
        chartview = self.chart_obj.showSectorBarChart(sectorData=sampleData)
        if chartview:
            layout = self.sectorPerformChartWidget.layout()
            if layout is None:
                layout = QVBoxLayout(self.sectorPerformChartWidget)
                layout.setContentsMargins(0, 0, 0, 0)
                self.sectorPerformChartWidget.setLayout(layout)
            else:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

            layout.addWidget(chartview)

    def loadTimeSeriesData(self):
        """Load the time series Data"""
        if not self.top3RecStTrendChartWidget: return

        #Here is the place where time series data shows
        success,dMessage, dataset = self.mainData_obj.loadClosedPrices()

        if not success:
            return success,dMessage,None

        #factorize the dataset
        sampleData,companySymbols = dataset[0],dataset[1]

        chartview = self.chart_obj.showTimeSeriesChart(
            trendDataList=sampleData,
            stockName=companySymbols
            )

        if chartview:
            layout = self.top3RecStTrendChartWidget.layout()
            # SAFE LAYOUT CREATION
            if layout is None:
                layout = QVBoxLayout(self.top3RecStTrendChartWidget)
                layout.setContentsMargins(0, 0, 0, 0)
                self.top3RecStTrendChartWidget.setLayout(layout)
            
            else:
                while layout.count():
                    child = layout.takeAt(0)
                    
                    if child.widget():
                        child.widget().deleteLater()

            layout.addWidget(chartview)

    def loadSuggestionsTable(self):
        if not self.stockPurchaseRecWidget: return
        suggestions_data = [
            {"code": "COMB.N0000", "name": "Commercial Bank", "suggestion": "Buy"},
            {"code": "DIAL.N0000", "name": "Dialog Axiata", "suggestion": "Hold"},
            {"code": "JKH.N0000", "name": "John Keells Hld", "suggestion": "Sell"}
        ]

        table = self.stockPurchaseRecWidget 
        table.setRowCount(0)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Stock Code", "Company Name", "AI Suggestion", "Action"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)

        for row_idx, item in enumerate(suggestions_data or []):
            table.insertRow(row_idx)
            table.setItem(row_idx, 0, QTableWidgetItem(item["code"]))
            table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))

            badge_widget = QWidget()
            badge_layout = QHBoxLayout(badge_widget)
            badge_layout.setContentsMargins(5, 2, 5, 2)
            lbl_badge = QLabel(item["suggestion"].upper())
            lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if "Buy" in item["suggestion"]:
                bg, txt = "#1E4620", "#4CAF50"
            elif "Sell" in item["suggestion"]:
                bg, txt = "#4A1A1A", "#F44336"
            else:
                bg, txt = "#4A401A", "#FFC107"

            lbl_badge.setStyleSheet(f"background-color: {bg}; color: {txt}; border-radius: 12px; font-weight: bold; padding: 0px 15px;")
            badge_layout.addWidget(lbl_badge)
            table.setCellWidget(row_idx, 2, badge_widget)

            btn_action = QPushButton("View Analysis")
            btn_action.setStyleSheet("QPushButton { background-color: #2D63E2; color: white; border-radius: 5px; padding: 5px; } QPushButton:hover { background-color: #1A4BBD; }")
            btn_action.clicked.connect(lambda checked=False, code=item["code"]: self.showSuggestionDetails(code))
            table.setCellWidget(row_idx, 3, btn_action)

    # ---------------------------------------------------------
    # DYNAMIC CARD SPAWNERS
    # ---------------------------------------------------------

    def showSuggestionDetails(self, stock_code):
        if not self.analysisCardContainer: return
        card = SuggestionCardWidget(
            stock_name=f"{stock_code} Analysis", current_price=110.50, target_price=135.00,
            verdict="BUY", confidence=92, rsi="35 (Oversold)", macd="Bullish Crossover",
            news="Deep Seek Analysis: High positive sentiment."
        )

        layout = self.analysisCardContainer.layout()
        if layout is None:
            layout = QVBoxLayout(self.analysisCardContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            self.analysisCardContainer.setLayout(layout)
        else:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                
        layout.addWidget(card)

    def loadAdvancedAnalysisCard(self, stock_code):
        if not self.advancedAnalysisContainer: return
        
        card = AdvancedAnalysisCardWidget(
            stock_code=stock_code, stock_name="Commercial Bank PLC", current_price=110.50, target_price=135.00,
            signal="STRONG BUY", confidence=92, rsi="35.4", macd="Bullish", volume_trend="High Accumulation",
            ai_summary="Deep Seek AI detects highly positive sentiment based on recent policy changes."
        )

        layout = self.advancedAnalysisContainer.layout()
        if layout is None:
            layout = QVBoxLayout(self.advancedAnalysisContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            self.advancedAnalysisContainer.setLayout(layout)
        else:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                
        layout.addWidget(card)

    def show(self):
        self.main_window.show()
    
    def close(self):
        self.main_window.close()