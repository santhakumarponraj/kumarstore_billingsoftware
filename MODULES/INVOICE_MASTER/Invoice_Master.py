from Env import *
from wcwidth import wcswidth
import win32print
import openpyxl 
from openpyxl.styles import Border, Side, Alignment, Font
from openpyxl.styles import Alignment
import os
import subprocess
from openpyxl.utils import get_column_letter
from escpos.printer import Usb, Network, Serial  # pick one based on your connection
from num2words import num2words
from datetime import datetime
import sys
import os
import ctypes
import subprocess


@Exception_Handle
def Invoice_Master_FN():
    print("------------Invoice Master Started-------------")
    # print(ldir)
    ui = Inv_MtrUI

    # print(,"========")


    print(ui.IQCB_AddOutstanding.isChecked(),"checking")

    global BillEdit,barcode_status 
    BillEdit,barcode_status = False,False
    PrdTbl = ui.IQTB_ProductList
    BilTbl = ui.IQTB_BillList

    global costPriceDict
    costPriceDict = getUIDndCP()

    global CustomerMobNo
    CustomerMobNo = Fetch_CustomerNo()


    @Exception_Handle
    def TimeUpdate():

        def is_admin():
            """Check whether the application is running with Administrator privileges."""
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception:
                return False

        def run_command(command):
            """Run a Windows command safely."""
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )

                return True, result.stdout

            except subprocess.CalledProcessError as e:

                error_msg = (
                    (e.stderr or "") +
                    (e.stdout or "")
                )

                return False, error_msg

        def sync_system_time():
            """Start Windows Time service and synchronize system clock."""

            print("Checking Windows Time Service (w32time)...")

            # Start Windows Time Service
            subprocess.run(
                ["net", "start", "w32time"],
                capture_output=True,
                text=True
            )

            print("Attempting to synchronize system clock...")

            # Force Windows time synchronization
            success, output = run_command(
                ["w32tm", "/resync"]
            )

            if success:

                print("\n[SUCCESS] Time synchronized successfully!")

                if output:
                    print(output.strip())

            else:

                print("\n[ERROR] Failed to synchronize system time.")

                if output:
                    print(
                        f"Windows Error Details:\n{output.strip()}"
                    )

        # -------------------------------------------------
        # CHECK ADMINISTRATOR PRIVILEGES & SYNC TIME
        # -------------------------------------------------
        if is_admin():
            sync_system_time()
        else:
            print("[INFO] Running without administrator privileges. System time synchronization skipped.")

    _bil_filter_timer = QtCore.QTimer()
    _bil_filter_timer.setSingleShot(True)

    def _execute_bil_filter(row, column, text):
        if column == 0:
            Update_PrdTbl(text)
            row, col = -1, 0
            if 'Product_Model' in models:
                index = models['Product_Model'].index(row, col)
                PrdTbl.setCurrentIndex(index)

    @Exception_Handle
    def BilTblFilter(row, column, text):
        if column == 0:
            _bil_filter_timer.stop()
            try:
                _bil_filter_timer.timeout.disconnect()
            except Exception:
                pass
            if text == "":
                _execute_bil_filter(row, column, text)
            else:
                _bil_filter_timer.timeout.connect(lambda: _execute_bil_filter(row, column, text))
                _bil_filter_timer.start(120)

    @Exception_Handle
    def setup_table_with_text_changes(table):
        print("setup_table_with_text_changes")
        class LetterEditDelegate(QStyledItemDelegate):
            textChanged = pyqtSignal(int, int, str)  # row, column, text

            def createEditor(self, parent, option, index):
                editor = super().createEditor(parent, option, index)
                if editor:  # Typically a QLineEdit
                    editor.textChanged.connect(
                        lambda text: self.textChanged.emit(
                            index.row(),
                            index.column(),
                            text
                        )
                    )
                return editor

        delegate = LetterEditDelegate(table)
        table.setItemDelegate(delegate)
        return delegate

    delegate = setup_table_with_text_changes(BilTbl)
    delegate.textChanged.connect(BilTblFilter)


    @Exception_Handle
    def Add_Item(index):
        # print("====Add Item===")
        global costPriceDict, costIndex

        data = get_row_values(PrdTbl, index.row())
        row = BilTbl.currentRow()

        item = QTableWidgetItem(str(data[1])) if ui.IQCB_UserLang.currentText() == "English" \
                            else QTableWidgetItem(str(data[2]))

        BilTbl.blockSignals(True)

        BilTbl.setItem(row, 0, item)
        temp = T_itm(str("1"))
        BilTbl.setItem(BilTbl.currentRow(), 1, temp)
        BilTbl.setItem(row, 2, QTableWidgetItem(str(data[4])))
        item = QTableWidgetItem(str(float(data[5])))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        BilTbl.setItem(row, 4, item)

        item = QTableWidgetItem(str(data[0]))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        BilTbl.setItem(row, 5, item)

        # Alias Column
        item = QTableWidgetItem(str(data[2])) if ui.IQCB_UserLang.currentText() == "English" \
            else QTableWidgetItem(str(data[1]))

        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        BilTbl.setItem(row, 6, item)

        costIndex = data[0]

        BilTbl.setFocus(True)
        BilTbl.setCurrentCell(row, 1)
        BilTbl.blockSignals(False)
        PrdTbl.selectionModel().clearSelection()


    @Exception_Handle
    def BillTbl_functionality(*args):
        # print("bill tbl fn")
        global barcode_status
        global costPriceDict

        col = BilTbl.currentColumn()
        row = BilTbl.currentRow()

        # Auto add when clicked enter - Bar Code Scanner
        if col == 0 and PrdTbl.model().rowCount() == 1:
            current_row_item = BilTbl.item(row, 0)
            already_filled = current_row_item is not None and current_row_item.text().strip() != ""

            if already_filled:  # ✅ Only auto-add if row is truly empty
                BilTbl.blockSignals(True)
                Add_Item(BilTbl.model().index(0, 0))
                BilTbl.blockSignals(False)
                Update_PrdTbl("")
                ui.IQLE_CostPrice.setText("Cost Price :    ")
                return
            else:
                Update_PrdTbl("")  # ✅ Row already has data, just reset PrdTbl and do nothing
                return

        # If changes in Qty or Price column, Calculate Amount
        if col == 1 or col == 2:
            if get_row_values(BilTbl, BilTbl.currentRow())[0]:
                frzItem = BilTbl.item(BilTbl.currentRow(), 0)
                if frzItem is None or frzItem.text().strip() == "":
                    BilTbl.setCurrentCell(BilTbl.currentRow(), 0)
                    return

                try:
                    BilTbl.blockSignals(True)

                    try:
                        qty_val  = round(float(BilTbl.item(row, 1).text()), 2)
                        price_val = round(float(BilTbl.item(row, 2).text()), 2)

                        BilTbl.setItem(row, 1, QTableWidgetItem(str(qty_val)))
                        BilTbl.setItem(row, 2, QTableWidgetItem(str(price_val)))
                    except:
                        show_info_msg("Input error", "Please enter valid number")
                        BilTbl.blockSignals(False)
                        return

                    amount_item = QTableWidgetItem(str(round(qty_val * price_val, 2)))
                    amount_item.setFlags(amount_item.flags() & ~Qt.ItemIsEditable)
                    BilTbl.setItem(row, 3, amount_item)

                    Calculate_Invoice_Values()
                    getCpforItem(row)

                    BilTbl.blockSignals(False)
                    BilTbl.setFocus(True)

                    # ✅ After Qty (col 1) — move to Price column
                    if col == 1:
                        BilTbl.setCurrentCell(row, 2)
                        return

                    # ✅ After Price (col 2) — reset PrdTbl FIRST, then move to next row
                    if col == 2:
                        Update_PrdTbl("")  # ✅ KEY FIX: Reset before setCurrentCell so col==0 trigger won't see rowCount==1
                        ui.IQLE_CostPrice.setText("Cost Price :    ")

                        if BilTbl.rowCount() == row + 1:  # Last row
                            rowItem = get_row_values(BilTbl, row)
                            if None not in rowItem and '' not in rowItem:
                                BilTbl.setRowCount(BilTbl.rowCount() + 1)

                        BilTbl.setCurrentCell(row + 1, 0)  # Move to next row
                        return

                except Exception as e:
                    print(e, "qty/price error")
                    BilTbl.blockSignals(False)
                    BilTbl.setFocus(True)

            return  # ✅ Always return after col 1/2 block

        # --- Table movement logic ---

        if col == 0 and BilTbl.hasFocus():
            BilTbl.setCurrentCell(BilTbl.currentRow(), BilTbl.currentColumn() + 1)
            ui.IQLE_CostPrice.setText("Cost Price :    ")

            try:
                frzItem = BilTbl.item(BilTbl.currentRow(), 0)
                if frzItem is None or frzItem.text().strip() == "":
                    BilTbl.setCurrentCell(BilTbl.currentRow(), 0)
            except Exception as e:
                print(e, "Enter")
                BilTbl.setCurrentCell(BilTbl.currentRow(), 0)

        elif col == 0 and not BilTbl.hasFocus() and BilTbl.rowCount() != BilTbl.currentRow() + 1:
            ui.IQLE_CostPrice.setText("Cost Price :    ")
            pass

        elif col == 1:
            if get_row_values(BilTbl, BilTbl.currentRow())[0]:
                BilTbl.setCurrentCell(BilTbl.currentRow(), BilTbl.currentColumn() + 1)

        elif barcode_status and col == 2:
            barcode_status = False
            Update_PrdTbl("")  # ✅ Reset PrdTbl for barcode path too
            ui.IQLE_CostPrice.setText("Cost Price :    ")
            if None not in get_row_values(BilTbl, BilTbl.rowCount() - 1):
                BilTbl.setRowCount(BilTbl.rowCount() + 1)
                BilTbl.setCurrentCell(BilTbl.rowCount() - 1, 0)
            else:
                BilTbl.setCurrentCell(BilTbl.rowCount() - 1, 0)

        else:
            if BilTbl.rowCount() == BilTbl.currentRow() + 1:
                rowItem = get_row_values(BilTbl, BilTbl.rowCount() - 1)
                if None not in rowItem and '' not in rowItem:
                    BilTbl.setRowCount(BilTbl.rowCount() + 1)
                    Update_PrdTbl("")
                    BilTbl.setCurrentCell(BilTbl.currentRow() + 1, 0)
                    ui.IQLE_CostPrice.setText("Cost Price :    ")
            else:
                BilTbl.setCurrentCell(BilTbl.currentRow() + 1, 0)
                if col == 2:
                    Update_PrdTbl("")  # ✅ Reset here too for safety
                    ui.IQLE_CostPrice.setText("Cost Price :    ")
    

    @Exception_Handle
    def round_up_any(n):
        i = int(n)
        return i if n == i else i + 1

    @Exception_Handle
    def Update_PrdTbl(filter):
        price = 'wholesale' if ui.IQCB_pricing.currentText() == "Wholesale" else "Retail"
        SQL_Product = fr''' SELECT product_id as ID, product_name as name, tamil_name as Tamil, uom as UOM, 
        {price} as Price,GST,cost_price FROM product_info WHERE active_status = "Y" 
        and (Product_name like "{filter}%" or barcode = "{filter}") order by Product_Name '''
        PrdTbl_PushData('Product_Model', PrdTbl, SQL_Product)

    @Exception_Handle
    def Calculate_Invoice_Values():
        temp = Fetch_Table_Values(BilTbl)
        
        try:
            if "" in temp[-1]:
                temp.pop(-1)
            ui.IQTE_NetQuantity.setText(str(sum(float(x[1]) for x in temp)))
            ui.IQTE_UniqueQuantity.setText(str(len(temp)))
            ui.IQLE_SubTotal.setText(str(round(sum(float(x[3]) for x in temp), 2)))

        except Exception as e:
            pass

        OP = defaultdict(lambda: {'count': 0, 'total': 0.0, 'GST': 0.0})
        for row in temp:
            try:
                key = row[4]
                OP[key]['count'] += 1
                OP[key]['total'] += float(row[3])
                OP[key]['GST'] += round( float(row[3]) - (float(row[3]) * 100 / (float(row[4]) + 100)), 2) #Reducing Tax from Amount    
                
            except:
                pass

        try:
            OP = [[k, v['count'], v['total'], v['GST']] for k, v in OP.items()]
            Push_Table_Values(ui.OQTB_Tax, OP, False)
            # print(OP)
        except Exception as e:
            print(e,"---")
            pass

    @Exception_Handle
    def getCpforItem(row):
        global costPriceDict
        costitem = BilTbl.item(row, 5)
        if costitem is not None:
            costIndex = costitem.text()
            if costIndex not in [None,""]:
                try:
                    ui.IQLE_CostPrice.setText( "Cost Price :    " + str(costPriceDict[int(costIndex)]))
                except Exception as e:
                    
                    costPriceDict = getUIDndCP()
                    ui.IQLE_CostPrice.setText( "Cost Price :    " + str(costPriceDict[int(costIndex)]))

            else:
                ui.IQLE_CostPrice.setText( "Cost Price :    ")

         
    @Exception_Handle
    def Update_customerDetails():

        BilTbl.blockSignals(True)
        ui.IQCB_PhoneNumber.blockSignals(True)

        try:
            temp = DB_Fetch(fr'''select name, address from customer_info 
            where phone_no ='{ui.IQCB_PhoneNumber.currentText()}' ''', False, "LOE")
            ui.IQLE_CustomerName.setDisabled(True)
            ui.IQLE_Address.setDisabled(True)
            ui.IQLE_CustomerName.setText(temp[0])
            ui.IQLE_Address.setText(temp[1])
            ui.IQCB_PhoneNumber.setStyleSheet("""
            QComboBox {
                background-color: lightgreen;
                border: 1px solid #4CAF50;
                padding: 0px;
            }

            QComboBox QLineEdit {
                background-color: lightgreen;
                border: none;
                padding: 2px;
                margin: 0px;
            }
            """)

            ui.IQPB_LoadCustomer.setEnabled(False)

        except Exception as e:
            print(e,"==Update_customerDetails==",temp)
            ui.IQLE_CustomerName.setDisabled(False)
            ui.IQLE_Address.setDisabled(False)
            ui.IQLE_CustomerName.setText("")
            ui.IQLE_Address.setText("")
            ui.IQCB_PhoneNumber.setStyleSheet("QComboBox { background-color: white; }")
            ui.IQPB_LoadCustomer.setEnabled(True)
            
            # ui.IQLE_Account.setText(str(0))
            pass

        BilTbl.blockSignals(False)
        ui.IQCB_PhoneNumber.blockSignals(False)

    @Exception_Handle
    def Load_NewCustomer():
        ui.IQCB_PhoneNumber.blockSignals(True)  
        
        if len(ui.IQCB_PhoneNumber.currentText()) == 10:
            value = {
                'cid': Fetch_CustomerID(),
                'phone_no': ui.IQCB_PhoneNumber.currentText(),
                'name': ui.IQLE_CustomerName.text(),
                'address': ui.IQLE_Address.text(),
                'wholesale': True if ui.IQCB_pricing.currentText() == "Wholesale" else False
            }
            DB_Push_Dict(value, 'customer_info', False)

            Show_Msg_Infomation("Customer Addition", "New Customer Added Successfully")


            ui.IQCB_PhoneNumber.clear()
            ui.IQCB_PhoneNumber.addItem(value["phone_no"])
            ui.IQCB_PhoneNumber.setEnabled(False)

            ui.IQLE_Address.setReadOnly(True)
            ui.IQLE_CustomerName.setReadOnly(True)
            ui.IQPB_LoadCustomer.setEnabled(False)

            global CustomerMobNo
            CustomerMobNo = Fetch_CustomerNo()

        else:
            Show_Msg_Infomation("Input Error", "Please enter valid Mobile Number")
        
        ui.IQCB_PhoneNumber.blockSignals(False)

    @Exception_Handle
    def Calculate_NetAmount():
        try:
            Account = float(ui.IQLE_Account.text()) if ui.IQCB_AddOutstanding.isChecked() else 0
        except:
            Account = 0
        try:
            Discount = float(ui.IQLE_Discount.text())
        except:
            Discount = 0

        if ui.IQLE_SubTotal.text() in [0 , 0.0 ,'0.0',"" ,None]:
            val = 0 + Account - Discount
            
        else:
            val = float(ui.IQLE_SubTotal.text()) + Account - Discount

        val = int(val) + (val % 1 > 0)
        ui.IQLE_TotalAmount.setText(str(round(val, 0)))
        ui.IQTE_NetAmount.setText(str(round(val, 0)))


        try:
            Rcvd = float(ui.IQLE_RcvdAmount.text())
        except:
            Rcvd = 0
        try:
            ui.IQLE_BalAccount.setText(str(round(Rcvd - float(ui.IQLE_TotalAmount.text()), 0)))
        except:
            pass

    @Exception_Handle
    def Calculate_Balance():
        try:
            Rcvd = float(ui.IQLE_RcvdAmount.text())
        except:
            Rcvd = 0
        try:
            
            ui.IQLE_BalAccount.setText(str(round(Rcvd - float(ui.IQLE_TotalAmount.text()), 0)))
        except:
            pass

        # if ui.IQLE_RcvdAmount.text() != "" and len(Fetch_Table_Values(BilTbl)) > 0:
        #     ui.IQPB_SavePrint.setEnabled(True)
        #     ui.IQPB_Save.setEnabled(True)

        # else:
        #     ui.IQPB_SavePrint.setEnabled(False)
        #     ui.IQPB_Save.setEnabled(False)

    @Exception_Handle  #workin Excel
    def Bill_Generating_Invoice():
        global BillEdit
        InvData = Fetch_Table_Values(BilTbl)
        if ['', '', '', '', '', '',''] in InvData:
            InvData.remove(['', '', '', '', '', '',''])
        wb = openpyxl.load_workbook(fr"{ldir}\Invoive.xlsx")
        # print(ldir)

        if ui.IQCB_PhoneNumber.currentText() not in [None,"","NA"]:
            ws = wb['CData']

            ws['B4'] = ui.IQSB_InvNo.text()
            ws['B5'] = datetime.now().strftime(f'%d-%m-%Y %I:%M %p')
            

            # ws['B5'] = ui.IQDE_InvDate.date().toString("dd-MM-yyyy")

            ws['B6'] = ui.IQLE_CustomerName.text()
            ws['B7'] = ui.IQCB_PhoneNumber.currentText()

            ws.row_dimensions[9].height = 19

            row = 10

            wb.remove(wb["Data"])

        else:
            ws = wb['Data']
            ws['B4'] = ui.IQSB_InvNo.text()
            # date_str = self.ui.IQDE_InvDate.date().toString("yyyy-MM-dd")
            # ws['B5'] = datetime.now().strftime('%d-%m-%Y %I:%M %p')

            # ws['B5'] = ui.IQDE_InvDate.date().toString("dd-MM-yyyy")

            ws['B5'] = datetime.now().strftime(f'%d-%m-%Y %I:%M %p')

            

            ws.row_dimensions[7].height = 19

            row = 8
            wb.remove(wb["CData"])


        subtotal = float(ui.IQLE_SubTotal.text())
        discAmt = 0 if ui.IQLE_Discount.text() == "" else float(ui.IQLE_Discount.text())
        rcvddAmt = 0 if ui.IQLE_RcvdAmount.text() == "" else float(ui.IQLE_RcvdAmount.text())
        outstndAmt = float(ui.IQLE_Account.text()) if ui.IQCB_AddOutstanding.isChecked() else 0

        


        for name,qty,rate,amt,gst,uid,aliasname in InvData:
            if ui.IQCB_UserLang.currentText() == ui.IQCB_BillLang.currentText():
                ogName = name
            else:
                ogName = aliasname
            amount = round(float(amt), 0)
            qty_s = f"{float(qty):.2f}".rstrip('0').rstrip('.')
            ws.row_dimensions[row].height = 19

            ws[fr"A{row}"].font = Font(size=10,bold=True)
            
            ws[fr"A{row}"] = ogName
            ws[fr"A{row}"].alignment = Alignment(horizontal='left', vertical='center')
            ws[fr"B{row}"] =  f"{float(qty_s):.2f}"#qty_s
            ws[fr"B{row}"].alignment = Alignment(horizontal='center', vertical='center')
            ws[fr"C{row}"] = f"{float(rate):.2f}"
            ws[fr"C{row}"].alignment = Alignment(horizontal='left', vertical='center')
            ws[fr"D{row}"] = f"{float(amount):.2f}"
            ws[fr"D{row}"].alignment = Alignment(horizontal='left', vertical='center')


            row = row+1

        if ui.IQCB_AddOutstanding.isChecked(): #Customer there
            netTotal = round_up_any(subtotal + outstndAmt - rcvddAmt - discAmt)
            
        else:
            netTotal = round_up_any(subtotal - discAmt - rcvddAmt)

        thick_dashed = Side(style="mediumDashed")

        ws.row_dimensions[row].height = 18

        row = row+1
        drows = row
        
        ws.merge_cells(fr"A{row}:B{row+1}")
        ws[fr"A{row}"] = fr"Items : {ui.IQTE_UniqueQuantity.toPlainText()}  Subtotal : "

        ws[fr"A{row}"].alignment = Alignment(horizontal="left", vertical="center")

        
        ws.merge_cells(fr"C{row}:D{row+1}")
        ws[fr"C{row}"].font = Font(size=18,bold=True)
        ws[fr"C{row}"] = fr"{round_up_any(subtotal):.2f}"
        ws[f"C{row}"].alignment = Alignment(horizontal="right", vertical="center")

        ws[fr"A{row}"].border = Border(top=thick_dashed)
        ws[fr"B{row}"].border = Border(top=thick_dashed)
        ws[fr"C{row}"].border = Border(top=thick_dashed)
        ws[fr"D{row}"].border = Border(top=thick_dashed)

        drows = row+1

        if ui.IQCB_AddOutstanding.isChecked():
            drows +=1
            ws.row_dimensions[drows].height = 18
            ws.merge_cells(fr"A{drows}:B{drows}")
            ws[fr"A{drows}"] = fr"Outstanding Amount :"
            ws[fr"A{drows}"].font = Font(size=14)
            ws[f"A{drows}"].alignment = Alignment(horizontal="left", vertical="center")


            ws.merge_cells(fr"C{drows}:D{drows}")
            ws[fr"C{drows}"] = fr"+ {round_up_any(outstndAmt):.2f}"
            ws[fr"C{drows}"].font = Font(size=18,bold=True)
            ws[f"C{drows}"].alignment = Alignment(horizontal="right", vertical="center")

        if ui.IQLE_Discount.text() not in [0.0,""," ",0,None,"0.0","0.00",'0']:
            drows +=1
            ws.row_dimensions[drows].height = 18
            ws.merge_cells(fr"A{drows}:B{drows}")
            ws[fr"A{drows}"] = fr" Discount :"
            ws[fr"A{drows}"].font = Font(size=14)
            ws[f"A{drows}"].alignment = Alignment(horizontal="left", vertical="center")

            ws.merge_cells(fr"C{drows}:D{drows}")
            ws[fr"C{drows}"] = fr" - {round_up_any(discAmt):.2f}"
            ws[fr"C{drows}"].font = Font(size=18,bold=True)
            ws[f"C{drows}"].alignment = Alignment(horizontal="right", vertical="center")
        
        if ui.IQLE_RcvdAmount.text() not in [0.0,""," ",0,None,"0.0","0.00",'0']:
            drows +=1
            ws.row_dimensions[drows].height = 18
            ws.merge_cells(fr"A{drows}:B{drows}")
            ws[fr"A{drows}"] = fr"Received Amount : "
            ws[fr"A{drows}"].font = Font(size=14)
            ws[f"A{drows}"].alignment = Alignment(horizontal="left", vertical="center")

            ws.merge_cells(fr"C{drows}:D{drows}")
            ws[fr"C{drows}"] = fr"- {round_up_any(rcvddAmt):.2f}"
            ws[fr"C{drows}"].font = Font(size=18,bold=True)
            ws[f"C{drows}"].alignment = Alignment(horizontal="right", vertical="center")

        drows = drows + 1
        ws.merge_cells(fr"A{drows}:B{drows+1}")
        ws[fr"A{drows}"] = fr"NET TOTAL: "
        ws[fr"A{drows}"].alignment = Alignment(horizontal="left", vertical="center")

        ws.merge_cells(fr"C{drows}:D{drows+1}")
        ws[fr"C{drows}"] = fr"{round_up_any(netTotal):.2f}"
        ws[fr"C{drows}"].font = Font(size=18,bold=True)
        ws[f"C{drows}"].alignment = Alignment(horizontal="right", vertical="center")

        ws[fr"A{drows}"].border = Border(top=thick_dashed)
        ws[fr"B{drows}"].border = Border(top=thick_dashed)
        ws[fr"C{drows}"].border = Border(top=thick_dashed)
        ws[fr"D{drows}"].border = Border(top=thick_dashed)

        ws[fr"A{drows+1}"].border = Border(bottom=thick_dashed)
        ws[fr"B{drows+1}"].border = Border(bottom=thick_dashed)
        ws[fr"C{drows+1}"].border = Border(bottom=thick_dashed)
        ws[fr"D{drows+1}"].border = Border(bottom=thick_dashed)

        drows = drows + 2
        amountwd = round_up_any(float(ui.IQTE_NetAmount.toPlainText()))
        amtwords = num2words(int(amountwd), lang='en_IN') + ' Only'

        ws.merge_cells(fr"A{drows}:D{drows+1}")
        ws[fr"A{drows}"] = fr"Amount : {amtwords}"
        ws[fr"A{drows}"].alignment = Alignment(horizontal="center",vertical="center",wrap_text=True)
        ws[fr"A{drows+1}"].border = Border(bottom=thick_dashed)
        ws[fr"B{drows+1}"].border = Border(bottom=thick_dashed)
        ws[fr"C{drows+1}"].border = Border(bottom=thick_dashed)
        ws[fr"D{drows+1}"].border = Border(bottom=thick_dashed) 

        drows = drows+2
        ws.row_dimensions[drows].height = 25

        drows = drows+1
        ws.merge_cells(fr"A{drows}:D{drows}")
        ws[fr"A{drows}"] = "ஞாயிறு விடுமுறை"
        ws[fr"A{drows}"].alignment = Alignment(horizontal="center",vertical="center")

        last_row = ws.max_row
        last_col = ws.max_column
        end_col = get_column_letter(last_col)
        ws.print_area = f"A1:{end_col}{last_row}"
        wb.save(fr"{ldir}\Invoive0.xlsx")
        try:
            wb.close()
        except Exception:
            pass

        import win32com.client
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        file_path = fr"{ldir}\Invoive0.xlsx"
        try:
            wb_excel = excel.Workbooks.Open(file_path)
            wb_excel.PrintOut()
            wb_excel.Close(False)
        finally:
            excel.Quit()

    @Exception_Handle
    def Generate_Invoice(inp):
        global BillEdit

        InvData = Fetch_Table_Values(BilTbl)
        if ['', '', '', '', '', '',''] in InvData:
            InvData.remove(['', '', '', '', '', '',''])

        if len(InvData) >0 :
            if inp and get_info_msg("Print", "Do u want to take a Print"):
                Bill_Generating_Invoice()

            if not BillEdit:  # Generating new Invoice
                BillEdit = True
                valid_items = [d for d in InvData if d[0] != "" and d[-2] != ""]
                prod_ids = list({str(d[5]) for d in valid_items if str(d[5]).strip() != ""})
                prod_meta = {}
                if prod_ids:
                    try:
                        meta_rows = DB_Fetch(
                            fr"SELECT product_id, stock, uom, gst FROM product_info WHERE product_id IN ({','.join(prod_ids)})",
                            False, "LOL"
                        )
                        for r in meta_rows:
                            prod_meta[int(r[0])] = {'stock': float(r[1]), 'uom': r[2], 'gst': r[3]}
                    except Exception as e:
                        print(e, "meta prefetch")

                for data in valid_items:  # for every item in Bill Table - Should we group items brfore processing?

                    product_id = data[5]
                    product_name = data[0]
                    qty = float(data[1])
                    sprice = float(data[2])
                    total_amt = float(data[1]) * float(data[2])
                    gst = data[4]
                    pid_int = int(product_id)

                    # Get current Stock from Product_info (use pre-fetched metadata if available)
                    if pid_int in prod_meta:
                        previous_stock = prod_meta[pid_int]['stock']
                    else:
                        previous_stock = float(DB_Fetch(fr"select stock from product_info where product_id = {product_id}", False, "LOE")[-1])

                    # reduce bill qty in stock and update in product info, if qty is higher than avl stock,
                    # mark it as zero
                    new_stock = 0.0 if (float(previous_stock) - float(qty)) < 0 else (float(previous_stock) - float(qty))
                    if pid_int in prod_meta:
                        prod_meta[pid_int]['stock'] = new_stock

                    sql = fr"UPDATE `product_info` SET `stock` = {new_stock} WHERE `product_id` = {product_id}"
                    dbc.execute(sql)

                    # Fetch current(!=0) Purchase Data
                    purchase_data = DB_Fetch(
                        fr"select uid,cost_price,avail_qty from purchase_info where avail_qty >0 and product_id = '{product_id}' order by uid",
                        False, "LOL")
                    pur_data_dict = {}
                    ind_costprice = 0
                    reduce_qty = 0
                    chk_qty = qty

                    # If there is no Purchase Data
                    if len(purchase_data) == 0:
                        # get the max uid
                        maxi_sql = DB_Fetch(fr"SELECT IFNULL(MAX(uid), 1) FROM purchase_info;", False, "LOE")[-1] + 1

                        # Get the latest C price to create a no stock entry
                        pur_cpriceData = DB_Fetch(fr'''select cost_price,mrp from purchase_info where 
                        product_id = {product_id} order by uid desc limit 1''', False, "LOE")
                        if len(pur_cpriceData) == 0:
                            pur_cprice = 0
                            pur_mrp = 0
                        else:
                            pur_cprice = pur_cpriceData[0]
                            pur_mrp = pur_cpriceData[1]

                        # Add a No Stock entry with latest cost price and billed qty,
                        sql = fr"""INSERT INTO `purchase_info` (`uid`,`pdate`, `product_id`, `cost_price`, 
                        `purchase_qty`, `avail_qty`, `remark` , `mrp`) VALUES ({maxi_sql},'{Cur_Date_SQL}', 
                        {product_id}, {pur_cprice}, {chk_qty}, {0}, 'NS',{pur_mrp})"""
                        dbc.execute(sql)

                        # Create Purchase Dictionary
                        pur_data_dict[int(maxi_sql)] = chk_qty
                        ind_costprice = ind_costprice + (chk_qty * pur_cprice)

                    # if there is Purchase Data -
                    for pi in range(len(purchase_data)):
                        pur_uid = purchase_data[pi][0]
                        pur_cprice = purchase_data[pi][1]
                        pur_astock = purchase_data[pi][2]
                        # if bill qty is lesser than earliest stock entry, reduce the bill qty and close the loop
                        if pur_astock >= chk_qty:
                            reduce_qty = pur_astock - chk_qty
                            sql = fr"UPDATE `purchase_info` SET `avail_qty` = {reduce_qty} WHERE `uid` = {pur_uid}"
                            dbc.execute(sql)
                            pur_data_dict[int(pur_uid)] = chk_qty
                            ind_costprice = ind_costprice + (chk_qty * pur_cprice)
                            break
                        # if bill qty is greater than earliest avail stock entry
                        else:
                            if len(purchase_data) > pi + 1:
                                chk_qty = chk_qty - pur_astock
                                reduce_qty = 0
                                sql = fr"UPDATE `purchase_info` SET `avail_qty` = {reduce_qty} WHERE `uid` = {pur_uid}"
                                dbc.execute(sql)
                                pur_data_dict[int(pur_uid)] = pur_astock
                                ind_costprice = ind_costprice + (pur_astock * pur_cprice)
                            else:
                                reduce_qty = chk_qty - pur_astock
                                sql = fr"UPDATE `purchase_info` SET `avail_qty` = 0 WHERE `uid` = {pur_uid}"
                                dbc.execute(sql)

                                pur_data_dict[int(pur_uid)] = pur_astock
                                ind_costprice = ind_costprice + (pur_astock * pur_cprice)

                                maxi_sql = DB_Fetch(fr"select max(uid) from purchase_info", False, "LOE")[-1] + 1
                                sql = fr"""INSERT INTO `purchase_info` (`uid`,`pdate`, `product_id`, `cost_price`, 
                                `purchase_qty`, `avail_qty`, `remark`,`mrp`) VALUES ({maxi_sql},
                                '{Cur_Date_SQL}', {product_id}, {pur_cprice}, {reduce_qty}, {0}, 'NS',{pur_mrp})"""
                                dbc.execute(sql)
                                pur_data_dict[int(maxi_sql)] = reduce_qty
                                ind_costprice = ind_costprice + (reduce_qty * pur_cprice)

                    # Get UOM and GST from pre-fetched metadata or DB
                    if pid_int in prod_meta:
                        uom_val = prod_meta[pid_int]['uom']
                        gst_val = prod_meta[pid_int]['gst']
                    else:
                        step_data = DB_Fetch(fr"select uom,gst from product_info where product_id = {product_id}", False,
                                            "LOE")
                        uom_val = step_data[0]
                        gst_val = step_data[1]

                    # Insert into invoice item info db
                    item_dict = {
                        'fy': FY_Gen(ui.IQDE_InvDate.date().toPyDate()),
                        'invoice_no': ui.IQSB_InvNo.value(),
                        'product_id': product_id,
                        'uom': uom_val,
                        'qty': qty,
                        'rate': sprice,
                        'gst': gst_val,
                        'i_pnl': total_amt - ind_costprice,
                        'purchase_uid': json.dumps(pur_data_dict)
                    }

                    try:
                        DB_Push_Dict(item_dict, 'invoice_item_info', False)
                    except Exception as e:
                        print(e,"gen 1")

                # insert into Invoice DB
                inv_mtr_dict = {
                    'fy': FY_Gen(ui.IQDE_InvDate.date().toPyDate()),
                    'inv_no': ui.IQSB_InvNo.value(),
                    'gdate': ui.IQDE_InvDate.date().toPyDate().strftime('%Y-%m-%d'),
                    'mob_no': "NA" if ui.IQCB_PhoneNumber.currentText() == "" else ui.IQCB_PhoneNumber.currentText(),
                    'sales_man': ui.IQCB_SaleMan.currentText(),
                    'pay_mode': ui.IQCB_PayMethod.currentText(),
                    'discount': 0.0 if ui.IQLE_Discount.text() == '' else ui.IQLE_Discount.text(),
                    'amt_payabe': round_up_any(float(ui.IQLE_SubTotal.text())) ,
                    'amt_received': round_up_any(float(ui.IQLE_TotalAmount.text())) if ui.IQLE_RcvdAmount.text() == '' else round_up_any(float(ui.IQLE_RcvdAmount.text()))
                }
                DB_Push_Dict(inv_mtr_dict, 'invoice_master', False)
                db.commit()

            else:  # Editing existing invoice
                inv_number = ui.IQSB_InvNo.value()
                # print(f"[EDIT] Starting edit for invoice: {inv_number}")

                # ── STEP 1: Fetch all existing items from DB ──────────────────────
                # DOL = Dict of Lists → key is uid, values are remaining columns
                # Query: uid, product_id, qty, purchase_uid
                # So item_vals[0]=product_id, [1]=qty, [2]=purchase_uid
                existing_items = DB_Fetch(
                    fr"SELECT uid, product_id, qty, purchase_uid FROM invoice_item_info WHERE invoice_no = '{inv_number}'",
                    False, "DOL"
                )
                # print(f"[EDIT] Existing items fetched: {existing_items}")

                # ── STEP 2: Reverse all stock for every existing item ─────────────
                for item_db_uid, item_vals in existing_items.items():
                    try:
                        item_pid     = item_vals[0]   # product_id
                        item_qty     = float(item_vals[1])  # qty
                        raw_pur_uid  = item_vals[2]   # purchase_uid (JSON string)

                        print(f"[REVERSE] uid={item_db_uid} | product_id={item_pid} | qty={item_qty} | purchase_uid raw={raw_pur_uid}")

                        # Safely parse purchase_uid JSON
                        if isinstance(raw_pur_uid, str):
                            item_pur_uid = json.loads(raw_pur_uid)
                        elif isinstance(raw_pur_uid, dict):
                            item_pur_uid = raw_pur_uid
                        else:
                            print(f"[WARN] Unexpected purchase_uid type: {type(raw_pur_uid)} — skipping uid={item_db_uid}")
                            continue

                    except Exception as e:
                        print(f"[ERROR] Parsing item_vals for uid={item_db_uid}: {e} | raw item_vals={item_vals}")
                        continue

                    for pur_uid_str, pur_qty in item_pur_uid.items():
                        try:
                            pur_uid_int = int(pur_uid_str)
                            pur_qty     = float(pur_qty)

                            # Fetch the remark for this purchase entry
                            remark_row = DB_Fetch(
                                fr"SELECT remark, avail_qty FROM purchase_info WHERE uid = {pur_uid_int}",
                                False, "LOE"
                            )
                            print(f"  [STOCK] pur_uid={pur_uid_int} | qty_to_restore={pur_qty} | remark_row={remark_row}")

                            if len(remark_row) == 0:
                                print(f"  [SKIP] pur_uid={pur_uid_int} not found in purchase_info — already deleted?")
                                continue

                            remark   = remark_row[0]
                            cur_avail = float(remark_row[1]) if len(remark_row) > 1 else 0.0

                            if remark == 'NS':
                                # This was a phantom no-stock entry — delete it entirely
                                dbc.execute(fr"DELETE FROM purchase_info WHERE uid = {pur_uid_int} AND remark = 'NS'")
                                db.commit()
                                print(f"  [DELETE NS] Deleted NS entry uid={pur_uid_int}")
                            else:
                                # Restore the deducted qty back into the purchase entry
                                restored_avail = cur_avail + pur_qty
                                dbc.execute(
                                    fr"UPDATE purchase_info SET avail_qty = {restored_avail} WHERE uid = {pur_uid_int}"
                                )
                                db.commit()
                                print(f"  [RESTORE] purchase_info uid={pur_uid_int}: {cur_avail} → {restored_avail}")

                                # Restore product_info stock
                                cur_stock_row = DB_Fetch(
                                    fr"SELECT stock FROM product_info WHERE product_id = {item_pid}",
                                    False, "LOE"
                                )
                                if len(cur_stock_row) > 0:
                                    cur_stock    = float(cur_stock_row[-1])
                                    new_stock    = cur_stock + pur_qty
                                    dbc.execute(
                                        fr"UPDATE product_info SET stock = {new_stock} WHERE product_id = {item_pid}"
                                    )
                                    db.commit()
                                    print(f"  [RESTORE STOCK] product_id={item_pid}: {cur_stock} → {new_stock}")
                                else:
                                    print(f"  [WARN] product_id={item_pid} not found in product_info")

                        except Exception as e:
                            print(f"  [ERROR] Reversing pur_uid={pur_uid_str}: {e}")
                            db.rollback()
                            continue

                # ── STEP 3: Wipe all invoice_item_info rows for this invoice ──────
                try:
                    dbc.execute(fr"DELETE FROM invoice_item_info WHERE invoice_no = '{inv_number}'")
                    db.commit()
                    print(f"[DELETE] Cleared invoice_item_info for invoice_no={inv_number}")
                except Exception as e:
                    print(f"[ERROR] Deleting invoice_item_info: {e}")
                    db.rollback()

                # ── STEP 4: Update invoice_master header ──────────────────────────
                try:
                    discount    = 0.0 if ui.IQLE_Discount.text() in [None, '', '0', '0.0', ' '] else ui.IQLE_Discount.text()
                    amt_payable = ui.IQLE_SubTotal.text()
                    amt_recv    = 0.0 if ui.IQLE_RcvdAmount.text() in [None, '', '0', '0.0'] else ui.IQLE_RcvdAmount.text()
                    inv_date    = ui.IQDE_InvDate.date().toPyDate().strftime('%Y-%m-%d')

                    dbc.execute(fr"""
                        UPDATE invoice_master
                        SET gdate        = '{inv_date}',
                            discount     = '{discount}',
                            amt_payabe   = '{amt_payable}',
                            amt_received = '{amt_recv}'
                        WHERE inv_no = '{inv_number}' and fy = '{FY_Gen(Cur_Date)}' """)
                    db.commit()
                    # print(f"[UPDATE] invoice_master updated for inv_no={inv_number}")
                except Exception as e:
                    print(f"[ERROR] Updating invoice_master: {e}")
                    db.rollback()

                # ── STEP 5: Re-apply current table rows using FIFO stock logic ────
                cur_table_data = Fetch_Table_Values(BilTbl)
                if ['', '', '', '', '', '', ''] in cur_table_data:
                    cur_table_data.remove(['', '', '', '', '', '', ''])

                # print(f"[REAPPLY] Re-applying {len(cur_table_data)} rows from UI table")

                for data in cur_table_data:
                    if data[0] == '' or data[-2] == '':
                        continue

                    try:
                        product_id   = data[5]
                        product_name = data[0]
                        qty          = float(data[1])
                        sprice       = float(data[2])
                        total_amt    = qty * sprice
                        print(f"[ITEM] product_id={product_id} | name={product_name} | qty={qty} | price={sprice}")
                    except Exception as e:
                        print(f"[ERROR] Parsing table row {data}: {e}")
                        continue

                    # Deduct from product_info stock
                    try:
                        prev_stock_row = DB_Fetch(
                            fr"SELECT stock FROM product_info WHERE product_id = {product_id}",
                            False, "LOE"
                        )
                        prev_stock = float(prev_stock_row[-1]) if len(prev_stock_row) > 0 else 0.0
                        new_stock  = max(0.0, prev_stock - qty)
                        dbc.execute(fr"UPDATE product_info SET stock = {new_stock} WHERE product_id = {product_id}")
                        db.commit()
                        print(f"  [STOCK DEDUCT] product_id={product_id}: {prev_stock} → {new_stock}")
                    except Exception as e:
                        print(f"  [ERROR] Deducting product stock for product_id={product_id}: {e}")
                        db.rollback()
                        continue

                    # FIFO deduction from purchase_info
                    purchase_data = DB_Fetch(
                        fr"SELECT uid, cost_price, avail_qty FROM purchase_info WHERE avail_qty > 0 AND product_id = '{product_id}' ORDER BY uid",
                        False, "LOL"
                    )
                    pur_data_dict = {}
                    ind_costprice = 0.0
                    chk_qty       = qty
                    pur_cprice    = 0.0
                    pur_mrp       = 0.0

                    print(f"  [FIFO] Available purchase lots: {purchase_data}")

                    if len(purchase_data) == 0:
                        # No stock available — create NS entry with latest cost price
                        try:
                            maxi_sql = DB_Fetch(fr"SELECT IFNULL(MAX(uid), 1) FROM purchase_info", False, "LOE")[-1] + 1
                            pur_meta = DB_Fetch(
                                fr"SELECT cost_price, mrp FROM purchase_info WHERE product_id = {product_id} ORDER BY uid DESC LIMIT 1",
                                False, "LOE"
                            )
                            if len(pur_meta) >= 2:
                                pur_cprice = float(pur_meta[0])
                                pur_mrp    = float(pur_meta[1])
                            elif len(pur_meta) == 1:
                                pur_cprice = float(pur_meta[0])
                                pur_mrp    = 0.0
                            else:
                                pur_cprice = 0.0
                                pur_mrp    = 0.0

                            dbc.execute(fr"""
                                INSERT INTO purchase_info (uid, pdate, product_id, cost_price, purchase_qty, avail_qty, remark, mrp)
                                VALUES ({maxi_sql}, '{Cur_Date_SQL}', {product_id}, {pur_cprice}, {chk_qty}, 0, 'NS', {pur_mrp})
                            """)
                            db.commit()
                            pur_data_dict[int(maxi_sql)] = chk_qty
                            ind_costprice += chk_qty * pur_cprice
                            print(f"  [NS INSERT] uid={maxi_sql} | qty={chk_qty} | cprice={pur_cprice}")
                        except Exception as e:
                            print(f"  [ERROR] NS insert for product_id={product_id}: {e}")
                            db.rollback()

                    else:
                        # FIFO loop across available purchase lots
                        for pi in range(len(purchase_data)):
                            try:
                                pur_uid    = purchase_data[pi][0]
                                pur_cprice = float(purchase_data[pi][1])
                                pur_astock = float(purchase_data[pi][2])

                                # Try to get mrp for NS fallback later
                                try:
                                    pur_mrp_row = DB_Fetch(
                                        fr"SELECT mrp FROM purchase_info WHERE uid = {pur_uid}",
                                        False, "LOE"
                                    )
                                    pur_mrp = float(pur_mrp_row[0]) if len(pur_mrp_row) > 0 else 0.0
                                except Exception:
                                    pur_mrp = 0.0

                                if pur_astock >= chk_qty:
                                    # This lot covers the remaining qty fully
                                    dbc.execute(
                                        fr"UPDATE purchase_info SET avail_qty = {pur_astock - chk_qty} WHERE uid = {pur_uid}"
                                    )
                                    db.commit()
                                    pur_data_dict[int(pur_uid)] = chk_qty
                                    ind_costprice += chk_qty * pur_cprice
                                    print(f"  [FIFO] uid={pur_uid} covers all. avail: {pur_astock} → {pur_astock - chk_qty}")
                                    break

                                else:
                                    if len(purchase_data) > pi + 1:
                                        # More lots remain — drain this one and continue
                                        dbc.execute(
                                            fr"UPDATE purchase_info SET avail_qty = 0 WHERE uid = {pur_uid}"
                                        )
                                        db.commit()
                                        pur_data_dict[int(pur_uid)] = pur_astock
                                        ind_costprice += pur_astock * pur_cprice
                                        chk_qty -= pur_astock
                                        print(f"  [FIFO] uid={pur_uid} drained. Remaining qty={chk_qty}")

                                    else:
                                        # Last lot — drain it and create NS for overflow
                                        reduce_qty = chk_qty - pur_astock
                                        dbc.execute(
                                            fr"UPDATE purchase_info SET avail_qty = 0 WHERE uid = {pur_uid}"
                                        )
                                        db.commit()
                                        pur_data_dict[int(pur_uid)] = pur_astock
                                        ind_costprice += pur_astock * pur_cprice
                                        print(f"  [FIFO] uid={pur_uid} last lot drained. Overflow NS qty={reduce_qty}")

                                        if reduce_qty > 0:
                                            maxi_sql = DB_Fetch(
                                                fr"SELECT IFNULL(MAX(uid), 1) FROM purchase_info", False, "LOE"
                                            )[-1] + 1
                                            dbc.execute(fr"""
                                                INSERT INTO purchase_info (uid, pdate, product_id, cost_price, purchase_qty, avail_qty, remark, mrp)
                                                VALUES ({maxi_sql}, '{Cur_Date_SQL}', {product_id}, {pur_cprice}, {reduce_qty}, 0, 'NS', {pur_mrp})
                                            """)
                                            db.commit()
                                            pur_data_dict[int(maxi_sql)] = reduce_qty
                                            ind_costprice += reduce_qty * pur_cprice
                                            print(f"  [NS INSERT overflow] uid={maxi_sql} | qty={reduce_qty}")

                            except Exception as e:
                                print(f"  [ERROR] FIFO loop pi={pi} for product_id={product_id}: {e}")
                                db.rollback()
                                continue

                    # Fetch UOM and GST from product_info
                    try:
                        step_data = DB_Fetch(
                            fr"SELECT uom, gst FROM product_info WHERE product_id = {product_id}",
                            False, "LOE"
                        )
                        uom = step_data[0] if len(step_data) > 0 else ''
                        gst = step_data[1] if len(step_data) > 1 else 0

                        item_dict = {
                            'fy':           FY_Gen(ui.IQDE_InvDate.date().toPyDate()),
                            'invoice_no':   inv_number,
                            'product_id':   product_id,
                            'uom':          uom,
                            'qty':          qty,
                            'rate':         sprice,
                            'gst':          gst,
                            'i_pnl':        round(total_amt - ind_costprice, 4),
                            'purchase_uid': json.dumps(pur_data_dict)
                        }
                        print(f"  [INSERT] invoice_item_info: {item_dict}")
                        DB_Push_Dict(item_dict, 'invoice_item_info', False)

                    except Exception as e:
                        print(f"  [ERROR] Inserting invoice_item_info for product_id={product_id}: {e}")
                        continue

                # print(f"[DONE] Edit complete for invoice_no={inv_number}")

            ui.IQCB_PhoneNumber.setEnabled(False)
            ui.IQPB_Clear.setFocus(True)

            ClearWindow()
        
        else:
            show_info_msg("No Invoice Data", "Please Select the Billing Details")


    @Exception_Handle
    def delete_BilTbl_Row():
        data = Fetch_Table_Values(BilTbl)
        if len(data) > 1:
            data.pop(ui.IQTB_BillList.currentRow())
            BilTbl.blockSignals(True)
            Push_Table_Values(ui.IQTB_BillList, data, [0, 1, 2])
            BilTbl.setCurrentCell(BilTbl.rowCount() - 1, 0)
            BilTbl.blockSignals(False)

    @Exception_Handle
    def ClearWindow():
        global BillEdit 
        global costPriceDict,costIndex ,CustomerMobNo

        ui.IQDE_InvDate.setDate(QDate.currentDate())

        ui.IQTB_BillList.blockSignals(True)
        ui.IQCB_PhoneNumber.blockSignals(True)

        # ui.IQTB_BillList.setFocus(True)
        BillEdit = False
        ui.IQSB_InvNo.setMaximum(Fetch_InvoiceNumber())
        ui.IQTB_BillList.setRowCount(0)
        Update_PrdTbl("")

        ui.IQCB_PhoneNumber.clear()

        ui.IQCB_PhoneNumber.addItems([""] + CustomerMobNo)

        ui.IQLE_CustomerName.setReadOnly(False)
        ui.IQLE_Address.setReadOnly(False)

        Push_Table_Values(ui.IQTB_BillList, [['', '0', '', '', '', '','']], [0, 1, 2])
        # ui.IQLE_Discount.setText("0")
        ui.IQCB_SaleMan.setCurrentIndex(0)
        ui.IQCB_PayMethod.setCurrentIndex(0)
        # ui.IQLE_RcvdAmount.setText("")
        ui.IQSB_InvNo.setValue(Fetch_InvoiceNumber())
        ui.IQSB_InvNo.setEnabled(False)
        # ui.IQCB_PhoneNumber.setFocus(True)
        ui.IQTB_BillList.setEnabled(True)
        ui.IQTB_ProductList.setEnabled(True)
        ui.IQCB_PhoneNumber.setEnabled(True)
        ui.IQCB_PhoneNumber.clear()
        ui.IQLE_Account.clear()
        ui.IQCB_AddOutstanding.setEnabled(True)
        ui.IQSB_InvNo.setStyleSheet("")
        ui.IQCB_PhoneNumber.addItems([""] + DB_Fetch("select distinct(phone_no) from customer_info", False,"LOE"))
        BilTbl = ui.IQTB_BillList
        BilTbl.setFocus(True)
        BilTbl.setCurrentCell(0,0)
        BilTbl.edit(BilTbl.currentIndex())
        ui.IQLE_CostPrice.setText("Cost Price :    ")
        costPriceDict = getUIDndCP()

        ui.IQLE_SubTotal.blockSignals(True)
        ui.IQLE_Discount.blockSignals(True)
        ui.IQLE_RcvdAmount.blockSignals(True)

        clrLst = [ui.IQTE_UniqueQuantity,ui.IQTE_NetAmount,ui.IQTE_NetQuantity,
                  ui.IQLE_BalAccount,ui.IQLE_RcvdAmount,ui.IQLE_TotalAmount,ui.IQLE_Discount,
                  ui.IQLE_Account,ui.IQLE_SubTotal,ui.IQLE_Address,ui.IQLE_CustomerName]
        for clr in clrLst:
            clr.clear()

        ui.IQLE_SubTotal.blockSignals(False)
        ui.IQLE_Discount.blockSignals(False)
        ui.IQLE_RcvdAmount.blockSignals(False)
        ui.IQTB_BillList.blockSignals(False)
        ui.IQCB_PhoneNumber.blockSignals(False)
        ui.IQTB_BillList.setRowCount(1)
        BilTbl.setCurrentCell(0,0)
        BilTbl.edit(BilTbl.currentIndex())

    @Exception_Handle
    def PreviewEditBill():
        global BillEdit
        ui.IQSB_InvNo.setEnabled(True)
        ui.IQSB_InvNo.setFocus(True)
        ui.IQSB_InvNo.setMaximum(Fetch_InvoiceNumber() - 1)
        ui.IQCB_AddOutstanding.setEnabled(False)
        BillEdit = True
        FetchBillDetails()

    @Exception_Handle
    def Clear_SpecificData():

        BilTbl.setRowCount(0)
        lsttoClr = [ui.IQLE_Address,ui.IQLE_CustomerName,ui.IQCB_PhoneNumber,ui.IQTE_NetAmount,
        ui.IQTE_UniqueQuantity,ui.IQTE_NetQuantity,ui.IQLE_SubTotal,ui.IQLE_TotalAmount,
        ui.IQLE_RcvdAmount,ui.IQLE_Discount,ui.IQLE_BalAccount,ui.IQLE_Account]

        for lstClr in lsttoClr:
            lstClr.clear()

    @Exception_Handle
    def FetchBillDetails():

        global BillEdit

        ui.IQLE_SubTotal.blockSignals(True)
        ui.IQLE_Discount.blockSignals(True)
        ui.IQLE_RcvdAmount.blockSignals(True)
        ui.IQTB_BillList.blockSignals(True)
        ui.IQCB_PhoneNumber.blockSignals(True)

        ui.IQPB_LoadCustomer.setEnabled(False)

        Clear_SpecificData()

        # print(FY_Gen)

        
        if BillEdit:

            inv_data = DB_Fetch(fr"""select gdate, mob_no, sales_man, pay_mode, discount, amt_payabe, 
            amt_received, active_status from invoice_master where inv_no = {ui.IQSB_InvNo.value()} 
            and active_status = 'Y' and fy = '{FY_Gen(Cur_Date)}' """,False, "LOE")

            if ui.IQCB_UserLang.currentText() == 'English':
                inv_item_data = DB_Fetch(
                    fr"""select P.product_name, i.qty, i.rate, round(i.qty* i.rate ,2), i.gst, i.product_id, 
                    P.tamil_name from invoice_item_info i inner join product_info P on 
                    P.product_id  = i.product_id where i.invoice_no = {ui.IQSB_InvNo.value()} 
                    and i.fy = '{FY_Gen(Cur_Date)}' """,
                    False, "LOL")
            
            else:
                inv_item_data = DB_Fetch(
                    fr"""select P.tamil_name, i.qty, i.rate, round(i.qty* i.rate ,2), i.gst, i.product_id, 
                    P.product_name from invoice_item_info i inner join product_info P on 
                    P.product_id  = i.product_id where i.invoice_no = {ui.IQSB_InvNo.value()} and
                    i.fy = '{FY_Gen(Cur_Date)}' """,
                    False, "LOL")

            try:
                if inv_data[1] == 'NA':
                    ui.IQCB_PhoneNumber.addItem("NA")
                    ui.IQLE_Address.setText("")
                    ui.IQLE_CustomerName.setText("")

                else:
                    ui.IQCB_PhoneNumber.addItem(inv_data[1])
                    custData = DB_Fetch(fr"""select name,address,wholesale from customer_info where 
                    phone_no = '{inv_data[1]}'""",False,"LOE")

                    ui.IQLE_CustomerName.setText(custData[0])
                    ui.IQLE_Address.setText(custData[1])
                    ui.IQCB_pricing.setCurrentIndex(int(custData[2]))

                    ui.IQLE_CustomerName.setReadOnly(True)
                    ui.IQLE_Address.setReadOnly(True)
                    ui.IQCB_pricing.setEnabled(False)

                Push_Table_Values(BilTbl, inv_item_data, [0, 1, 2])

                # print(inv_data,float(inv_data[5]) - float(inv_data[4]) - float(inv_data[6]))

                ui.IQDE_InvDate.setDate(inv_data[0])
                ui.IQCB_PayMethod.setCurrentIndex(paymMode.index(inv_data[3]))
                ui.IQCB_SaleMan.setCurrentIndex(saleManlst.index(inv_data[2]))
                ui.IQLE_SubTotal.setText(str(inv_data[5]))
                ui.IQLE_Discount.setText(str(inv_data[4]))
                val = float(inv_data[5]) - float(inv_data[4])
                ui.IQLE_TotalAmount.setText(str(int(val) + (val % 1 > 0)))
                if float(inv_data[6]) != float(inv_data[5]):
                    ui.IQLE_RcvdAmount.setText(str(inv_data[6]))
                else:
                    ui.IQLE_RcvdAmount.setText(str(0.0))
                    
                ui.IQLE_BalAccount.setText(str(float(inv_data[5]) - float(inv_data[4]) - float(inv_data[6])))

                # round_up_any(float(ui.IQTE_NetAmount.toPlainText()))
                    
                ui.IQTE_NetAmount.setText(str(round_up_any( float(inv_data[5]) - float(inv_data[4]))))
                





                netqty = sum([float(i[1]) for i in inv_item_data])
                ui.IQTE_NetQuantity.setText(str(netqty))
                ui.IQTE_UniqueQuantity.setText(str(len(inv_item_data)))
                                    

                if inv_data[7] == "N":
                    ui.IQSB_InvNo.setStyleSheet("QSpinBox { background-color: lightcoral; }")
                    ui.IQTB_BillList.setEnabled(False)

                else:
                    ui.IQSB_InvNo.setStyleSheet('''
                    QSpinBox {
                    background-color: #f0f8ff;
                    border: 2px solid #0078d7;
                    border-radius: 6px;
                    padding: 2px 20px 2px 8px;
                    color: #003366;
                    font-size: 30px;
                    }''')
                    ui.IQTB_BillList.setEnabled(True)
                    BilTbl.setFocus(True)

            except Exception as e:
                print(e,"Bill Preview")

        ui.IQLE_SubTotal.blockSignals(False)
        ui.IQLE_Discount.blockSignals(False)
        ui.IQLE_RcvdAmount.blockSignals(False)
        ui.IQTB_BillList.blockSignals(False)
        ui.IQCB_PhoneNumber.blockSignals(False)

    @Exception_Handle
    def Delete_Invoice():

        if get_info_msg("Delete Invoice", "Please confirm to delete the invoice"):
            invoiceNumber = ui.IQSB_InvNo.value()

            itemInfoData = DB_Fetch(
                fr"select product_id,uid,purchase_uid from invoice_item_info where invoice_no = '{invoiceNumber}' and active_status = 'Y'",
                False, "DOL")

            for dkey, dvalue in itemInfoData.items():
              # print(dkey, dvalue, "item")
                productId = dkey
                productitemId = dvalue[0]
                productQty = json.loads(dvalue[1])

                sql = fr"update invoice_item_info set active_status = 'N' where uid = '{productitemId}'"
                dbc.execute(sql)
                db.commit()

                for prodkey, prodvalue in json.loads(dvalue[1]).items():
                  # print(prodkey, prodvalue, "individual")

                    prodData = DB_Fetch(
                        fr"select purchase_qty,avail_qty,remark from purchase_info where uid = {prodkey}", False, "LOE")
                    purQTY = prodData[0]
                    availStock = prodData[1]
                    remarkData = prodData[2]

                    if purQTY == availStock + prodvalue and remarkData == "NS":
                        sql = fr"delete from purchase_info where uid = '{prodkey}'"
                      # print(sql)
                        dbc.execute(sql)
                        db.commit()
                    elif purQTY > availStock + prodvalue and remarkData == "NS":
                        sql = fr"update purchase_info set avail_qty = {availStock + prodvalue},purchase_qty = {availStock + prodvalue} where uid = '{prodkey}'"
                      # print(sql)
                        dbc.execute(sql)
                        db.commit()
                    else:
                        sql = fr"update purchase_info set avail_qty = {availStock + prodvalue} where uid = '{prodkey}'"
                        # print(sql)
                        dbc.execute(sql)
                        db.commit()
                        prodInfoStock = \
                        DB_Fetch(fr"select stock from product_info where product_id = '{productId}'", False, "LOE")[
                            -1] + prodvalue
                        # print(prodInfoStock)
                        productsql = fr"update product_info set stock = {prodInfoStock} where product_id = '{productId}'"
                        dbc.execute(productsql)
                        db.commit()

            sql = fr"""update invoice_master set active_status = 'N' where 
            inv_no = '{invoiceNumber}' and fy = '{FY_Gen(Cur_Date)}' """
            dbc.execute(sql)
            db.commit()
            ui.IQSB_InvNo.setStyleSheet("QSpinBox { background-color: lightcoral; }")

    @Exception_Handle
    def UI_Flow():
        if QApplication.focusWidget().objectName() != "IQTB_BillList":
            ui.IQTB_BillList.setFocus()
        else:
            ui.IQLE_RcvdAmount.setFocus()

    @Exception_Handle
    def Calculating_Balance_Amt():
        if ui.IQCB_PhoneNumber.currentText() not in ["NA",""]:
            print("----------")
            sql = fr"""select COALESCE(sum(amt_payabe) -sum(discount) - sum(amt_received),0) from invoice_master 
            where mob_no = '{ui.IQCB_PhoneNumber.currentText()}' and fy = '{FY_Gen(Cur_Date)}' ;"""
            balAmount = DB_Fetch(sql,False,'LOE')[0]
            ui.IQLE_Account.setText(str(balAmount))
            Calculate_NetAmount()

        else:
            ui.IQLE_Account.clear()
            show_info_msg("No Customer Data", "Please Select the Customer Details")
            if ui.IQCB_PhoneNumber.currentText() in ["NA",""]:
                ui.IQLE_Account.setText("0.0")

    FetchCustomerMobile = lambda X: DB_Fetch(fr''' select phone_no from customer_info where 
                                                        phone_no like '{X}%' order by phone_no ''', False, "LOE")

    Update_PrdTbl("")
    TimeUpdate()
    Adjust_Table_Width(ui.OQTB_Tax, [8, 5, 15, 10])
    Adjust_Table_Width(ui.IQTB_BillList, [38, 10, 10, 15, 0, 0,0])
    Adjust_Table_Width(ui.IQTB_ProductList, [0, 0, 25, 10, 10, 0, 0])

    PrdTbl.setTabKeyNavigation(False)
    BilTbl.setTabKeyNavigation(False)
    BilTbl.setRowCount(1)
    # BilTbl.setFocus(True)
    PrdTbl.activated.connect(Add_Item)
    # BilTbl.activated.connect(lambda: BilTbl_func())
    # BilTbl.cellChanged.connect(Calc_Amount)
    BilTbl.activated.connect(BillTbl_functionality)
    BilTbl.cellChanged.connect(BillTbl_functionality)

    ui.IQCB_PhoneNumber.addItems([""] + FetchCustomerMobile(""))
    Dynamic_Filter_ComboBox(ui.IQCB_PhoneNumber)
    ui.IQCB_PhoneNumber.currentIndexChanged.connect(lambda: Update_customerDetails())
    ui.IQDE_InvDate.setDate(QDate.currentDate())
    ui.IQPB_LoadCustomer.clicked.connect(lambda: Load_NewCustomer())
    ui.IQSB_InvNo.setValue(Fetch_InvoiceNumber())
    ui.IQSB_InvNo.setEnabled(False)
    ui.IQLE_SubTotal.textChanged.connect(lambda: Calculate_NetAmount())
    ui.IQLE_Discount.textChanged.connect(lambda: Calculate_NetAmount())
    ui.IQLE_RcvdAmount.textChanged.connect(lambda: Calculate_Balance())
    ui.IQPB_Save.clicked.connect(lambda: Generate_Invoice(False))
    ui.IQPB_SavePrint.clicked.connect(lambda: Generate_Invoice(True))

    QShortcut(QKeySequence(Qt.ControlModifier | Qt.Key_Delete), ui.IQTB_BillList).activated.connect(delete_BilTbl_Row)
    ui.IQPB_Clear.clicked.connect(lambda: ClearWindow())
    ui.IQPB_PreviewEdit.clicked.connect(lambda: PreviewEditBill())
    ui.IQSB_InvNo.valueChanged.connect(lambda: FetchBillDetails())
    ui.IQPB_Delete.clicked.connect(lambda: Delete_Invoice())

    QShortcut(QKeySequence("F1"), ui.InvWindow).activated.connect(lambda: UI_Flow())
    
    shortcutf9 = QShortcut(QKeySequence("F9"), Inv_Mtr)
    shortcutf9.activated.connect(lambda: ui.IQCB_pricing.setCurrentText("Retail"))

    shortcutf10 = QShortcut(QKeySequence("F10"), Inv_Mtr)
    shortcutf10.activated.connect(lambda: ui.IQCB_pricing.setCurrentText("Wholesale"))

    for elem in ui.scrollAreaWidgetContents.findChildren(QWidget):
        if elem.objectName()=="IQCB_PhoneNumber":
            continue
        elem.installEventFilter(highlighter)
    ui.IQCB_pricing.currentIndexChanged.connect(lambda: Update_PrdTbl(""))  
    TwinkUI.Base_Tab.currentChanged.connect(lambda:Update_PrdTbl(""))
    # ui.IQCB_PhoneNumber.setFocus(True)
    ui.IQCB_AddOutstanding.stateChanged.connect(lambda : Calculating_Balance_Amt())
    
    BilTbl.setCurrentCell(0,0)
    BilTbl.setFocus(True)
    BilTbl.edit(BilTbl.currentIndex())


    ui.IQCB_UserLang.currentIndexChanged.connect(lambda : \
        Adjust_Table_Width(ui.IQTB_ProductList, [0, 0, 25, 10, 10, 0, 0]) \
            if ui.IQCB_UserLang.currentText() == "Tamil" else \
                Adjust_Table_Width(ui.IQTB_ProductList, [0, 25, 0, 10, 10, 0, 0]))


if __name__ == "__main__":
    Invoice_Master_FN()
    Inv_Mtr.showMaximized()
    sys.exit(app.exec_())