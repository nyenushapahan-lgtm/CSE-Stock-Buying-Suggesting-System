import os
import tempfile
import time
from datetime import date, timedelta

import pandas as pd
import requests
from PySide6.QtCore import QThread, Signal

from src.services.logger import Logging


DATA_COLUMNS = [
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
]


def normalize_market_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize CSE API rows to the bundled CSV format."""
    frame = frame.rename(
        columns={
            "closingPrice": "close",
            "sharevolume": "volume",
            "percentageChange": "pct_change",
        }
    ).copy()
    if not set(DATA_COLUMNS[:8]).issubset(frame.columns):
        raise ValueError("CSE response is missing required market data columns")
    for optional_column in ("turnover", "pct_change"):
        if optional_column not in frame.columns:
            frame[optional_column] = 0

    frame = frame.loc[:, DATA_COLUMNS]
    frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    frame["symbol"] = frame["symbol"].astype("string").str.strip()
    frame["name"] = frame["name"].fillna("").astype(str).str.strip()
    numeric_columns = DATA_COLUMNS[3:]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["trade_date", "symbol", "open", "high", "low", "close", "volume"])
    frame = frame.loc[(frame["symbol"] != "") & (frame["close"] > 0)]
    frame["volume"] = frame["volume"].astype("int64")
    return frame


def merge_market_data(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    """Merge refreshed rows without discarding older bundled history."""
    frames = []
    for frame in (existing, incoming):
        if frame is not None and not frame.empty:
            frames.append(normalize_market_data(frame))
    if not frames:
        raise ValueError("No valid market data is available to save")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(subset=["trade_date", "symbol"], keep="last")
    merged = merged.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    return merged.loc[:, DATA_COLUMNS]


class MarketDataRefreshThread(QThread):
    refresh_finished = Signal(str)
    refresh_failed = Signal(str)

    def __init__(self, csv_path: str, parent=None):
        super().__init__(parent)
        self.csv_path = csv_path
        self.logMsg = Logging()

    def run(self):
        try:
            existing = pd.read_csv(self.csv_path) if os.path.exists(self.csv_path) else pd.DataFrame()
            if not existing.empty and "trade_date" not in existing.columns:
                raise ValueError("Bundled market data is missing its trade_date column")

            today = date.today()
            earliest_refresh_date = today - timedelta(days=7)
            if not existing.empty:
                latest_saved_date = pd.to_datetime(
                    existing["trade_date"], errors="coerce"
                ).max()
                if pd.isna(latest_saved_date):
                    raise ValueError("Bundled market data has no valid trading dates")
                start_date = max(earliest_refresh_date, latest_saved_date.date())
            else:
                start_date = earliest_refresh_date

            trading_days = pd.date_range(start=start_date, end=today, freq="B")
            frames = []
            errors = []
            for index, trading_day in enumerate(trading_days):
                date_text = trading_day.strftime("%Y-%m-%d")
                try:
                    response = requests.post(
                        "https://www.cse.lk/api/tradeSummary",
                        headers={
                            "User-Agent": "Mozilla/5.0",
                            "Accept": "application/json, text/plain, */*",
                            "Content-Type": "application/json",
                        },
                        json={"date": date_text},
                        timeout=10,
                    )
                    response.raise_for_status()
                    records = response.json().get("reqTradeSummery", [])
                    if records:
                        daily = pd.DataFrame(records)
                        daily["trade_date"] = date_text
                        frames.append(normalize_market_data(daily))
                except (requests.RequestException, ValueError, TypeError) as error:
                    errors.append(f"{date_text}: {error}")
                    self.logMsg.error_message(message=f"Market data refresh failed for {date_text}: {error}")

                if index < len(trading_days) - 1:
                    time.sleep(2)

            if not frames:
                if errors:
                    raise RuntimeError("; ".join(errors))
                latest_date = (
                    pd.to_datetime(existing["trade_date"], errors="coerce").max().date().isoformat()
                    if not existing.empty
                    else "none"
                )
                self.refresh_finished.emit(f"Bundled market data is current through {latest_date}")
                return

            merged = merge_market_data(existing, pd.concat(frames, ignore_index=True))
            directory = os.path.dirname(self.csv_path) or "."
            os.makedirs(directory, exist_ok=True)
            file_descriptor, temporary_path = tempfile.mkstemp(
                prefix=".market-data-",
                suffix=".csv",
                dir=directory,
            )
            os.close(file_descriptor)
            try:
                merged.to_csv(temporary_path, index=False)
                os.replace(temporary_path, self.csv_path)
            finally:
                if os.path.exists(temporary_path):
                    os.remove(temporary_path)

            latest_date = merged["trade_date"].max()
            self.refresh_finished.emit(
                f"Bundled market data refreshed through {latest_date}"
            )
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, RuntimeError) as error:
            message = f"Bundled market data refresh failed: {error}"
            self.logMsg.error_message(message=message)
            self.refresh_failed.emit(message)
