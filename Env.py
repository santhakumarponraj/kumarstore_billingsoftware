from Base_Environment.BENV import *
from ICONS import ICONS_rc
from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
from collections import defaultdict
from PyQt5 import QtCore, QtGui, QtWidgets
from MODULES.INVOICE_MASTER import UI_InvoiceMaster # Ui_MainWindow_InvoiceMaster
from MODULES.ITEM_MASTER import UI_ItemMaster # Ui_MainWindow_ItemMaster
from MODULES.PURCHASE_MASTER import UI_PurchaseMaster #Ui_MainWindow_Purchase
from MODULES.REGISTER import UI_Payment # Ui_MainWindow_Payment
from MODULES.REGISTER import UI_Register # Ui_MainWindow_Register
import UI_BaseWin # Ui_MainWindow_BaseWin
from datetime import datetime
import os


# UI to .py Method Begins Here

Inv_Mtr = QtWidgets.QMainWindow()
Inv_MtrUI = UI_InvoiceMaster.Ui_MainWindow()
Inv_MtrUI.setupUi(Inv_Mtr)

Itm_Mtr= QtWidgets.QMainWindow()
Itm_MtrUI = UI_ItemMaster.Ui_MainWindow_ItemMaster()
Itm_MtrUI.setupUi(Itm_Mtr)

Twink = QtWidgets.QMainWindow()
TwinkUI = UI_BaseWin.Ui_MainWindow_BaseWin()
TwinkUI.setupUi(Twink)

Inv_Reg = QtWidgets.QMainWindow()
Inv_RegUI = UI_Register.Ui_MainWindow_Register()
Inv_RegUI.setupUi(Inv_Reg)

Prc_Mtr = QtWidgets.QMainWindow()
Prc_MtrUI = UI_PurchaseMaster.Ui_MainWindow_Purchase()
Prc_MtrUI.setupUi(Prc_Mtr)

payUI = QtWidgets.QMainWindow()
payUIUI = UI_Payment.Ui_MainWindow_Payment()
payUIUI.setupUi(payUI)


# #--- UI Imports ---
# Itm_Mtr = uic.loadUi(fr'{os.path.dirname(os.path.abspath(__file__))}\MODULES\ITEM_MASTER\UI_ItemMaster.ui')
# # Inv_Mtr = uic.loadUi(fr'{os.path.dirname(os.path.abspath(__file__))}\MODULES\INVOICE_MASTER\UI_InvoiceMaster.ui')
# Twink = uic.loadUi(fr'{os.path.dirname(os.path.abspath(__file__))}\UI_BaseWin.ui')
# Inv_Reg = uic.loadUi(fr'{os.path.dirname(os.path.abspath(__file__))}\MODULES\REGISTER\UI_Register.ui')
# Prc_Mtr = uic.loadUi(fr'{os.path.dirname(os.path.abspath(__file__))}\MODULES\PURCHASE_MASTER\UI_PurchaseMaster.ui')
# payUI = uic.loadUi(fr"{os.path.dirname(os.path.abspath(__file__))}\MODULES\REGISTER\UI_Payment.ui")





#--- Keyboard Event Functions ---
class KeyFilter(QObject):
    @Exception_Handle
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # print("Key pressed:", event.text(), "Code:", event.key())
            focused = QApplication.focusWidget()
            chain = []
            w = focused
            while w is not None:
                name = w.objectName() if w.objectName() else w.__class__.__name__
                # chain.append(name)
                chain.append(w)
                w = w.parentWidget()
            if (Inv_MtrUI.IQTB_BillList in chain
                and (Inv_MtrUI.IQTB_BillList.currentColumn() == 0)
                and (event.key() == Qt.Key_Up or event.key() == Qt.Key_Down) and
                Inv_MtrUI.IQTB_BillList.state() == Inv_MtrUI.IQTB_BillList.EditingState
            ):
                Inv_MtrUI.IQTB_BillList.blockSignals(True)
                Inv_MtrUI.IQTB_ProductList.setFocus(True)
                Inv_MtrUI.IQTB_BillList.blockSignals(False)

                return False




            if (
                obj == Prc_MtrUI.PurchaseTable
                and event.type() == QEvent.KeyPress
                and (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter)
                and Prc_MtrUI.PurchaseTable.currentColumn() < 7
            ):
                index = Prc_MtrUI.PurchaseTable.currentIndex()
                Prc_MtrUI.PurchaseTable.setCurrentCell(index.row(), index.column() + 1)
                Prc_MtrUI.PurchaseTable.edit(Prc_MtrUI.PurchaseTable.currentIndex())
                Prc_MtrUI.PurchaseTable.activated.emit(index)
                
                return True

        return super().eventFilter(obj, event)

filter = KeyFilter()
app.installEventFilter(filter)


#--- Fetch Row_TableView  ---
def get_row_values(tableView, row):
    model = tableView.model()
    return [model.data(model.index(row, col), Qt.DisplayRole) for col in range(model.columnCount())]

def FY_Gen(date_val):

    if date_val.month >= 4:
        start_year = date_val.year
        end_year = date_val.year + 1
    else:  # January to March
        start_year = date_val.year - 1
        end_year = date_val.year

    return f"{start_year}-{end_year}"

Fetch_CustomerID = lambda : DB_Fetch('''select concat("AstA-",lpad(greatest(count(*)+1,1),3,0)) from customer_info''',False,"LOE")[0]
Fetch_InvoiceNumber = lambda : DB_Fetch(fr'''select count(*)+1 from invoice_master where fy = '{FY_Gen(Cur_Date)}' and
                                          active_status in ('Y','N') ''',False,"LOE")[0]

Fetch_CustomerNo = lambda : DB_Fetch(""" select distinct phone_no from customer_info """,False,"LOE")

