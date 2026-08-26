import sys
import logging

class Logging():
    def __init__(self):  
        #basic consigurations
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("./log/app.log")
            ]
        )

        #create logger instance 
        self.logger = logging.getLogger(__name__)

    def debug_message(self,message):
        """Debug Message"""
        if message:
            self.logger.debug(msg=message)

    def dubug_message(self, message):
        """Alias for debug_message to support legacy calls"""
        self.debug_message(message)

    def error_message(self,message):
        """Error Message"""
        if message:
            self.logger.error(msg=message)
    
    def info_message(self,message):
        """Infor Message"""
        if message:
            self.logger.info(msg=message)
    
