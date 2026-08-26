from src.databases.query import QueryOperation
import pandas as pd
import numpy as np

class InsertData():
    def __init__(self):
        #making query object
        self.query_obj = QueryOperation()

    def insert_csv_file(self,file_path:str)->tuple[bool,str,list[any]]:
        """Insert CSV file into MySQL Database"""
        if not file_path:
            return False,"File Location Cannot be Empty !",None
        
        #load the dataset
        try:
            df = pd.read_csv(file_path)
        
        except Exception as e:
            return False,"Error : "+str(e),None
        
        #clean the dataset
        df = df.where(pd.notnull(df),None)

        #get all non-zero close prices
        non_zero_closes = df[df['close'] != 0.0]['close']

        if len(non_zero_closes) > 0:
            close_mean = non_zero_closes.mean()
            close_std = non_zero_closes.std()
            use_random = True

        else:
            use_random = False #fallback if all close are zero

        #convert the dataframe into list of tuples
        data_values = []

        for index,row in df.iterrows():
            if row['close'] == 0.0:
                if use_random:
                    random_close = round(np.random.normal(close_mean, close_std), 2)
                    row['close'] = max(random_close, 0.01)  

                else:
                    row['close'] = round(row['open'], 2)  

            data_values.append((
                row['trade_date'],
                row['symbol'],
                row['name'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume'],
                row['turnover'],
                row['pct_change']
            ))
            
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

        return True, "Successfully inserted CSV file data", None




        
