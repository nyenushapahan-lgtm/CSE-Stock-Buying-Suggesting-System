from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout
import pandas as pd
from src.services.charts.charts import Charts
from src.services.main_window.MainData import MainData
from src.services import logger
from src.services.DB_Handler.ReadData import ReadOperation
import os   
import json


class SectorPerformance:
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
            #select combobox
            self.sectorComboBox = self.main_window_obj.sectorComboBox

            #select chart element
            self.timeSeriesChartWidget = self.main_window_obj.timeSeriesChartWidget

            #select the table widget
            self.sectorWiseDetailTable = self.main_window_obj.sectorWiseDetailTable
        
        except Exception as e:
            self.logMsg.error_message(message="Error Sector Performance : "+str(e))
            raise ("Error Sector Performance : "+str(e))
        

    def addGridChart(self):
        """Compare two companies stock price details"""
        try:
            # Get scroll area from designer
            scroll_area = self.main_window_obj.gridChartScrollArea
            
            # Configure scroll area
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scroll_area.setWidgetResizable(True)
            
            # Load data
            success, dMessage, dataset = self.mainData_obj.loadClosedPrices()
            if not success:
                self.logMsg.error_message(message=dMessage)
                return
            
            # Factorize dataset
            sampleData, companySymbols = dataset[0], dataset[1]
            
            # Get grid chart (this returns a QWidget)
            chartview = self.charts.showGridTimeSeriesCharts(
                trendDataList=sampleData[:4],
                stockNames=companySymbols[:4]
            )
            
            # Set chart as scroll area's content
            scroll_area.setWidget(chartview)
            
        except Exception as e:
            self.logMsg.error_message(message="Error loading chart: "+str(e))
    
    def addTimeSeriesChart(self):
        """Load and Control the Time Series Chart Tab"""
        #call the sector adding to the combo box
        self.__addSectorsToComboBoxWidget()
        
    #using cash file to store the sector names for the combo box
    def __gettingSectorNamesFromCash(self)->list:
        """Getting sector names from cash file"""
        file_path = './resources/cash/sector_dataset_cash.json'
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r') as f:
            cash_data = json.load(f)

        if cash_data["data"] is None:
            return []
        
        return cash_data["data"]

    def __addSectorsToComboBoxWidget(self):
        """Add sectors to the combo box only when they actually contain company data."""

        sectorNames = self.__gettingSectorNamesFromCash()

        filtered_sector_names = []
        for raw_name in sectorNames or []:
            sector_name = str(raw_name).strip() if raw_name is not None else ""
            if sector_name and sector_name not in filtered_sector_names:
                filtered_sector_names.append(sector_name)

        if not filtered_sector_names:
            self.logMsg.error_message(message="No valid sectors available to display")
            return

        self.sectorComboBox.clear()
        self.sectorComboBox.addItems(filtered_sector_names)
        self.sectorComboBox.setCurrentIndex(0)
        self.sectorComboBox.currentIndexChanged.connect(self.__sectorComboBoxChanged)

        self.__sectorComboBoxChanged(index=0)
    
    def __sectorComboBoxChanged(self,index):
        #this is default value for the combo box when the application starts
        if index == 1:
            self.sectorComboBox.setCurrentIndex(1)

        #getting the current value of the combo box
        value = self.sectorComboBox.currentText()

        #check if the value
        if value:
            try:
                success,dMessage,dataset = self.read_db.gettingSectorWiseCompanyClosePrice(
                    sectorName=value
                    )

                if not success:
                    return success,dMessage,None

                companySymbols = list(dataset.keys())
                close_prices = list(dataset.values())

                chartview = self.charts.showTimeSeriesChart(
                    trendDataList=close_prices,
                    stockName=companySymbols,
                    title=f"Performance of {value}"
                    )
                
                if chartview:
                    layout = self.timeSeriesChartWidget.layout()

                    if layout is None:
                        layout = QVBoxLayout(self.timeSeriesChartWidget)
                        layout.setContentsMargins(0, 0, 0, 0)
                        self.timeSeriesChartWidget.setLayout(layout)
                    
                    else:
                        while layout.count():
                            child = layout.takeAt(0)
                        
                            if child.widget():
                                child.widget().deleteLater()
                    
                    layout.addWidget(chartview)

                #show sector table
                self.showSectorTable(
                    success=success,
                    dMessage=dMessage,
                    dataset=dataset
                    )
                
            except Exception as e:
                self.logMsg.error_message(message=f"Chart Render Error in Combobox: {str(e)}")
            
    def showSectorTable(self,success,dMessage,dataset):
        """Add Dates Columns to the sector table and Add rows also to the table"""
        #getting sectorwise company details
        if not success:
            self.logMsg.debug_message(message=dMessage)
            return
        
        #set the debug message
        self.logMsg.info_message(message=dMessage)

        if not dataset:
            self.logMsg.debug_message(message="No data available for this sector")
            self.sectorWiseDetailTable.clearContents()
            self.sectorWiseDetailTable.setRowCount(0)
            self.sectorWiseDetailTable.setColumnCount(0)
            return
        
        company_symbols = list(dataset.keys())
        if not company_symbols:
            self.logMsg.error_message(message="No price data available")
            self.sectorWiseDetailTable.clearContents()
            return

        records = []
        for symbol in company_symbols:
            prices = dataset.get(symbol, []) or []
            if prices:
                for item in prices:
                    records.append({"company_symbol": symbol, "date": item.get("date"), "close_price": item.get("close_price")})

        if not records:
            self.logMsg.error_message(message="No usable price records available")
            self.sectorWiseDetailTable.clearContents()
            return

        price_frame = pd.DataFrame(records)
        if price_frame.empty:
            self.logMsg.error_message(message="No usable price records available")
            self.sectorWiseDetailTable.clearContents()
            return

        pivot_frame = price_frame.pivot_table(
            index="company_symbol",
            columns="date",
            values="close_price",
            aggfunc="last"
        )

        self.sectorWiseDetailTable.clearContents()
        self.sectorWiseDetailTable.setColumnCount(len(pivot_frame.columns) + 1)
        self.sectorWiseDetailTable.setRowCount(len(pivot_frame.index))
        self.sectorWiseDetailTable.setHorizontalHeaderLabels(["Company Symbol"] + [str(col) for col in pivot_frame.columns])

        try:
            for row_index, company_symbol in enumerate(pivot_frame.index):
                self.sectorWiseDetailTable.setItem(row_index, 0, QTableWidgetItem(str(company_symbol)))
                for col_index, date_value in enumerate(pivot_frame.columns, start=1):
                    value = pivot_frame.loc[company_symbol, date_value]
                    self.sectorWiseDetailTable.setItem(row_index, col_index, QTableWidgetItem(str(value)))

            self.sectorWiseDetailTable.resizeColumnsToContents()
        except Exception as e:
            self.logMsg.error_message(message="Error Sector Performance |showSectorTable() - Populating table : " + str(e))