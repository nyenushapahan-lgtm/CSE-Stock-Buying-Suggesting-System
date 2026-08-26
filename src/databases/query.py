from src.databases.connection import DBConnection
from typing import Tuple, List, Any, Optional


class QueryOperation():
    def __init__(self):
        #make the connection object
        connection_obj = DBConnection()

        try:
            #make the connection
            success, dMessage, self.conn = connection_obj.connect()

            if not success:
                raise Exception(f"Error connecting to database: {dMessage}")
            
        except Exception as e:
            self.conn = None
            raise Exception(f"Error initializing QueryOperation: {str(e)}")
    
    def readSQL(self,query)->Tuple[bool,str,list[Any]]:
        """Read MySQL Tables and Return All the Data"""
        if not self.conn:
            return False,"Database Connection Does not Exists!", []
        
        cursor = None

        try:
            #creating cursor object
            cursor = self.conn.cursor(dictionary=True)

            #Execute the query
            cursor.execute(query)
            
            #get the result
            data = cursor.fetchall()

            return True,"Successfully Retrived the Data!",data
        
        except Exception as e:
            return False,"Unsuccessful "+str(e),[]
        
        finally:
            if cursor:
                cursor.close()
    
    def applyFilterForSQL(self,query,values)->Tuple[bool,str,list[Any]]:
        """Applying Filters when reading MySQL Data"""
        if not self.conn:
            return False, "Database connection does not exists !", None
        
        cursor = None

        try:
            #creating cursor object
            cursor = self.conn.cursor(dictionary=True)

            cursor.execute(query,values)

            data = cursor.fetchall()

            return True,"Successfully Retrieved the Data !",data

        except Exception as e:
            return False, "Unsuccessful "+str(e), []
        
        finally:
            if cursor:
                cursor.close()

    def insertSQL(self,query,values)->Tuple[bool,str,list[Any]]:
        """Insert data into mysql database"""
        if not self.conn:
            return False,"Database connection does not exists !",None
        
        cursor = None

        try:
            #creating cursor object
            cursor = self.conn.cursor(dictionary=True)

            #execute the query
            cursor.execute(query,values)

            #commit the changes
            self.conn.commit()

            return True,"Successfully Inserted the data !",None
        
        except Exception as e:
            if self.conn:
                self.conn.rollback()

            return False,"Unsuccessful"+str(e),None
        
        finally:
            if cursor:
                cursor.close()

    def insertCSV(self,query:str,values:list)->Tuple[bool,str,list[Any]]:
        """Insert CSV dataset in to mysql database"""
        if not self.conn:
            return False,"Database Connection does not exists !",None
        
        cursor = None

        try:
            #create cursor object
            cursor = self.conn.cursor(dictionary=True)

            #execute the query
            cursor.executemany(query,values)

            #commit the connection
            self.conn.commit()

            return True,"Successfully Data added to the database !",None
        
        except Exception as e:
            if self.conn:
                self.conn.rollback()

            return False,"Error : "+str(e),None
        
        finally:
            if cursor:
                cursor.close()
    
    def deleteSQL(self,query:str,values:tuple)->Tuple[bool,str,None]:
        """Delete MySQL Data"""
        if not self.conn:
            return False,"Database Connection Does not Exists !",None
        
        cursor = None

        try:
            #create cursor object
            cursor = self.conn.cursor(dictionary=True)

            #execute the query
            cursor.execute(query,values)

            #comit the connection
            self.conn.commit()

            return True,"Successfully Deleted the data !",None

        except Exception as e:
            if self.conn:
                self.conn.rollback()

            return False,"Deletion Error : "+str(e),None
        
        finally:
            if cursor:
                cursor.close()

            