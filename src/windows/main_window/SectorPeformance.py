from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout
import pandas as pd
from src.services.charts.charts import Charts
from src.services.main_window.MainData import MainData
from src.services import logger
from src.services.DB_Handler.ReadData import ReadOperation
import os   
import json
from datetime import datetime, timedelta


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
        self.SECTOR_HISTORY_CASH_FILE = './resources/cash/sector_wise_close_prices_cash.json'
        self.SECTOR_NAME_CASH_FILE = './resources/cash/sector_dataset_cash.json'
        self.SECTOR_HISTORY_CASH_DURATION = timedelta(days=1)
        self.SECTOR_VOLUME_DATA_FILE = self.mainData_obj.SECTOR_VOLUME_DATA_FILE
        self.SECTOR_MAPPING_DATA_FILE = self.mainData_obj.SECTOR_MAPPING_DATA_FILE

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
        file_path = self.SECTOR_NAME_CASH_FILE
        if not os.path.exists(file_path):
            return self._load_sector_names_from_mapping()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cash_data = json.load(f)
            sector_names = cash_data.get("data")
            if isinstance(sector_names, list) and sector_names:
                return sector_names
        except (OSError, ValueError, TypeError):
            self.logMsg.error_message(message="Unable to read sector names cache; using bundled sector mapping.")

        return self._load_sector_names_from_mapping()

    def _load_sector_names_from_mapping(self):
        try:
            mapping = pd.read_csv(self.SECTOR_MAPPING_DATA_FILE)
            prices = pd.read_csv(self.SECTOR_VOLUME_DATA_FILE)
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as error:
            self.logMsg.error_message(message=f"Unable to read bundled sector history sources: {error}")
            return []

        if not {"symbol", "sector_name"}.issubset(mapping.columns):
            self.logMsg.error_message(message="Bundled sector mapping is missing required columns.")
            return []
        close_column = "close_price" if "close_price" in prices.columns else "close"
        if not {"symbol", close_column}.issubset(prices.columns):
            self.logMsg.error_message(message="Bundled trading data is missing symbol or close-price columns.")
            return []

        valid_prices = prices.loc[:, ["symbol", close_column]].copy()
        valid_prices["symbol"] = valid_prices["symbol"].astype("string").str.strip()
        valid_prices[close_column] = pd.to_numeric(valid_prices[close_column], errors="coerce")
        available_symbols = set(
            valid_prices.loc[
                valid_prices[close_column] > 0,
                "symbol",
            ].dropna()
        )
        mapping["symbol"] = mapping["symbol"].astype("string").str.strip()
        mapping = mapping.loc[mapping["symbol"].isin(available_symbols)]

        return sorted({
            sector.strip()
            for sector in mapping["sector_name"].dropna().astype(str)
            if sector.strip()
        })

    def _load_sector_history_from_dataset(self, sector_name):
        """Load mapped company close-price histories for a sector from bundled CSV data."""
        try:
            prices = pd.read_csv(self.SECTOR_VOLUME_DATA_FILE)
            mapping = pd.read_csv(self.SECTOR_MAPPING_DATA_FILE)
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as error:
            return False, f"Unable to read bundled sector history data: {error}", {}

        close_column = "close_price" if "close_price" in prices.columns else "close"
        if not {"trade_date", "symbol", close_column}.issubset(prices.columns):
            return False, "Bundled trading data is missing required close-price columns", {}
        if not {"symbol", "sector_name"}.issubset(mapping.columns):
            return False, "Bundled sector mapping is missing required columns", {}

        prices = prices.loc[:, ["trade_date", "symbol", close_column]].copy()
        prices["trade_date"] = pd.to_datetime(prices["trade_date"], errors="coerce")
        prices["symbol"] = prices["symbol"].astype("string").str.strip()
        prices[close_column] = pd.to_numeric(prices[close_column], errors="coerce")
        prices = prices.dropna(subset=["trade_date", "symbol", close_column])
        prices = prices.loc[(prices["symbol"] != "") & (prices[close_column] > 0)]

        mapping = mapping.loc[:, ["symbol", "sector_name"]].copy()
        mapping["symbol"] = mapping["symbol"].astype("string").str.strip()
        mapping["sector_name"] = mapping["sector_name"].astype("string").str.strip()
        mapping = mapping.dropna(subset=["symbol", "sector_name"])
        mapping = mapping.loc[(mapping["symbol"] != "") & (mapping["sector_name"] != "")]
        mapping = mapping.drop_duplicates(subset=["symbol", "sector_name"])

        matching = mapping.loc[mapping["sector_name"] == sector_name]
        if matching.empty:
            return False, f"No company mapping found for sector: {sector_name}", {}

        sector_prices = prices.merge(matching[["symbol"]], on="symbol", how="inner")
        if sector_prices.empty:
            return False, f"No close prices found for sector: {sector_name}", {}

        recent_dates = sorted(sector_prices["trade_date"].drop_duplicates())[-30:]
        sector_prices = sector_prices.loc[sector_prices["trade_date"].isin(recent_dates)]
        dataset = {}
        for symbol, history in sector_prices.groupby("symbol", sort=True):
            history = history.sort_values("trade_date").drop_duplicates(
                subset=["trade_date"], keep="last"
            )
            dataset[str(symbol)] = [
                {
                    "date": row["trade_date"].date().isoformat(),
                    "close_price": float(row[close_column]),
                }
                for _, row in history.iterrows()
            ]

        if not dataset:
            return False, f"No usable close prices found for sector: {sector_name}", {}

        latest_date = max(recent_dates).date().isoformat()
        return True, f"Loaded {sector_name} close prices from bundled data dated {latest_date}", dataset

    def _load_sector_history_from_cash(self, sector_name):
        try:
            with open(self.SECTOR_HISTORY_CASH_FILE, "r", encoding="utf-8") as cash_file:
                cached = json.load(cash_file)
            cache_time = datetime.fromisoformat(cached["timestamp"])
            sectors = cached["data"]
            cache_age = datetime.now() - cache_time
            if (
                isinstance(sectors, dict)
                and timedelta(0) <= cache_age < self.SECTOR_HISTORY_CASH_DURATION
            ):
                dataset = sectors.get(sector_name)
                if isinstance(dataset, dict) and dataset:
                    return dataset
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return None
        return None

    def _save_sector_history_to_cash(self, sector_name, dataset):
        if not isinstance(dataset, dict) or not dataset:
            raise ValueError("Cannot cache empty sector close-price data")

        sectors = self._load_sector_history_cash_data()
        sectors[sector_name] = dataset
        os.makedirs(os.path.dirname(self.SECTOR_HISTORY_CASH_FILE), exist_ok=True)
        with open(self.SECTOR_HISTORY_CASH_FILE, "w", encoding="utf-8") as cash_file:
            json.dump(
                {"timestamp": datetime.now().isoformat(), "data": sectors},
                cash_file,
            )

    def _load_sector_history_cash_data(self):
        try:
            with open(self.SECTOR_HISTORY_CASH_FILE, "r", encoding="utf-8") as cash_file:
                cached = json.load(cash_file)
            data = cached.get("data")
            if isinstance(data, dict):
                return {
                    sector: histories
                    for sector, histories in data.items()
                    if isinstance(sector, str) and isinstance(histories, dict) and histories
                }
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
        return {}

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
                database_success, database_message, database_dataset = self.read_db.gettingSectorWiseCompanyClosePrice(
                    sectorName=value
                    )

                csv_success, csv_message, csv_dataset = self._load_sector_history_from_dataset(value)
                database_date = self._latest_sector_history_date(database_dataset)
                csv_date = self._latest_sector_history_date(csv_dataset)

                if (
                    database_success
                    and database_dataset
                    and database_date
                    and (not csv_success or not csv_dataset or not csv_date or database_date >= csv_date)
                ):
                    success, dMessage, dataset = True, database_message, database_dataset
                    data_source = "Database"
                elif csv_success and csv_dataset:
                    success, dMessage, dataset = True, csv_message, csv_dataset
                    data_source = "Bundled CSV"
                else:
                    dataset = self._load_sector_history_from_cash(value)
                    if dataset:
                        success = True
                        dMessage = f"Loaded {value} close prices from cache"
                        data_source = "Cached data"
                    else:
                        dMessage = csv_message or database_message
                        self.logMsg.error_message(message=dMessage or f"No price history available for {value}")
                        self._clear_sector_display()
                        return False, dMessage, None

                try:
                    self._save_sector_history_to_cash(value, dataset)
                except OSError as error:
                    self.logMsg.error_message(message=f"Unable to cache {value} price history: {error}")

                companySymbols = list(dataset.keys())
                close_prices = list(dataset.values())
                data_date = self._latest_sector_history_date(dataset)

                chartview = self.charts.showTimeSeriesChart(
                    trendDataList=close_prices,
                    stockName=companySymbols,
                    title=f"Performance of {value} | {data_source} through {data_date}"
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
                else:
                    self.logMsg.error_message(message=f"Could not create the {value} sector time-series chart.")

                #show sector table
                self.showSectorTable(
                    success=success,
                    dMessage=dMessage,
                    dataset=dataset
                    )

            except Exception as e:
                self.logMsg.error_message(message=f"Chart Render Error in Combobox: {str(e)}")

    @staticmethod
    def _latest_sector_history_date(dataset):
        if not isinstance(dataset, dict):
            return None
        dates = [
            point.get("date")
            for history in dataset.values()
            if isinstance(history, list)
            for point in history
            if isinstance(point, dict) and point.get("date")
        ]
        return max(dates) if dates else None

    def _clear_sector_display(self):
        layout = self.timeSeriesChartWidget.layout()
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        self.sectorWiseDetailTable.clearContents()
        self.sectorWiseDetailTable.setRowCount(0)
            
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