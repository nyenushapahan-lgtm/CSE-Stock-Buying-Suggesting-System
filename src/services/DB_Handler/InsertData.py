from src.databases.query import QueryOperation
import pandas as pd
import numpy as np


class InsertData():
    def __init__(self):
        #making query object
        self.query_obj = QueryOperation()

    @staticmethod
    def clean_market_data(frame: pd.DataFrame) -> pd.DataFrame:
        """Normalize CSE or bundled CSV columns and clean rows for database insertion."""
        frame = frame.copy()
        frame.columns = [str(column).strip() for column in frame.columns]
        frame = frame.rename(
            columns={
                "closingPrice": "close",
                "sharevolume": "volume",
                "percentageChange": "pct_change",
                "open_price": "open",
                "close_price": "close",
            }
        )

        required_columns = {
            "trade_date",
            "symbol",
            "name",
            "open",
            "high",
            "low",
            "close",
            "volume",
        }
        missing_columns = required_columns.difference(frame.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV is missing required columns: {missing}")

        for optional_column in ("turnover", "pct_change"):
            if optional_column not in frame.columns:
                frame[optional_column] = 0

        frame = frame.loc[
            :,
            [
                "trade_date",
                "symbol",
                "name",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "turnover",
                "pct_change",
            ],
        ].copy()
        frame["trade_date"] = pd.to_datetime(
            frame["trade_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        frame["symbol"] = frame["symbol"].fillna("").astype(str).str.strip()
        frame["name"] = frame["name"].fillna("").astype(str).str.strip()

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover",
            "pct_change",
        ]
        for column in numeric_columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        frame = frame.dropna(
            subset=["trade_date", "open", "high", "low", "close", "volume"]
        )
        frame = frame.loc[
            (frame["symbol"] != "")
            & (frame["open"] >= 0)
            & (frame["high"] >= 0)
            & (frame["low"] >= 0)
            & (frame["volume"] >= 0)
        ].copy()
        frame[["turnover", "pct_change"]] = frame[
            ["turnover", "pct_change"]
        ].fillna(0)

        non_zero_closes = frame.loc[frame["close"] != 0, "close"]
        if not non_zero_closes.empty:
            close_mean = non_zero_closes.mean()
            close_std = non_zero_closes.std()
            if pd.isna(close_std):
                close_std = 0
            zero_close_mask = frame["close"] == 0
            replacement_closes = np.random.normal(
                close_mean, close_std, size=int(zero_close_mask.sum())
            )
            frame.loc[zero_close_mask, "close"] = np.maximum(
                replacement_closes, 0.01
            )
        else:
            zero_close_mask = frame["close"] == 0
            frame.loc[zero_close_mask, "close"] = frame.loc[
                zero_close_mask, "open"
            ].round(2)

        frame = frame.loc[frame["close"] > 0]
        if frame.empty:
            raise ValueError("CSV contains no valid market data rows")
        return frame.reset_index(drop=True)

    def insert_csv_file(self,file_path:str)->tuple[bool,str,list[any]]:
        """Insert CSV file into MySQL Database"""
        if not file_path:
            return False,"File Location Cannot be Empty !",None
        
        #load the dataset
        try:
            df = pd.read_csv(file_path)
            return self.insert_dataframe(df)
        except Exception as e:
            return False,"Error : "+str(e),None

    def insert_dataframe(self, frame: pd.DataFrame) -> tuple[bool, str, None]:
        """Clean and insert CSE or CSV market data using the shared import path."""
        try:
            clean_frame = self.clean_market_data(frame)
        except (TypeError, ValueError, KeyError) as error:
            return False, f"Unable to clean market data: {error}", None

        data_values = list(clean_frame.itertuples(index=False, name=None))

        #write the SQL Query
        query = """
                    INSERT INTO historical_prices 
                    (
                        trade_date,
                        symbol,
                        name,
                        open_price,
                        high,
                        low,
                        close_price,
                        volume,
                        turnover,
                        pct_change
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                """
        
        #insert csv dataset
        success,dMessage,_ = self.query_obj.insertCSV(query=query,values=data_values)

        if not success:
            return success,dMessage,_

        return True, f"Successfully inserted {len(data_values)} market data rows", None
        
