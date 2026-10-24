from Env import *

def Purchase_Master_FN():
    # print("Start")
    # ---Definitions---

    print("================= Purchase Started =================")

    ui = Prc_MtrUI

    tbl = ui.PurchaseTable

    @Exception_Handle
    def Generate_Table_Entry():
        # print(tbl.currentColumn(),"=============")

        if tbl.currentColumn() == 2:
            exist = Fetch_Table_Values(tbl)
            exist_prod = [x[1] for x in exist]
            new_prod = exist[tbl.currentRow()][1]
            if exist_prod.count(new_prod)>1:
                # print("Already Aval")
                show_info_msg("Exiting Entry",fr" '{new_prod}' already available in Row {exist_prod.index(new_prod)+1}, Please update ")
                tbl.removeRow(tbl.currentRow())

                tbl.setCurrentCell(exist_prod.index(new_prod), 1)

        if tbl.rowCount()>0 and tbl.currentColumn() == 7:
            # print(Fetch_Table_Values(tbl)[-1])
            if '' != Fetch_Table_Values(tbl)[-1][0]:
                tbl.setRowCount(tbl.rowCount() + 1)
                tbl.setFocus(True)
                row = tbl.rowCount()-1
            else:
                row = tbl.rowCount()-1
                tbl.setCurrentCell(row, 1)
                return


            CB = QComboBox()
            CB.setEditable(True)

            CB.addItem("","")

            if ui.IQCB_Language.currentText() == "Tamil":
                print(ProductBarCodeList())
                for name,barcode,tamil_name in ProductBarCodeList():
                    CB.addItem(tamil_name + " - " + name ,barcode)
            else:
                for name,barcode,tamil_name in ProductBarCodeList():
                    CB.addItem(name,barcode)

            # for name,barcode,tamil_name in ProductBarCodeList():
            #     CB.addItem(name,barcode)

            Dynamic_Filter_ComboBox(CB)
            CB.lineEdit().returnPressed.connect(Update_BarcodeText)
            CB.currentIndexChanged.connect(Update_ProductData)
            tbl.setCellWidget(row,1,CB)
            tbl.setCurrentCell(row, 1)
            tbl.setCellWidget(row,1,CB)
            tbl.setCurrentCell(row, 1)

        if tbl.rowCount() == 0 :
            tbl.setRowCount(1)
            tbl.setFocus(True)
            row = 0
            CB = QComboBox()
            CB.setEditable(True)
            CB.addItem("","")

            if ui.IQCB_Language.currentText() == "Tamil":
                for name,barcode,tamil_name in ProductBarCodeList():
                    CB.addItem(tamil_name + " - " + name ,barcode)
            else:
                for name,barcode,tamil_name in ProductBarCodeList():
                    CB.addItem(name,barcode)

            Dynamic_Filter_ComboBox(CB)
            CB.lineEdit().returnPressed.connect(Update_BarcodeText)
            CB.currentIndexChanged.connect(Update_ProductData)
            tbl.setCellWidget(row,1,CB)
            tbl.setCurrentCell(row, 1)

    @Exception_Handle
    def Update_BarcodeText():
        # print("I'm here return pressed")
        tindex = tbl.currentIndex()
        val = tbl.cellWidget(tindex.row(),tindex.column())
        text = val.lineEdit().text().strip()
        index = val.findData(text)
        if index >= 0:
            val.setCurrentIndex(index)


    @Exception_Handle
    def Update_ProductData(arg):
        # print("Activation")
        index = tbl.currentIndex()
        if index.column()== 1:
            val = tbl.cellWidget(index.row(),index.column())
            if val.currentText() !="":

                if ui.IQCB_Language.currentText() == "Tamil":
                    try:
                        sql = fr'''select product_id,mrp,cost_price,wholesale,retail,purchase_price from product_info where 
                                    product_name =  '{val.currentText().split(" - ")[1]}' '''
                    except Exception as e:
                        print(e)
                        sql = fr'''select product_id,mrp,cost_price,wholesale,retail,purchase_price from product_info where 
                                    product_name =  '{val.currentText()}' '''
                else:
                    sql = fr'''select product_id,mrp,cost_price,wholesale,retail,purchase_price from product_info where 
                                product_name =  '{val.currentText()}' '''

                try:
                    temp = DB_Fetch(sql,False,"DOC")
                    tbl.setItem(index.row(),3, T_itm(str(temp['cost_price'])))
                    tbl.setItem(index.row(),4, T_itm(str(temp['mrp']))) 
                    tbl.setItem(index.row(),5, T_itm(str(temp['retail']))) 
                    tbl.setItem(index.row(),6, T_itm(str(temp['wholesale'])))  
                    tbl.setItem(index.row(),0, T_itm(str(temp['product_id']))) 
                    tbl.setItem(index.row(),9, T_itm(str(temp['purchase_price']))) 

                
                except:
                    temp = T_itm('')
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                    temp.setBackground(QColor("#ffcccc"))
                    tbl.setItem(index.row(),3, temp)
                    #----
                    temp = T_itm('')
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                    temp.setBackground(QColor("#ffcccc"))
                    tbl.setItem(index.row(),4, temp)
                    #---
                    temp = T_itm('')
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                    temp.setBackground(QColor("#ffcccc"))
                    tbl.setItem(index.row(),5, temp)
                    #---
                    temp = T_itm('')
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                    temp.setBackground(QColor("#ffcccc"))
                    tbl.setItem(index.row(),6, temp)
                    #---
                    temp = T_itm('')
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                    temp.setBackground(QColor("#ffcccc"))
                    tbl.setItem(index.row(),0, temp)
                    #---
                    temp = T_itm('')
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                    temp.setBackground(QColor("#ffcccc"))
                    tbl.setItem(index.row(),9, temp)

            else:
                tbl.setItem(index.row(),3, T_itm(str("0.0")))
                tbl.setItem(index.row(),4, T_itm(str("0.0")))
                tbl.setItem(index.row(),5, T_itm(str("0.0")))
                tbl.setItem(index.row(),6, T_itm(str("0.0")))
                tbl.setItem(index.row(),0, T_itm(str("0.0")))
                tbl.setItem(index.row(),9, T_itm(str("0.0")))

    @Exception_Handle
    def Calculate_Values(row,column):
        # print(row,column)
        if column >1 and column <7:
            try:
                CP = float(tbl.item(row,3).text())
                RSP = float(tbl.item(row,5).text())
                WSP = float(tbl.item(row,6).text())

                if CP >0:
                    RPP = str(round(((RSP-CP)/CP)*100,1)) + " %"
                    WPP = str(round(((WSP-CP)/CP)*100,1)) + " %"

                    tbl.setItem(row,7,T_itm(RPP))
                    tbl.setItem(row,8,T_itm(WPP))
                
                else:
                    
                    tbl.setItem(row,7,T_itm("NA"))
                    tbl.setItem(row,8,T_itm("NA"))
            
            except Exception as e:pass

            data = Fetch_Table_Values(tbl)
            if data[-1][0]== "": data.pop(-1)
            ui.OQLE_NetProdCount.setText(str(len(data)))

            #----Work Here
            try:

                total = str(sum((float(row[2]) or 0) for row in data))
                ui.OQLE_NetProdQty.setText(total)
                
                ui.OQLE_NetProdPrice.setText(str(sum((float(row[2])*float(row[3]) or 0) for row in data)))
            

            except Exception as e: pass

    @Exception_Handle
    def Clear_Table():
        tbl.setRowCount(0)
        Generate_Table_Entry()
        ui.OQLE_NetProdCount.setText("0")
        ui.OQLE_NetProdQty.setText("0")     
        ui.OQLE_NetProdPrice.setText("0")
        ui.IQPB_PushPurchaseEntry.setEnabled(True)

    @Exception_Handle    
    def DeleteTableEntry():
        if get_info_msg("Delete Confirmation","Please confirm to delete the selected entry"):
            if tbl.currentRow() >0:
                tbl.removeRow(tbl.currentRow())
            
            else:
                tbl.setRowCount(0)
                Generate_Table_Entry()

    @Exception_Handle
    def LoadPurchaseDateSql():

        tblData = Fetch_Table_Values(ui.PurchaseTable)

        purData, prodId = (
            [i for i in tblData if i[0] != ""],
            [i[0] for i in tblData if i[0] != ""])

        if len(purData) > 0:
            if len(prodId) > 1:
                sql = fr"""select product_id,stock from product_info 
                where product_id in {tuple(prodId)}"""
            
            else:
                sql = fr"""select product_id,stock from product_info 
                            where product_id in ('{prodId[0]}')"""

            sqlData = DB_Fetch(sql, False, 'DIC')

            # print(sqlData)


            for tblValue in purData:

                proddict = {
                    'stock': float(sqlData[int(tblValue[0])]) + float(tblValue[2]),
                    'cost_price': float(tblValue[3]),
                    'mrp': float(tblValue[4]),
                    'retail': float(tblValue[5]),
                    'wholesale': float(tblValue[6]),
                    'purchase_price': float(tblValue[9])
                }

                prodDictUID = {
                    'product_id': tblValue[0]
                }

                DB_Update_Dict(proddict, prodDictUID, 'product_info', False)

                purcDict = {
                    'pdate' : ui.IQDE_Date.date().toString("yyyy-MM-dd"),
                    'product_id' : tblValue[0],
                    'mrp' : float(tblValue[4]),
                    'cost_price' : float(tblValue[3]),
                    'purchase_qty' : float(tblValue[2]),
                    'avail_qty' : float(tblValue[2]),
                    'purchase_price' : float(tblValue[9])
                }
                DB_Push_Dict(purcDict, 'purchase_info', False)

            show_info_msg("Purchased Stock", "Purchase Stock updated Successfully")
            ui.IQPB_PushPurchaseEntry.setEnabled(False)
            
        else:
            show_info_msg("Empty Purchase Data", "Enter the Purchase Data")

    @Exception_Handle
    def Re_Generate_Table_Entry():

        # print(tbl.currentColumn(),"=============",tbl.currentRow())

        row = tbl.currentRow()
        col = tbl.currentColumn()

        CB = QComboBox()
        CB.setEditable(True)
        
        CB.addItem("","")

        if ui.IQCB_Language.currentText() == "Tamil":
            for name,barcode,tamil_name in ProductBarCodeList():
                CB.addItem(tamil_name + " - " + name ,barcode)
        else:
            for name,barcode,tamil_name in ProductBarCodeList():
                CB.addItem(name,barcode)

        # tbl.setCellWidget(row,1,CB)

        Dynamic_Filter_ComboBox(CB)
        CB.lineEdit().returnPressed.connect(Update_BarcodeText)
        CB.currentIndexChanged.connect(Update_ProductData)
        tbl.setCellWidget(row,1,CB)
        tbl.setCurrentCell(row, 1)





    # ---Functions---
    ui.IQDE_Date.setDate(QDate.currentDate())
    tbl.setFocus(True)
    Generate_Table_Entry()
    Adjust_Table_Width(tbl,[5,50,10,10,10,15,15,18,18,10])
    tbl.activated.connect(lambda : Generate_Table_Entry())
    tbl.cellChanged.connect(Calculate_Values)
    ui.IQPB_Refresh.clicked.connect(lambda : Clear_Table())
    QShortcut(QKeySequence(Qt.ControlModifier | Qt.Key_Delete),tbl).activated.connect(DeleteTableEntry)

    ui.IQCB_Language.currentIndexChanged.connect(lambda : Re_Generate_Table_Entry())

    ui.IQPB_PushPurchaseEntry.clicked.connect(lambda : LoadPurchaseDateSql())



if __name__ == "__main__":
    Purchase_Master_FN()
    Prc_Mtr.showMaximized()
    sys.exit(app.exec_())