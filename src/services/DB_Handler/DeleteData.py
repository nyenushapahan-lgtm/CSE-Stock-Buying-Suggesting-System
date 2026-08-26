from typing import *
from src.databases.query import QueryOperation
from PySide6.QtCore import QDate

class DeleteOperation():
    def __init__(self):
        self.query_obj = QueryOperation()

    def deleteHistoricalPriceData(self):
        """Delete data from month back"""

        query = """
                DELETE FROM historical_prices 
                WHERE trade_date < (
                    SELECT MAX(trade_date) - INTERVAL 30 DAY 
                    FROM historical_prices
                    );
                """
        
        success,dMessage,_ = self.query_obj.deleteSQL(
            query=query,
            values=()
        )

        if not success:
            return success,dMessage,_
        
        return success,dMessage,_