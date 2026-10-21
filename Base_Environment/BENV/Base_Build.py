import os
from cryptography.fernet import Fernet

# ___Generic Import Statements___
import mysql.connector,\
    openpyxl,\
    sys,\
    traceback,\
    inspect,\
    calendar,\
    subprocess,\
    math,\
    datetime as dt,\
    time as PyTime,\
    json
# win32com.client as win32,


#_________ Qt Imports _________
from PyQt5 import \
    QtCore, \
    QtGui, \
    QtWidgets,  \
    uic
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QTableWidgetItem as T_itm
from PyQt5.QtWidgets import \
    QComboBox, \
    QCompleter,\
    QShortcut, \
    QAction


from PyQt5.QtCore import \
    QSortFilterProxyModel,\
    Qt,QCoreApplication, \
    QDate, \
    QByteArray, \
    QBuffer,\
    QIODevice
from PyQt5.QtCore import \
    QSortFilterProxyModel,\
    Qt,QCoreApplication, \
    QDate, \
    QByteArray, \
    QBuffer,\
    QItemSelectionModel,\
    QIODevice
from PyQt5.QtGui import \
    QPixmap, \
    QImage,\
    QKeySequence,\
    QImageReader,\
    QColor,\
    QFont,\
    QStandardItemModel,\
    QDoubleValidator

from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel
from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtCore import Qt, pyqtSignal
from collections import defaultdict
from PyQt5 import QtCore, QtGui, QtWidgets
from num2words import num2words

#_________ DateTime Imports _________
from datetime import datetime as ddt,\
    date,\
    timedelta,\
    time


clipboard = QApplication.clipboard()


# ___Exception Handling___
def Show_Error(title, message):#Show an error Message
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Warning)
    error_box.setWindowTitle(title)
    error_box.setText(message)
    error_box.exec_()


Exception_Dict = {
"PermissionError:" : "Please Close the exported Output file  and try again..!"
}

def Exception_Handle(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_info = traceback.format_exc()
            calling_frame = inspect.currentframe().f_back
            file_name = calling_frame.f_code.co_filename
            line_number = calling_frame.f_lineno

            error_message = "Dear User...!\n"
            try:
                if "PermissionError:" in exc_info:
                    error_message += Exception_Dict["PermissionError:"]
            except:
                error_message += "UnKnown Error : Please contact Support"

            error_message +="\n\n----------------------------------------\n\n"

            error_message += (f"Error in function {func.__name__} called from {file_name} line {line_number}"
                              f"\n\n----------------------------------------\n\n"
                              f"\n{exc_info}")
            print(error_message)
            Show_Error("ERROR:", error_message)
    return wrapper

def Window_Holder(window):
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window.destroyed.connect(app.quit)
    app.exec_()

app = QtWidgets.QApplication(sys.argv)

@Exception_Handle
def Use_Root_Dir():
    os.chdir(ldir)

#___Time Functions___
@Exception_Handle
def Mysql_Date(inp):
    try:
        dateform = ddt.strptime(inp, '%d/%m/%Y')
    except:
        dateform = ddt.strptime(inp, '%d-%m-%Y')
    return dateform.strftime('%Y-%m-%d')

Cur_Date = ddt.today()
Cur_date_M = Cur_Date.strftime("%m")
Cur_Date_NF = Cur_Date.strftime("%d-%m-%Y")
Cur_Date_SQL = Cur_Date.strftime("%Y-%m-%d")
Cur_Date_DD =  Cur_Date.strftime("%d")
Cur_Date_MM =  Cur_Date.strftime("%m")
Cur_Date_YR =  Cur_Date.strftime("%Y")
Cur_Date_MY = Cur_Date.strftime("%m-%Y")
Cur_Date_YM = Cur_Date.strftime("%Y-%m")
Cur_Date_MMW =  Cur_Date.strftime("%B")
sqlformat = 'yyyy-MM-dd'
Cur_Date_NFR = Cur_Date.strftime("%d%m%H%M")

@Exception_Handle
def Nomrmal_Date(inp):
    return inp.strftime('%d-%m-%Y')

@Exception_Handle
def Time_Difference_Behind(date2_str,date1_str):
    time_format = "%H:%M"

    date1 = datetime.strptime(date1_str, time_format)
    date2 = datetime.strptime(date2_str, time_format) + timedelta(days=1)  # Add one day to the second date

    time_difference = date2 - date1
    return time_difference.total_seconds() / 3600

@Exception_Handle
def Qtdate_strt(inp):
    Date_temp = inp.date().toString(Qt.ISODate)
    Date_splt = Date_temp.split("-")
    Date_Join = Date_splt[2],Date_splt[1],Date_splt[0]
    Date_Dispy = "-".join(Date_Join)
    # Inv_Mtr.OQL_PreviewPODate.setText(Date_Dispy)
    return Date_Dispy

@Exception_Handle
def Nf_Date(inp):
    return inp.strftime('%d-%m-%Y')

@Exception_Handle
def ConvertCurrencyToWords(amount):
    # Split the amount into rupees and paise
    try:
        rupees, paise = str(amount).split('.')
        # Convert rupees to words
        rupees_words = num2words(int(rupees))
        # Convert paise to words
        if paise == '00' or paise =='0':
            paise_words = 'zero'
        else:
            paise_words = num2words(int(paise))
        # Format the result
        if paise == '00' or paise =='0':
            result = f"{rupees_words} rupees only"
        else:
            result = f"{rupees_words} rupees and {paise_words} paise only"
        
        return result.title()
    except:pass


parts =  os.getcwd().split(os.sep)
if "MODULES" in parts:
    ldir = os.sep.join(parts[:parts.index("MODULES")])  # take everything before "Modules"
else:
    ldir = os.getcwd()


key = 'mQFegoZL-vAfaf0sA6RqGQd9eZCE97T4SZae6TWRtmA='
cipher = Fernet(key)


with open(fr"{ldir}\CONFIG\CONFIG.enc", "rb") as f:
    encrypted_data = f.read()

ConfigData = json.loads(cipher.decrypt(encrypted_data).decode("utf-8"))

# ConfigData['Primary']['database'] = 'twink_static_erp'
# print((ConfigData['Primary']))
# print(ConfigData['Primary']['database'])


# ConfigData['Primary']['database'] = 'spark_lite'
ConfigData['Primary']['database'] = 'twink_erp'
ConfigData['Primary']['db_host'] = "localhost"
ConfigData['Primary']['db_user'] = "root"
# ConfigData['Primary']['db_pass'] = "MSeGa@1109"
# ConfigData['Primary']['db_pass'] = "Santha@8122"
ConfigData['Primary']['db_pass'] = "Admin@123"
ConfigData['Primary']['db_port'] = '3306'

# print(type(ConfigData))
# print('confic',ConfigData)

