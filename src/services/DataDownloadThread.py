from PySide6.QtCore import QThread, Signal
import pandas as pd
import time
from src.services.logger import Logging
import requests

class DataDownloadThread():
    def __init__(self):
        self.logMsg = Logging()

    def fetching_data(self,start_date,end_date):
        api_url = "https://www.cse.lk/api/tradeSummary" 

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        }

        #getting data on bussiness days only
        date_range = pd.date_range(start=start_date, end=end_date)

        all_dataframes = []

        self.logMsg.info_message(f"Starting Extraction from {start_date} to {end_date}")

        for current_date in date_range:
            #format the date as string
            date_str = current_date.strftime('%Y-%m-%d')

            #fetching data for 
            self.logMsg.dubug_message(message=f"Fetching data for: {date_str}")

            # The Payload: This tells the server which specific day we want
            # Update the key "date" if the CSE Network Tab shows a different key
            payload = {"date":date_str}

            try:
                response = requests.post(api_url,headers=headers,json=payload,timeout=10)

                if response.status_code == 200:
                    json_responce = response.json()
                    data_records = json_responce.get('reqTradeSummery', [])

                    if data_records:
                        #convert today's data to a DataFrame
                        daily_df = pd.DataFrame(data_records)

                        #add a date column
                        daily_df["trade_date"] = date_str

                        #store it in our master list
                        all_dataframes.append(daily_df)
                    
                    else:
                        self.logMsg.error_message(f"  -> No trading data found for {date_str} (Might be a public holiday).")

                else:
                    self.logMsg.error_message(f"  -> Failed. Status code: {response.status_code}")

            except Exception as e:
                self.logMsg.error_message(f"  -> Error fetching {date_str}: {e}")


            # RATE LIMITING: Pause for 2 seconds between requests. 
            # Never hammer a server with rapid-fire requests, or your IP will be blocked.
            time.sleep(2) 

        if all_dataframes:
            master_df = pd.concat(all_dataframes, ignore_index=True)
            return master_df
        
        else:
            return None