paymMode =['Cash','UPI','Card']
saleManlst = ['A','B','C']

class FocusHighlighter(QObject):
    @Exception_Handle
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if "IQTB"  in QApplication.focusWidget().objectName():
                obj.setStyleSheet(r'''
                /* Table container (both Widget & View) */
                QTableWidget, QTableView {
                    border: 2px solid #002B5B;
                    border-radius: 5px;
                }

                /* Selected items (active) */
                QTableWidget::item:selected,
                QTableView::item:selected {
                    color: black;
                    background-color: #a9c7f5;
                }

                /* Selected items (inactive / focus lost) */
                QTableWidget::item:selected:!active,
                QTableView::item:selected:!active {
                    color: black;
                    background-color: #a9c7f5;
                }
                ''')

            else:

                obj.setStyleSheet("border: 2px solid #002B5B ;  border-radius: 5px;")
            

        elif event.type() == QEvent.FocusOut:
            if QApplication.focusWidget() and "IQTB" not in QApplication.focusWidget().objectName():
                obj.setStyleSheet( '''
                    QSpinBox {
                    background-color: #f0f8ff;
                    border: 2px solid #0078d7;
                    border-radius: 6px;
                    padding: 2px 20px 2px 8px;
                    color: #003366;
                    font-size: 30px;
                    }
                    ''') # Reset to default
                
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter) and "QPB" in QApplication.focusWidget().objectName():
            try:obj.click()  # simulate button click
            except:pass
            return True  # stop further processing
        
        return False

highlighter = FocusHighlighter()

ProductList = lambda : DB_Fetch("select product_name from product_info where active_status <> 'D' ",False,"LOE")
ProductBarCodeList = lambda : DB_Fetch("select product_name,barcode,tamil_name from product_info where active_status <> 'D' order by product_name",False,"LOL")

ProductBarCodeListwithx = lambda x : DB_Fetch(fr"select product_name,barcode,tamil_name from product_info where active_status <> 'D' and product_name = '{x}' order by product_name",False,"LOL")



class ColorSqlModel(QSqlQueryModel):
    def data(self, index, role):
        if role == Qt.BackgroundRole and index.row() == 0:
            return QColor(220, 235, 255)
        return super().data(index, role)

def PrdTbl_PushData(tbl_name,tbl,sql):
    model = ColorSqlModel()
    model.setQuery(sql, dbod)
    if model.lastError().isValid():
        print("SQL Error:", model.lastError().text())
    tbl.setModel(model)
    models[tbl_name] = model

TAMIL_KEYS = [
    ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'ஊ'],
    ['எ', 'ஏ', 'ஐ', 'ஒ', 'ஓ', 'ஔ', 'ஃ'],
    ['க', 'ங', 'ச', 'ஞ', 'ட', 'ண'],
    ['த', 'ந', 'ப', 'ம', 'ய', 'ர'],
    ['ல', 'வ', 'ழ', 'ள', 'ற', 'ன'],
    ['ஷ', 'ஸ', 'ஹ', 'ஜ', 'க்ஷ', 'ஶ்ரீ'],
    ['்', 'ா', 'ி', 'ீ', 'ு', 'ூ', 'ெ'],
    ['ே', 'ை', 'ொ', 'ோ', 'ௌ']
]

BOTTOM_BUTTONS = ['Space', 'Backspace', 'Save', '⌫ Clear', 'Close']


class TamilKeyboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tamil Virtual Keyboard")
        self.setFixedSize(700, 550)

        self.init_ui()


    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # ---------------- TEXT BOX ----------------
        self.textbox = QTextEdit()
        self.textbox.setFont(QFont("Latha", 15))
        self.textbox.setFixedHeight(90)
        main_layout.addWidget(self.textbox)

        # ---------------- KEY GRID ----------------
        grid = QGridLayout()
        grid.setSpacing(10)

        key_font = QFont("Latha", 18)

        for row, keys in enumerate(TAMIL_KEYS):
            for col, key in enumerate(keys):
                btn = QPushButton(key)
                btn.setFont(key_font)
                btn.setFixedSize(70, 50)
                btn.clicked.connect(lambda _, k=key: self.key_pressed(k))
                grid.addWidget(btn, row, col)

        main_layout.addLayout(grid)

        # ---------------- BOTTOM BUTTONS ----------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        for label in BOTTOM_BUTTONS:
            btn = QPushButton(label)
            btn.setFixedHeight(42)
            btn.setFont(QFont("Segoe UI", 11))
            btn.clicked.connect(lambda _, t=label: self.handle_action(t))
            bottom_layout.addWidget(btn)

        main_layout.addLayout(bottom_layout)

    # ---------------- KEY ACTIONS ----------------
    def key_pressed(self, key):
        cursor = self.textbox.textCursor()
        cursor.insertText(key)
        

    def handle_action(self, action):
        cursor = self.textbox.textCursor()

        if action == 'Space':
            cursor.insertText(' ')

        elif action == 'Backspace':
            cursor.deletePreviousChar()

        elif action == '⌫ Clear':
            self.textbox.clear()

        elif action == 'Save':
            Itm_MtrUI.IQLE_TamilName.setText(self.textbox.toPlainText())
            
        elif action == 'Close':
            Itm_MtrUI.IQLE_TamilName.setText(self.textbox.toPlainText())
            self.close()
            self.textbox.clear()


tamilWindow = TamilKeyboard()


def getUIDndCP():
    return DB_Fetch("select product_id,cost_price from product_info",False,"DIC")

def getUIDndPurCost():
    return DB_Fetch("select product_id,purchase_price from product_info",False,"DIC")

def getUIDndMRP():
    return DB_Fetch("select product_id,mrp from product_info",False,"DIC")

