import os
import mysql.connector
from dotenv import load_dotenv


class DBConnection():
    def __init__(self):
        """Load environmental variables and Initialize the state"""
        #load env variables
        load_dotenv()

        #pass the values
        try:
            self.host = os.getenv("DB_HOST")
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASSWORD")
            self.database = os.getenv("DB_NAME")

            #holds the active connection
            self.connection = None

        except Exception as e:
            raise Exception(f"Error loading environment variables: {str(e)}")
        
    
    def connect(self):
        """Create Connection it doesn't exists"""
        if not self.connection or not self.connection.is_connected():
            try:
                #make the connection
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database= self.database
                )

                return True,"Connection Successful!",self.connection

            except Exception as e:
                return False,f"Error: {str(e)}",None
            
        return True,"Connection Already Exists !",self.connection
    
    def close(self):
        """Close the connection safely"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None

            
