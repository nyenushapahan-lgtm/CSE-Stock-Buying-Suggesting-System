import requests
import pandas as pd
import time
import os
from src.services.logger import Logging
from PySide6.QtCore import QThread, Signal
from src.services.DB_Handler.InsertData import InsertData

class CSEDataDownload(QThread):
    progress_bar = Signal(int)
    download_finished = Signal(bool, str)

    def __init__(self,start_date,end_date):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.logMsg = Logging()

    def run(self):
        """Download the CSE data as a CSV file"""
        api_url = "https://www.cse.lk/api/tradeSummary"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        }

        #generate a list of dates
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='B')
        total_dates = len(date_range)

        all_dataframes = []

        self.logMsg.info_message(message=f"Starting extraction from {self.start_date} to {self.end_date} ..\n")

        for i,current_date in enumerate(date_range):
            #format the date as a string
            date_str = current_date.strftime('%Y-%m-%d')

            self.logMsg.info_message(message=f"Fetching data for: {date_str}")

            payload = {'date':date_str}

            try:
                responce = requests.post(api_url,headers=headers,json=payload, timeout=10)
                
                if responce.status_code == 200:
                    json_responce = responce.json()
                    data_records = json_responce.get('reqTradeSummery',[])

                    if data_records:
                        #converts today's data to a DataFrame
                        daily_df = pd.DataFrame(data_records)

                        #add column for date
                        daily_df['trade_date'] = date_str

                        #store it in our master list
                        all_dataframes.append(daily_df)

                    else:
                        self.logMsg.error_message(message=f"  -> No trading data found for {date_str} (Might be a public holiday).")
                 
                else:
                    self.logMsg.error_message(message=f"  -> Failed. Status code: {responce.status_code}")
                    
            except Exception as error:
                self.logMsg.error_message(
                    message=f"Failed to fetch CSE data for {date_str}: {error}"
                )

            #Update the progress bar
            progress_percentage = int(((i + 1) / total_dates) * 100)
            self.progress_bar.emit(min(progress_percentage, 99))

            time.sleep(2)

        #--- Combine all the daily DataFrame into one massive dataset
        if all_dataframes:
            master_df = pd.concat(all_dataframes, ignore_index=True)
            
        else:
            self.download_finished.emit(
                False, "No CSE market data was returned for the selected dates."
            )
            return
        
        self.logMsg.info_message(
            f"\nExtraction Complete! Loaded {len(master_df)} total stock records across multiple days."
        )

        try:
            importer = InsertData()
            clean_df = importer.clean_market_data(master_df)
            os.makedirs("./resources/data", exist_ok=True)
            clean_df.to_csv("./resources/data/data.csv", index=False)

            success, message, _ = importer.insert_dataframe(clean_df)
            if not success:
                self.logMsg.error_message(message=message)
                self.download_finished.emit(False, message)
                return

            self.logMsg.info_message(message=message)
            self.progress_bar.emit(100)
            self.download_finished.emit(True, message)
        except (OSError, TypeError, ValueError, KeyError) as error:
            message = f"Unable to clean or save downloaded CSE data: {error}"
            self.logMsg.error_message(message=message)
            self.download_finished.emit(False, message)
