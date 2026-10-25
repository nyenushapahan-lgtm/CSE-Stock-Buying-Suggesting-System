import pandas as pd
from src.services.DB_Handler.ReadData import ReadOperation
from PySide6.QtCore import QDate
from typing import *
import json
import os
from datetime import datetime, timedelta
from functools import lru_cache

class MainData():
    """
    Process All the data for main window
    """
    def __init__(self):
        """Data Return for dashboard main items"""
        self.db_read = ReadOperation()

        #cash files
        self.CASH_FILE = './resources/cash/sector_wise_investments_cash.json'
        self.CASH_DURATION = timedelta(days=1)
        self.SECTOR_VOLUME_DATA_FILE = './resources/data/data.csv'
        self.SECTOR_MAPPING_DATA_FILE = './my_mapped_symboled.csv'
        self.CLOSE_PRICE_CASH_FILE = './resources/cash/top_gainers_close_prices_cash.json'
        self.CLOSE_PRICE_CASH_DURATION = timedelta(days=1)

    def average_tracked_st_count(self):
        """Calculate average tracked stocks count ."""

        success,dMessage,dataset = self.db_read.getting_tracked_stock_count()

        if not dataset:
            return False, dMessage, 0

        #calculate the average st count
        totalStCount = 0

        for item in dataset:
            totalStCount += int(item["tracked_stock_count"])

        average_st_count = totalStCount/len(dataset) if len(dataset) > 0 else 0

        return True, dMessage, average_st_count
    
    def FindLatestDate(self)->Tuple[bool,str,any]:
        """This methord returns maximum date that stored in mysql database.\n
        Based on that can asign import function begining date"""

        success,dMessage,dataset = self.db_read.gettingMaxDate()

        if not success:
            return success,dMessage,None
        
        py_date = dataset[0]["MAX(trade_date)"]

        qDate = QDate(py_date.year, py_date.month, py_date.day)

        return True,"Successfully Return QDate Object ",qDate
    
    def findTop10Gainers(self)->Tuple[bool,str,Any]:
        """This methord is doing formating the dataset that returns \n
        Latest day and 7 days before it data representation
        """

        success,dMessage,dataset = self.db_read.getting_top_gainers()

        if not success:
            return success,dMessage,None
        
        
        format_dataset = []
        count = 1

        for item in dataset:
            #formating the dataset
            format_dataset.append({
                "No":count,
                "symbol":item["symbol"],
                "name":item["name"],
                "close_latest":item["close_latest"],
                "close_previous":item["close_previous"],
                "weekly_pct_change":item["weekly_pct_change"]
            })
            count += 1
        
        if not format_dataset:
            dMessage = "The list is empty !"
            return False,dMessage,[]

        return True,dMessage,format_dataset
    
    def loadClosedPrices(self)->Tuple[bool,str,Tuple[List,List]]:
        """
            Get top-gainer close prices from the database, bundled data, or cache.
        """
        database_error = "No top-gainer data available"
        success, message, gainers = self.findTop10Gainers()
        database_dataset = None
        if success and gainers:
            close_price_data = []
            valid_symbols = []

            for item in gainers:
                symbol = item.get("symbol") if item else None
                if not symbol:
                    continue

                price_success, price_message, prices = self.db_read.getting_past_close_prices(
                    companySymbol=symbol
                )
                if not price_success or not prices:
                    database_error = price_message or f"No close prices found for {symbol}"
                    continue

                series = self._format_close_price_series(prices)
                if series:
                    close_price_data.append(series)
                    valid_symbols.append(symbol)

            if close_price_data:
                database_dataset = (close_price_data, valid_symbols)
        else:
            database_error = message or database_error

        dataset_success, dataset_message, dataset = self._load_close_prices_from_dataset()
        if database_dataset and dataset_success and dataset:
            database_date = self._latest_close_price_date(database_dataset[0])
            bundled_date = self._latest_close_price_date(dataset[0])
            if database_date and bundled_date and database_date >= bundled_date:
                self._save_close_prices_to_cash(database_dataset)
                return True, f"Database close prices through {database_date}", database_dataset
            self._save_close_prices_to_cash(dataset)
            return True, dataset_message, dataset
        if database_dataset:
            database_date = self._latest_close_price_date(database_dataset[0])
            self._save_close_prices_to_cash(database_dataset)
            return True, f"Database close prices through {database_date}", database_dataset
        if dataset_success and dataset:
            self._save_close_prices_to_cash(dataset)
            return True, dataset_message, dataset

        cached_dataset = self._load_close_prices_from_cash()
        if cached_dataset:
            cache_date = self._latest_close_price_date(cached_dataset[0])
            return True, f"Cached top-gainer close prices through {cache_date}", cached_dataset

        return False, f"{database_error}; {dataset_message}", (None, None)

    @staticmethod
    def _latest_close_price_date(histories):
        dates = [
            point.get("date")
            for history in histories
            for point in history
            if point.get("date")
        ]
        return max(dates) if dates else None

    @staticmethod
    def _format_close_price_series(rows):
        """Normalize price rows and sort them chronologically for charting."""
        formatted = []
        for row in rows:
            date_value = row.get("trade_date", row.get("date")) if row else None
            if date_value is None:
                continue
            try:
                date = pd.to_datetime(date_value, errors="raise").date().isoformat()
                close_price = float(row.get("close_price"))
            except (TypeError, ValueError, OverflowError):
                continue
            if close_price <= 0:
                continue
            formatted.append({"date": date, "close_price": close_price})

        formatted.sort(key=lambda item: item["date"])
        return formatted

    def _load_close_prices_from_dataset(self)->Tuple[bool,str,Optional[Tuple[List,List]]]:
        """Build close-price histories for the latest top gainers from the bundled CSV."""
        try:
            prices = pd.read_csv(self.SECTOR_VOLUME_DATA_FILE)
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as e:
            return False, f"Unable to read bundled close-price data: {e}", None

        close_column = "close_price" if "close_price" in prices.columns else "close"
        required_columns = {"trade_date", "symbol", close_column}
        if not required_columns.issubset(prices.columns):
            return False, "Bundled trading data is missing close-price columns", None

        prices = prices.loc[:, ["trade_date", "symbol", close_column] + (
            ["name"] if "name" in prices.columns else []
        ) + (["pct_change"] if "pct_change" in prices.columns else [])].copy()
        prices["trade_date"] = pd.to_datetime(prices["trade_date"], errors="coerce")
        prices["symbol"] = prices["symbol"].astype("string").str.strip()
        prices[close_column] = pd.to_numeric(prices[close_column], errors="coerce")
        prices = prices.dropna(subset=["trade_date", "symbol", close_column])
        prices = prices.loc[(prices["symbol"] != "") & (prices[close_column] > 0)]
        if prices.empty:
            return False, "Bundled trading data contains no valid close prices", None

        trading_dates = sorted(prices["trade_date"].drop_duplicates())
        latest_date = trading_dates[-1]
        latest = prices.loc[prices["trade_date"] == latest_date].drop_duplicates(
            subset=["symbol"], keep="last"
        )

        if len(trading_dates) > 1:
            comparison_date = trading_dates[max(0, len(trading_dates) - 6)]
            comparison = prices.loc[prices["trade_date"] == comparison_date, ["symbol", close_column]]
            comparison = comparison.drop_duplicates(subset=["symbol"], keep="last").rename(
                columns={close_column: "comparison_close"}
            )
            gainers = latest.merge(comparison, on="symbol", how="inner")
            gainers["change"] = (
                (gainers[close_column] - gainers["comparison_close"])
                / gainers["comparison_close"].where(gainers["comparison_close"] > 0)
            ) * 100
        else:
            gainers = latest.copy()
            gainers["change"] = pd.to_numeric(gainers.get("pct_change"), errors="coerce")

        if "pct_change" in latest.columns:
            gainers["change"] = gainers["change"].fillna(
                pd.to_numeric(gainers["pct_change"], errors="coerce")
            )
        gainers = gainers.dropna(subset=["change"]).sort_values("change", ascending=False).head(10)
        if gainers.empty:
            return False, "Bundled trading data contains no comparable top gainers", None

        histories = []
        symbols = []
        for symbol in gainers["symbol"]:
            history = prices.loc[prices["symbol"] == symbol].sort_values("trade_date").tail(60)
            series = self._format_close_price_series(
                [
                    {"trade_date": row.trade_date, "close_price": getattr(row, close_column)}
                    for row in history.itertuples(index=False)
                ]
            )
            if series:
                histories.append(series)
                symbols.append(str(symbol))

        if not histories:
            return False, "Bundled trading data has no top-gainer price history", None

        return True, f"Bundled CSV close prices through {latest_date.date()}", (
            histories,
            symbols,
        )

    def _load_close_prices_from_cash(self):
        """Load a recent, valid top-gainer price-history cache."""
        try:
            with open(self.CLOSE_PRICE_CASH_FILE, "r", encoding="utf-8") as cash_file:
                cached = json.load(cash_file)
            cache_time = datetime.fromisoformat(cached["timestamp"])
            histories = cached["data"]["histories"]
            symbols = cached["data"]["symbols"]
            if (
                not isinstance(histories, list)
                or not isinstance(symbols, list)
                or len(histories) != len(symbols)
                or not all(isinstance(history, list) for history in histories)
                or not all(isinstance(symbol, str) and symbol.strip() for symbol in symbols)
                or not all(
                    isinstance(point, dict)
                    for history in histories
                    for point in history
                )
            ):
                return None

            formatted_histories = [
                self._format_close_price_series(history) for history in histories
            ]
            if not symbols or not all(formatted_histories):
                return None
            cache_age = datetime.now() - cache_time
            if timedelta(0) <= cache_age < self.CLOSE_PRICE_CASH_DURATION:
                return formatted_histories, symbols
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return None
        return None

    def _save_close_prices_to_cash(self, dataset):
        """Save normalized top-gainer price histories for offline chart rendering."""
        histories, symbols = dataset
        if not histories or len(histories) != len(symbols) or not all(histories):
            raise ValueError("Cannot cache empty or invalid top-gainer price data")

        cached = {
            "timestamp": datetime.now().isoformat(),
            "data": {"histories": histories, "symbols": symbols},
        }
        os.makedirs(os.path.dirname(self.CLOSE_PRICE_CASH_FILE), exist_ok=True)
        with open(self.CLOSE_PRICE_CASH_FILE, "w", encoding="utf-8") as cash_file:
            json.dump(cached, cash_file)


    def getSectorWiseInvestmentsDetails(self,force_refresh=False)->Tuple[bool,str,Dict[str,int]]:
        """Return sector wise investsments data.\n
            Gives sector based total volume
        """
        #check if we have the cash files
        if not force_refresh:
            cashed_data = self._load_from_cash()

            if cashed_data and not self._bundled_data_is_newer_than_cache():
                cache_timestamp = self._sector_volume_cache_timestamp()
                return True, f"Cached sector-volume snapshot from {cache_timestamp}", cashed_data

        # Fast 1-query optimization
        fast_success, fast_msg, fast_volumes = self.db_read.getting_all_sector_volumes()
        if fast_success and fast_volumes:
            database_date = self._latest_database_trade_date()
            bundled_date = self._latest_bundled_trade_date()
            if bundled_date and (not database_date or bundled_date > database_date):
                fallback_success, fallback_message, fallback_volumes = self._load_sector_volumes_from_dataset()
                if fallback_success and fallback_volumes:
                    self._save_to_cash(fallback_volumes)
                    return True, fallback_message, fallback_volumes
            self._save_to_cash(fast_volumes)
            date_text = f" through {database_date}" if database_date else ""
            return True, f"Database sector volumes{date_text}", fast_volumes
            
        #getting industry names
        success,dMessage,dataset = self.readIndustryGroupName()

        #getting company names according to the sectors
        sectorBasedCompany = {}
        sectorBasedVolume = {}
        

        if not success:
            fallback_success, fallback_message, fallback_volumes = self._load_sector_volumes_from_dataset()
            if not fallback_success:
                return False, f"{dMessage}; {fallback_message}", None

            self._save_to_cash(fallback_volumes)
            return True, fallback_message, fallback_volumes
        
        for item in dataset:
            if item:
                #created for one sector
                companySymbols = []
                totalVolume = 0

                #Based on the Sectors its company names returns to company symbols
                success,dMessage,companySymbols = self.__readCompanyNames(sectorName=item)

                if success:
                    #based on the sector category company symbols asigns
                    sectorBasedCompany[item] = companySymbols
        
                    #using company symbols calculate each sector release how much of volume or shares to the share market
                    for symbol in companySymbols:
                        success,dMessage,volume = self.__calculateSectorBasedTotalVolume(companySymbol=symbol)

                        if success:
                            totalVolume += int(volume)
                
                #asign sector based volume
                sectorBasedVolume[item] = totalVolume

        #save to cash after loop completes
        self._save_to_cash(sectorBasedVolume)

        return True,"Successfully Calculated the volume",sectorBasedVolume

    def _latest_bundled_trade_date(self):
        try:
            dates = pd.read_csv(self.SECTOR_VOLUME_DATA_FILE, usecols=["trade_date"])["trade_date"]
            dates = pd.to_datetime(dates, errors="coerce").dropna()
            return dates.max().date().isoformat() if not dates.empty else None
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError):
            return None

    def _latest_database_trade_date(self):
        try:
            success, _, dataset = self.db_read.gettingMaxDate()
            if success and dataset and dataset[0]:
                latest_date = next(iter(dataset[0].values()))
                if latest_date:
                    return latest_date.date().isoformat() if hasattr(latest_date, "date") else str(latest_date)
        except (AttributeError, IndexError, TypeError, ValueError):
            return None
        return None

    def _bundled_data_is_newer_than_cache(self):
        try:
            return (
                os.path.exists(self.SECTOR_VOLUME_DATA_FILE)
                and os.path.exists(self.CASH_FILE)
                and os.path.getmtime(self.SECTOR_VOLUME_DATA_FILE) > os.path.getmtime(self.CASH_FILE)
            )
        except OSError:
            return False

    def _sector_volume_cache_timestamp(self):
        try:
            with open(self.CASH_FILE, "r", encoding="utf-8") as cache_file:
                cache_data = json.load(cache_file)
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            return timestamp.strftime("%Y-%m-%d %H:%M")
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return "an unknown date"

    def _load_sector_volumes_from_dataset(self)->Tuple[bool,str,Optional[Dict[str,int]]]:
        """Aggregate the latest bundled trading-data snapshot by mapped sector."""
        try:
            prices = pd.read_csv(self.SECTOR_VOLUME_DATA_FILE)
            sector_mapping = pd.read_csv(self.SECTOR_MAPPING_DATA_FILE)
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as e:
            return False, f"Unable to read bundled sector-volume data: {e}", None

        required_price_columns = {"trade_date", "symbol", "volume"}
        required_mapping_columns = {"symbol", "sector_name"}
        if not required_price_columns.issubset(prices.columns):
            return False, "Bundled trading data is missing required columns", None
        if not required_mapping_columns.issubset(sector_mapping.columns):
            return False, "Bundled sector mapping is missing required columns", None

        prices = prices.loc[:, ["trade_date", "symbol", "volume"]].copy()
        prices["trade_date"] = pd.to_datetime(prices["trade_date"], errors="coerce")
        prices["volume"] = pd.to_numeric(prices["volume"], errors="coerce")
        prices["symbol"] = prices["symbol"].astype("string").str.strip()
        prices = prices.dropna(subset=["trade_date", "symbol", "volume"])
        prices = prices.loc[prices["volume"] >= 0]
        if prices.empty:
            return False, "Bundled trading data contains no valid volume records", None

        latest_trade_date = prices["trade_date"].max()
        prices = prices.loc[prices["trade_date"] == latest_trade_date]

        sector_mapping = sector_mapping.loc[:, ["symbol", "sector_name"]].copy()
        sector_mapping["symbol"] = sector_mapping["symbol"].astype("string").str.strip()
        sector_mapping["sector_name"] = sector_mapping["sector_name"].astype("string").str.strip()
        sector_mapping = sector_mapping.dropna(subset=["symbol", "sector_name"])
        sector_mapping = sector_mapping.loc[sector_mapping["symbol"] != ""]
        sector_mapping = sector_mapping.loc[sector_mapping["sector_name"] != ""]

        conflicting_mappings = (
            sector_mapping.groupby("symbol")["sector_name"].nunique().gt(1)
        )
        if conflicting_mappings.any():
            return False, "Bundled sector mapping assigns symbols to multiple sectors", None

        sector_mapping = sector_mapping.drop_duplicates(subset=["symbol"])
        sector_data = prices.merge(sector_mapping, on="symbol", how="inner", validate="many_to_one")
        if sector_data.empty:
            return False, "No bundled trading records match the sector mapping", None

        sector_volumes = {
            sector: int(volume)
            for sector, volume in (
                sector_data.groupby("sector_name", sort=True)["volume"].sum().items()
            )
        }
        trade_date = latest_trade_date.date().isoformat()
        return True, f"Loaded sector volumes from bundled data dated {trade_date}", sector_volumes

    def getSectorWiseClosePriceDetails(self):
        """Getting Sectorwise Company names and those companies close prices"""
        success,dMessage,dataset = self.readIndustryGroupName()

    def __calculateSectorBasedTotalVolume(self,companySymbol)->Tuple[bool,str,int]:
        """Calculate the total volume that based on the sectors"""

        if not companySymbol:
            return False, "Company Symbol Cannot be Empty !",0
        
        #getting company wise latest volume count
        success,dMessage,dataset = self.db_read.getting_company_latest_volume(symbol=companySymbol)

        if not dataset or not dataset[0]:
            return False, dMessage, 0
        
        volume = dataset[0].get('volume') or 0

        return success,dMessage,int(volume)

    def __readCompanyNames(self,sectorName:str):
        """Getting company Names that belongs to sectors"""
        companySymbols = []

        success,dMessage,dataset = self.db_read.getting_category_based_company(category=sectorName)

        if not success:
            return success,dMessage,None
        
        if not dataset:
            return success,dMessage,[]
        
        for item in dataset:
            if item['symbol']:
                companySymbols.append(item['symbol'])


        return success,dMessage,companySymbols
        

    def readIndustryGroupName(self)->Tuple[bool,str,List[str]]:
        """Return industry Group Names"""
        industryGroupNames = []
        
        #getting sectors details
        success,dMessage,dataset = self.db_read.getting_industry_group_names()

        if not success:
            return success,dMessage,None
        
        for item in dataset:
            industryGroupNames.append(item['industryGroupName'])
        
        if not industryGroupNames:
            return False,"Indusctry Group Names List is Empty !",None
        
        return True,"Data added Successfully !",industryGroupNames
        
    def _load_from_cash(self):
        """Load a recent, structurally valid sector-volume snapshot."""
        try:
            if os.path.exists(self.CASH_FILE):
                with open(self.CASH_FILE, "r", encoding="utf-8") as f:
                    cash_data = json.load(f)

                cache_time = datetime.fromisoformat(cash_data["timestamp"])
                data = cash_data["data"]
                if not isinstance(data, dict) or not data:
                    return None

                normalized_data = {}
                for sector, volume in data.items():
                    if not isinstance(sector, str) or not sector.strip():
                        return None
                    numeric_volume = int(volume)
                    if numeric_volume < 0:
                        return None
                    normalized_data[sector.strip()] = numeric_volume

                cache_age = datetime.now() - cache_time
                if timedelta(0) <= cache_age < self.CASH_DURATION:
                    return normalized_data
                
        except (OSError, ValueError, TypeError, KeyError, OverflowError, json.JSONDecodeError):
            return None

        return None
    
    def _save_to_cash(self,data):
        """Save sector volumes in the cache format consumed by _load_from_cash."""
        if not isinstance(data, dict) or not data:
            raise ValueError("Cannot cache empty or invalid sector-volume data")

        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        os.makedirs(os.path.dirname(self.CASH_FILE), exist_ok=True)
        with open(self.CASH_FILE, "w", encoding="utf-8") as cache_file:
            json.dump(cache_data, cache_file)

    # ---------- Load Data From 30 Days Back---------------------------
    def __load30DaysBackData(self)->Dict:
        """Returns Back to 30 days of data"""
        success,dMessage,dataset = self.db_read.returnDataFromServer()

        if not success:
            return success,dMessage,None

        dataset = pd.DataFrame(dataset)

        return dataset

        #return the dataset
    # ---------- Helper function to generate recommendations ----------
    def generate_recommendations(self, weights=None, buy_percentile=0.25, sell_percentile=0.75,min_days=30)->dict:
        """
        Generate stock recommendations based on statistical scoring.

        Parameters:
            df (pd.DataFrame): DataFrame with columns: symbol, name, trade_date,
                            close_price, volume.
            weights (dict): Optional weights for the four metrics.
                            Default: {'norm_return':0.35, 'norm_volatility':0.25,
                                    'norm_trend':0.25, 'norm_volume':0.15}
            buy_percentile (float): Top fraction to label as BUY (e.g., 0.25).
            sell_percentile (float): Bottom fraction to label as SELL (e.g., 0.75).
            min_days (int): Minimum number of trading days required per stock.

        Returns:
            list: A list of dictionaries with keys 'code', 'name', 'suggestion'.
        """

        #setting up the dataframe
        df = self.__load30DaysBackData()

        if isinstance(df, tuple):
            return {"error": df[1]}

        if df is None or df.empty:
            dMessage = {
                "error":"There is no dataset found !"
            }
            return dMessage

        # Default weights if not provided
        if weights is None:
            weights = {
                'norm_return': 0.35,
                'norm_volatility': 0.25,
                'norm_trend': 0.25,
                'norm_volume': 0.15
            }

        results = []

        # --- Process each stock ---
        try:
            # Ensure correct data types and sorting
            df = df.copy()
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.sort_values(['symbol', 'trade_date'], inplace=True)

            for symbol, group in df.groupby('symbol'):
                try:
                    if len(group) < min_days:
                        continue

                    close = group['close_price']
                    volume = group['volume']

                    # Metric 1: Total Return (%)
                    total_return = (close.iloc[-1] / close.iloc[0] - 1) * 100

                    # Metric 2: Volatility (std of daily returns, %)
                    daily_returns = close.pct_change().dropna()
                    volatility = daily_returns.std() * 100

                    # Metric 3: Trend Strength (distance from 20-day MA, %)
                    ma20 = close.rolling(20).mean().iloc[-1]
                    last_close = close.iloc[-1]
                    trend_strength = ((last_close / ma20) - 1) * 100

                    # Metric 4: Volume Momentum (last 5 days vs overall average, %)
                    avg_vol_last5 = volume.iloc[-5:].mean()
                    avg_vol_overall = volume.mean()
                    volume_momentum = (avg_vol_last5 / avg_vol_overall) * 100

                    results.append({
                        'symbol': symbol,
                        'name': group['name'].iloc[0],
                        'total_return': total_return,
                        'volatility': volatility,
                        'trend_strength': trend_strength,
                        'volume_momentum': volume_momentum
                    })

                except Exception as e:
                    # Log error for this symbol and continue
                    dMessage = "Error processing symbol " + str(symbol) + ": " + str(e)
                    print(dMessage)   # Replace with your logging mechanism
                    continue

        except Exception as e:
            dMessage = "Error during data grouping: " + str(e)
            print(dMessage)   # Replace with your logging mechanism
            return []   # Return empty list on major failure

        if not results:
            print("No valid stocks after processing.")
            return []

        df_metrics = pd.DataFrame(results)

        # --- Normalisation (min-max) ---
        try:
            def min_max_normalize(series, reverse=False):
                min_val = series.min()
                max_val = series.max()
                if max_val == min_val:
                    return pd.Series([0.5] * len(series))
                norm = (series - min_val) / (max_val - min_val)
                return 1 - norm if reverse else norm

            df_metrics['norm_return'] = min_max_normalize(df_metrics['total_return'], False)
            df_metrics['norm_volatility'] = min_max_normalize(df_metrics['volatility'], True)   # lower is better
            df_metrics['norm_trend'] = min_max_normalize(df_metrics['trend_strength'], False)
            df_metrics['norm_volume'] = min_max_normalize(df_metrics['volume_momentum'], False)

        except Exception as e:
            dMessage = "Error during normalisation: " + str(e)
            print(dMessage)   # Replace with your logging mechanism
            return []

        # --- Composite Score ---
        try:
            df_metrics['composite_score'] = (
                weights['norm_return'] * df_metrics['norm_return'] +
                weights['norm_volatility'] * df_metrics['norm_volatility'] +
                weights['norm_trend'] * df_metrics['norm_trend'] +
                weights['norm_volume'] * df_metrics['norm_volume']
            )
        except KeyError as e:
            dMessage = "Missing weight key: " + str(e)
            print(dMessage)
            return []
        except Exception as e:
            dMessage = "Error computing composite score: " + str(e)
            print(dMessage)
            return []

        # --- Classification ---
        try:
            df_metrics.sort_values('composite_score', ascending=False, inplace=True)
            n = len(df_metrics)
            buy_idx = int(buy_percentile * n)
            sell_idx = int(sell_percentile * n)

            df_metrics['recommendation'] = 'HOLD'
            df_metrics.iloc[:buy_idx, df_metrics.columns.get_loc('recommendation')] = 'BUY'
            df_metrics.iloc[sell_idx:, df_metrics.columns.get_loc('recommendation')] = 'SELL'

        except Exception as e:
            dMessage = "Error during classification: " + str(e)
            print(dMessage)
            return []

        # --- Build output list ---
        output = []
        for _, row in df_metrics.iterrows():
            output.append({
                'code': row['symbol'],
                'name': row['name'],
                'suggestion': row['recommendation']
            })

        return output
