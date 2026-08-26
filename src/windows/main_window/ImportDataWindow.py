import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox,QButtonGroup
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QDate
from src.services import handleThems
from PySide6.QtGui import QIcon, QPixmap

from src.services import logger
from resources.icons import resources_rc
from src.services.DataDownloadThread import DataDownloadThread
from src.services.CSEDataDownload import CSEDataDownload
from src.services.main_window.MainData import MainData
import os
from src.services.DB_Handler.DeleteData import DeleteOperation

class ImportDataWindow():
    """
    This is for data importing handles from this class and manage it. 
    """
    def __init__(self):
        self.import_data_window = None

        try:
            #make logger instance
            self.logMsg = logger.Logging()

            #load the ui
            self.loader = QUiLoader()

            ui_file_path = "./resources/ui_files/importing_data.ui"
            ui_file = QFile(ui_file_path)

            #open the file
            if not ui_file.open(QFile.ReadOnly):
                QMessageBox.critical(None,"File Error","Ui File Cannot be Opened !")

                #logger message
                self.logMsg.error_message(message="Ui file Cannot be Opened !")

                sys.exit(-1)

            #load the ui
            self.import_data_window = self.loader.load(ui_file)
            ui_file.close()

            #add window icon to the main window
            file_path = "./resources/icons/icon.png"
            self.import_data_window.setWindowIcon(QIcon(file_path))

            #object for maindata method
            self.mainData_obj = MainData()

            #----------------------------------------------------------------------------------
            #load the items
            try:
                self.startDateWidget = self.import_data_window.startDateWidget
                self.endDateWidget = self.import_data_window.endDateWidget
                self.progressBar = self.import_data_window.downloadingProgressBar
                self.importDataBtn = self.import_data_window.importDataBtn

                self.logMsg.info_message(message="Successfully Selected the items ! ")
            
            except Exception as e:
                self.logMsg.error_message(message="Error : "+str(e))
            
            #set progress bar progress 0
            self.progressBar.setValue(0)

            #when click the btn
            self.importDataBtn.clicked.connect(self.start_download)

        
        except Exception as e:
            self.logMsg.error_message(message="Error : "+str(e))

    def start_download(self):
        """Call this function when the user clicks 'start/Import' """

        #pass the data to download funtion
        start_date = self.startDateWidget.date().toString("yyyy-MM-dd")
        end_date = self.endDateWidget.date().toString("yyyy-MM-dd") 


        if not all((start_date,end_date)):
            return self.logMsg.error_message(message="Start date and End Date Cannot be Empty ! ")
        
        #disable the button 
        self.importDataBtn.setEnabled(False)

        self.download_thread = CSEDataDownload(start_date=start_date,end_date=end_date)

        #connect the signals
        self.download_thread.progress_bar.connect(self.update_progress_bar)
        self.download_thread.download_finished.connect(self.on_download_complete)

        #start the thread
        self.download_thread.start()

        #start the deletion
        #self.__clearTheDataMonthBack()

    def update_progress_bar(self, value):
        """This updates the UI every time the thread emits a new percentage"""
        self.progressBar.setValue(value)

        if int(value) == 100:
            QMessageBox.information(self.import_data_window,"Data Download Status","Successfully Download the Data !")

            self.logMsg.info_message(message="Successfully Download the Data !")
            
            self.close()

    def on_download_complete(self, data_dict):
        """This runs when the thread hits 100%"""

        #create data folder if is does not exists
        save_folder = 'resources/data'
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)

        for ticker,df in data_dict.items():
            file_path = f"{save_folder}/{ticker}_historical.csv"

            #write data to csv file
            df.to_csv(file_path,index=False)
            self.logMsg.info_message(f"Saved {ticker} to {file_path}")

        QMessageBox.information(None, "Success", f"Successfully downloaded data for {len(data_dict)} stocks!")

        #self.close()

    def __clearTheDataMonthBack(self):
        """This method clear the data one month before"""
        try:
            #create an object for delete operation
            query_obj = DeleteOperation()

            #call delete operation
            success,dMessage,_ = query_obj.deleteHistoricalPriceData()

            if not success:
                self.logMsg.dubug_message(message=dMessage)

            #log message
            self.logMsg.info_message(message=dMessage)
            
        except Exception as e:
            dMessage = "Error in ImportDataWindow-ClearTheDataMonthBack : "+str(e)
            self.logMsg.error_message(message=dMessage)

    def setLatestDate(self):
        """Set the Latest date at the start date"""
        try:
            success,dMessage,qDateObj = self.mainData_obj.FindLatestDate()
            
            if not success:
                return self.logMsg.error_message(message=dMessage)
            
            #set the date at import function
            self.startDateWidget.setDate(qDateObj)

            #send log message
            self.logMsg.info_message(message="Starting date set as the current Date !")
            
        except Exception as e:
            QMessageBox.critical(None,"Error",str(e))

            self.logMsg.error_message(message=str(e))

    
    def setCurrentDate(self):
        """Set current date as end date"""
        current_date = QDate.currentDate()

        #set the ending date as current date
        self.endDateWidget.setDate(current_date)

    def show(self):
        self.import_data_window.show()

        #set latest day when open the application
        self.setLatestDate()

        #set the current day as end date
        self.setCurrentDate()

    def close(self):
        self.import_data_window.close()