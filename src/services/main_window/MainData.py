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
            Get the company names and load history data one by one
        """
        #getting company names and symbols
        companySymbols = []
        companyNames = []

        success,dMessage,dataset = self.findTop10Gainers()

        if not success or not dataset:
            return False, dMessage or "No gainers data found", (None, None)


        for item in dataset:
            if item and item.get('symbol'):
                companyNames.append(item.get('name', ''))
                companySymbols.append(item.get('symbol'))

        if not companySymbols:
            return False,"Company Names Cannot be Empty ! ",(None,None)
        
        
        closePrice_dataset = []
        valid_symbols = []
        
        for companySymbol in companySymbols:
            format_dataset = []

            success,dMessage,dataset = self.db_read.getting_past_close_prices(companySymbol=companySymbol)

            if not success or not dataset:
                continue
            
            for item in dataset:
                if item and item.get('trade_date') is not None:
                    dt = item['trade_date']
                    date_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)
                    format_dataset.append({
                        "date": date_str,
                        'close_price': item.get('close_price', 0)
                    })
            
            if format_dataset:
                closePrice_dataset.append(format_dataset)
                valid_symbols.append(companySymbol)

        if not closePrice_dataset:
            return False,"Close Price Dataset Cannot be Empty !",(None,None)
        
        return True,"Successfully Retrieved !",(closePrice_dataset,valid_symbols)


    def getSectorWiseInvestmentsDetails(self,force_refresh=False):
        """Return sector wise investsments data.\n
            Gives sector based total volume
        """
        #check if we have the cash files
        if not force_refresh:
            cashed_data = self._load_from_cash()

            if cashed_data:
                return True,"Successfully calculated the volume (from cashe)",cashed_data

        # Fast 1-query optimization
        fast_success, fast_msg, fast_volumes = self.db_read.getting_all_sector_volumes()
        if fast_success and fast_volumes:
            self._save_to_cash(fast_volumes)
            return True, "Successfully Calculated the volume", fast_volumes
            
        #getting industry names
        success,dMessage,dataset = self.readIndustryGroupName()

        #getting company names according to the sectors
        sectorBasedCompany = {}
        sectorBasedVolume = {}
        

        if not success:
            return success,dMessage,None
        
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
        """Load cashed data if it's still valid"""
        try:
            if os.path.exists(self.CASH_FILE):
                with open(self.CASH_FILE,'r') as f:
                    cash_data = json.load(f)

                cashe_time = datetime.fromisoformat(cash_data['timestamp'])

                if datetime.now() - cashe_time < self.CASH_DURATION:
                    return cash_data['data']
                
        except Exception as e:
            pass

        return None
    
    def _save_to_cash(self,data):
        """Save data to cash File"""
        try:
            cashe_data = {
                'timestamp':datetime.now().isoformat(),
                'data':data
            }

            os.makedirs(os.path.dirname(self.CASH_FILE), exist_ok=True)
            with open(self.CASH_FILE,'w') as f:
                json.dump(cashe_data,f)
        
        except:
            pass
            


