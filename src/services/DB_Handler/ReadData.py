import re
from tkinter import NO
from typing import *
from src.databases.query import QueryOperation
from PySide6.QtCore import QDate

class ReadOperation():
    def __init__(self):
        self.query_obj = QueryOperation()

    def getting_tracked_stock_count(self)->Tuple[bool,str,list[any]]:
        """Return Tracked Stock Count date wise."""
        query = """
                SELECT
                    trade_date,
                    COUNT(DISTINCT  symbol) AS tracked_stock_count
                
                FROM
                    historical_prices

                GROUP BY
                    trade_date

                ORDER BY
                    trade_date ASC;
                """

        try:
            success,dMessage,dataset = self.query_obj.readSQL(query=query)

            if not success:
                return success,dMessage,[]
            
            return True,dMessage,dataset

        except Exception as e:
            return False,"Error : "+str(e),[]
        
    def gettingMaxDate(self)->Tuple[bool,str,list[any]]:
        """Return latest date that stored in mysql database"""
        query = "SELECT MAX(trade_date) FROM historical_prices;"
        try:
            success,dMessage,dataset = self.query_obj.readSQL(query=query)

            if not success:
                return success,dMessage,[]

            return success,dMessage,dataset

        except Exception as e:
            return False,"Error : "+str(e),[]
    
    def __gettingDayBeforeWeek(self)->Tuple[bool,str,str]:
        """Returning date that before 7 th date that according to the latest one"""

        query = "SELECT DATE_SUB(MAX(trade_date),INTERVAL 7 DAY) AS dayBeforeWeek FROM historical_prices;"

        try:
            success,dMessage,dataset = self.query_obj.readSQL(query=query)

            if not success:
                return success,dMessage,None
            
            return success,dMessage,dataset
        
        except Exception as e:
            return False, "Error : "+str(e),[]

    def getting_top_gainers(self)->Tuple[bool,str,list[Any]]:
        """
        Return top gainers Data Between latest data point and week before it
        """
        query_dates = "SELECT DISTINCT trade_date FROM historical_prices ORDER BY trade_date DESC LIMIT 6;"
        try:
            success, dMessage, dates_res = self.query_obj.readSQL(query=query_dates)
            if not success or not dates_res:
                return False, "No trading date data available", []
            
            dates_list = [item['trade_date'] for item in dates_res if item and item.get('trade_date')]
            if not dates_list:
                return False, "No valid trading dates found", []
            
            latest_date = dates_list[0].strftime("%Y-%m-%d") if hasattr(dates_list[0], 'strftime') else str(dates_list[0])
            prev_date = dates_list[-1].strftime("%Y-%m-%d") if hasattr(dates_list[-1], 'strftime') else str(dates_list[-1])

            if len(dates_list) == 1:
                query_single = """
                    SELECT 
                        name, symbol, close_price AS close_latest, 
                        open_price AS close_previous, pct_change AS weekly_pct_change
                    FROM historical_prices
                    WHERE trade_date = %s
                    ORDER BY pct_change DESC
                    LIMIT 10;
                """
                success, dMessage, dataset = self.query_obj.applyFilterForSQL(query=query_single, values=(latest_date,))
                return success, dMessage, dataset or []

            query = """
                SELECT 
                    DISTINCT latest.name,
                    latest.symbol,
                    latest.close_price AS close_latest,
                    previous.close_price AS close_previous,
                    CASE 
                        WHEN previous.close_price > 0 THEN ((latest.close_price - previous.close_price) / previous.close_price) * 100
                        ELSE latest.pct_change
                    END AS weekly_pct_change
                FROM historical_prices AS latest
                JOIN historical_prices AS previous 
                    ON latest.symbol = previous.symbol
                WHERE latest.trade_date = %s 
                  AND previous.trade_date = %s
                ORDER BY weekly_pct_change DESC
                LIMIT 10;
            """
            success, dMessage, dataset = self.query_obj.applyFilterForSQL(query=query, values=(latest_date, prev_date))
            
            if success and dataset:
                if hasattr(self, 'logMsg'):
                    self.logMsg.info_message(message="Successfully retrieved top gainers")
                return True, "Successfully retrieved top gainers", dataset

            query_fallback = """
                SELECT 
                    name, 
                    symbol, 
                    close_price AS close_latest, 
                    open_price AS close_previous, 
                    pct_change AS weekly_pct_change
                FROM historical_prices
                WHERE trade_date = %s
                ORDER BY pct_change DESC
                LIMIT 10;
            """
            return self.query_obj.applyFilterForSQL(query=query_fallback, values=(latest_date,))

        except Exception as e:
            return False, "Error getting top gainers: " + str(e), []
        
    def getting_past_close_prices(self,companySymbol)->Tuple[bool,str,list[Any]]:
        """Getting company close prices for about one year of historical data."""

        if not companySymbol:
            return False,"Company Symbol Cannot be Empty !",None
        
        query = """
                    SELECT
                        DISTINCT trade_date,
                        close_price
                    FROM historical_prices
                    WHERE symbol=%s
                    ORDER BY trade_date DESC 
                    LIMIT 60;"""
        
        values = (companySymbol,)

        try:
            success,dMessage,dataset = self.query_obj.applyFilterForSQL(query=query,values=values)

            if not success:
                return success,dMessage,None
            
            return success,dMessage,dataset
        
        except Exception as e:
            return False,"There is an Error : "+str(e),None
            
    def getting_industry_group_names(self)->Tuple[bool,str,list[Any]]:
        """Return Industry Group Names / Sectors or Categories"""
        query = "SELECT DISTINCT industryGroupName FROM material_sector;" 

        try:
            success,dMessage,dataset = self.query_obj.readSQL(query=query)

            if not success:
                return success,dMessage,None
            
            return success,dMessage,dataset

        except Exception as e:
            return False,"There is an Error : "+str(e), None

    def getting_all_sector_volumes(self)->Tuple[bool,str,dict]:
        """Return total volume per sector in a single optimized query."""
        query = """
                SELECT 
                    s.sectorName, 
                    SUM(h.volume) AS total_volume 
                FROM historical_prices h 
                JOIN sectorized_table s ON h.symbol = s.symbol 
                WHERE h.trade_date = (SELECT MAX(trade_date) FROM historical_prices) 
                GROUP BY s.sectorName;
                """
        try:
            success, dMessage, dataset = self.query_obj.readSQL(query=query)
            if not success or not dataset:
                return False, dMessage, None

            sector_volumes = {}
            for item in dataset:
                if item and item.get('sectorName'):
                    sector_volumes[item['sectorName']] = int(item.get('total_volume') or 0)
            return True, "Successfully retrieved sector volumes", sector_volumes

        except Exception as e:
            return False, "Error getting sector volumes: " + str(e), None
    
    def getting_category_based_company(self,category:str)->Tuple[bool,str,List[str]]:
        """Return company Names that Belongs to the sector category"""

        if not category:
            return False,"Company Category Cannot be Empty !",None
        
        query = "SELECT symbol FROM sectorized_table WHERE sectorName=%s;"
        values = (category,)
        try:
            success,dMessage,dataset = self.query_obj.applyFilterForSQL(query=query,values=values)

            if not success:
                return success,dMessage,None
            
            if not dataset:
                return success,dMessage,[]
            
            return success,dMessage,dataset
            
        except Exception as e:
            return False, "There is an Error : "+str(e),None
    
    def getting_company_latest_volume(self,symbol:str)->Tuple[bool,str,List[str]]:
        """Return company Latest Volume"""

        if not symbol:
            return False,"Company Symbol Cannot be Empty !",None
        
        query = """
                SELECT 
                    DISTINCT trade_date,
                    SUM(volume) AS volume
                FROM historical_prices 
                WHERE 
                    symbol = %s 
                    AND 
                    trade_date = (
                        SELECT 
                            MAX(trade_date) 
                        FROM historical_prices 
                        WHERE symbol=%s
                        );
                """
        
        values = (symbol,symbol)

        try:
            success,dMessage,dataset = self.query_obj.applyFilterForSQL(
                query=query,
                values=values
            )

            if not success:
                return success,dMessage,None
            
            return success,dMessage,dataset
        
        except Exception as e:
            return False,"There is an Error : "+str(e),None
    

    def gettingSectorWiseCompanyClosePrice(self, sectorName: str) -> Tuple[bool, str, dict]:
        """Return Sector Wise Company Closes Prices to study"""
        if not sectorName:
            return False, "Sector Name Cannot be Empty!", {}

        try:
            # ✅ Get company symbols once
            query_symbols = """
                SELECT DISTINCT h.symbol
                FROM historical_prices h
                JOIN sectorized_table s ON h.symbol = s.symbol
                WHERE h.trade_date = (SELECT MAX(trade_date) FROM historical_prices)
                AND s.sectorName = %s
                ORDER BY h.close_price DESC;
            """
            
            success, dMessage, symbols_dataset = self.query_obj.applyFilterForSQL(
                query=query_symbols,
                values=(sectorName,)
            )
            
            if not success:
                return False, dMessage, {}
            
            company_symbols = [row['symbol'] for row in symbols_dataset if row.get('symbol')]
            
            if not company_symbols:
                return False, f"No companies found in sector: {sectorName}", {}
            
            # ✅ Get last 30 trading dates
            query_dates = """
                SELECT DISTINCT trade_date 
                FROM historical_prices 
                ORDER BY trade_date DESC 
                LIMIT 30;
            """
            
            success, dMessage, dates_dataset = self.query_obj.readSQL(query=query_dates)
            
            if not success:
                return False, f"Error getting dates: {dMessage}", {}
            
            dates_list = [row['trade_date'] for row in dates_dataset if row.get('trade_date')]
            
            if len(dates_list) < 2:
                return False, "Not enough trading dates available", {}
            
            # ✅ Get data for last 5 days in a single query
            date_range = dates_list[1:29]  # Skip the latest date (index 0)
            
            if not date_range:
                return False, "No historical data available", {}
            
            # ✅ Build a single query for all dates
            placeholders = ','.join(['%s'] * len(date_range))
            query_prices = f"""
                SELECT 
                    h.symbol,
                    h.trade_date,
                    h.close_price
                FROM historical_prices h
                JOIN sectorized_table s ON h.symbol = s.symbol
                WHERE s.sectorName = %s
                AND h.trade_date IN ({placeholders})
                ORDER BY h.symbol, h.trade_date DESC;
            """
            
            values = [sectorName] + [date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date) for date in date_range]
            
            success, dMessage, price_dataset = self.query_obj.applyFilterForSQL(
                query=query_prices,
                values=tuple(values)
            )
            
            if not success:
                return False, f"Error getting prices: {dMessage}", {}
            
            # ✅ Organize data by symbol
            sector_details = {symbol: [] for symbol in company_symbols}
            
            for row in price_dataset:
                symbol = row.get('symbol')
                trade_date = row.get('trade_date')
                close_price = row.get('close_price')
                
                if symbol in sector_details and trade_date and close_price is not None:
                    date_str = trade_date.strftime("%Y-%m-%d") if hasattr(trade_date, 'strftime') else str(trade_date)
                    sector_details[symbol].append({
                        'date': date_str,
                        'close_price': float(close_price)
                    })
            
            # ✅ Sort dates for each symbol (newest first)
            for symbol in sector_details:
                sector_details[symbol].sort(key=lambda x: x['date'], reverse=True)
            
            # ✅ Remove symbols with no data
            sector_details = {k: v for k, v in sector_details.items() if v}
            
            if not sector_details:
                return False, "No price data found for companies in this sector", {}
            
            return True, "Successfully retrieved sector data", sector_details
            
        except Exception as e:
            return False, f"Error in gettingSectorWiseCompanyClosePrice: {str(e)}", {}
        
        
    def gettingCompanyFullDetails(self,symbol)->Tuple[bool,str,dict]:
        """
        Using Company Symbol Return Company Full Details from the database
        """
        if not symbol:
            return False,"Company Symbol Cannot be Empty !",None
        
        query = """
                    SELECT DISTINCT(trade_date),
                        open_price,
                        high,
                        low,
                        close_price,
                        volume 
                    FROM historical_prices 
                    WHERE 
                        symbol=%s;
                """

        values = (symbol,)

        try:
            success,dMessage,dataset = self.query_obj.applyFilterForSQL(
                query=query,
                values=values
                )
            
            if not success:
                return success,dMessage,None
            
            return success,dMessage,dataset


        except Exception as e:
            return False,"Error gettingCompanyFullDetails() : "+str(e),None
            
