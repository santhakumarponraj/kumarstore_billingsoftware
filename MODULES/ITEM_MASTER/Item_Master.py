from Env import *

@Exception_Handle
def Item_Master_FN():

    print("================ Item Master Started ===========")

    ui = Itm_MtrUI

    validator = QDoubleValidator(0.0, 9999999.99, 2)  # min=0 prevents negative
    validator.setNotation(QDoubleValidator.StandardNotation)
    ui.IQLE_Stock.setValidator(validator)

    Update_Property(ui.Item_Frame, "Readonly", "IQLE", True)
    Update_Property(ui.Item_Frame, "Readonly", "IQTE", True)

    Units_List = ["Kg", "Nos", "Ton",'Piece','Gram','Bags','Dozen','Case','Tin']
    Active_Status = ["Yes","No"]

    ui.IQCB_UOM.addItems(Units_List)
    


    print("------------Item Master Started-------------")

    @Exception_Handle
    def On_Clicked_Product_ViewTbl():

        selected_rows = ui.OQTB_Product.selectionModel().selectedRows()
        index = selected_rows[-1]
        Product_IPN = ui.OQTB_Product.model().index(index.row(), 0).data()

        StockStatus = fr"""(select uid,pdate,product_id,mrp,cost_price,purchase_qty,avail_qty,
        remark from purchase_info where avail_qty =0 and product_id = {Product_IPN} order by uid desc limit 1) 
        union (select uid,pdate,product_id,mrp,cost_price,purchase_qty,avail_qty,remark from purchase_info 
        where avail_qty > 0 and product_id = {Product_IPN})"""

        # print(StockStatus,'StockStatus')
        # Push_TableView_SqlData('Stock_Model', ui.IQTB_StockEntry, StockStatus)
        Push_TableView_SqlData_Wth_AdjColumName('Stock_Model', ui.IQTB_StockEntry, StockStatus,
                                                ["UID", "Purchase Date", "Product ID", "MRP", "Purchase Price",
                                                 "Total Quantity", "Available Quantity", "Remarks"])

        # Adjust_ViewTbl_ColName(ui.IQTB_StockEntry,["1","2","3","4","5","6","7","8"])



        # ui.IQTB_StockEntry.setHorizontalHeaderLabels(["Col1", "Col2", "Col3", "Col4", "Col5", "Col6", "col7","col7"])

        sql = fr"select sum(avail_qty) from purchase_info where product_id = {Product_IPN} and  avail_qty>0 group by product_id"
        maxi_stock = DB_Fetch(sql, False, "LOE")
        ui.IQLE_CurrentStock.setText(str(0 if len(maxi_stock) == 0 else maxi_stock[0]))

        ui.IQLE_ProductID.setText(str(Product_IPN))
        ui.IQLE_BarcodeInput.setText(str(ui.OQTB_Product.model().index(index.row(), 1).data()))
        ui.IQLE_ProductName.setText(ui.OQTB_Product.model().index(index.row(), 2).data())
        ui.IQLE_TamilName.setText(ui.OQTB_Product.model().index(index.row(), 3).data())
        ui.IQLE_PurchaseRate.setText(str(ui.OQTB_Product.model().index(index.row(), 4).data()))
        ui.IQLE_MRP.setText(str(ui.OQTB_Product.model().index(index.row(), 5).data()))
        ui.IQLE_SalesPrice_W.setText(str(ui.OQTB_Product.model().index(index.row(), 6).data()))
        ui.IQLE_SalesPrice_R.setText(str(ui.OQTB_Product.model().index(index.row(), 7).data()))
        ui.IQLE_GST.setText(str(ui.OQTB_Product.model().index(index.row(), 8).data()))
        hsn_code = "NA" if str(ui.OQTB_Product.model().index(index.row(), 11).data()) == "" else str(ui.OQTB_Product.model().index(index.row(), 11).data())
        ui.IQLE_HsnCode.setText(hsn_code)

        ui.IQCB_UOM.clear()
        ui.IQCB_UOM.addItems(Units_List)
        ui.IQCB_UOM.setCurrentIndex(
            Units_List.index(ui.OQTB_Product.model().index(index.row(), 9).data()))
        ui.IQCB_UOM.setEnabled(False)

        ui.IQLE_Stock.setText("")

        ui.IQCB_Active.clear()
        ui.IQCB_Active.addItems(Active_Status)
        ui.IQCB_Active.setCurrentIndex(
            Active_Status.index("Yes" if ui.OQTB_Product.model().index(index.row(), 10).data() == "Y" else "No"))
        ui.IQCB_Active.setEnabled(False)

        Update_Property(ui.Item_Frame, "Readonly", "IQLE", True)
        Update_Property(ui.Item_Frame, "Readonly", "IQTE", True)

        if ui.IQCB_Add.isChecked():
            ui.IQCB_Add.setChecked(False)
        if ui.IQCB_Update.isChecked():
            ui.IQCB_Update.setChecked(False)
        if ui.IQCB_UpdateStock.isChecked():
            ui.IQCB_UpdateStock.setChecked(False)
            Enable_Stock_Product()

        # Adjust_Table_Width(ui.IQTB_StockEntry, [0, 0, 10, 10, 10, 10, 10, 10])

    @Exception_Handle
    def Filter_Product_ViewTbl():
        if len(ui.OQLE_ProductFilter.text()) >0:
            # print(ui.IQLE_CustomerSearch.text())
            filter_SQL_Customer = fr"""select product_id,barcode,product_name,tamil_name,cost_price,mrp,wholesale,
            retail,gst,uom,active_status,hsn 
            from product_info WHERE (product_name LIKE '%{ui.OQLE_ProductFilter.text()}%' or barcode like 
            '%{ui.OQLE_ProductFilter.text()}%') and active_status not in ('D') ORDER BY product_name"""
            # print(filter_SQL_Customer)
            Push_TableView_SqlData('Product_Model', ui.OQTB_Product, filter_SQL_Customer)

        else:
            Product_Viewtbl_SQlData()

            Update_Property(ui.Item_Frame, "Clear", "IQLE", True)
            Update_Property(ui.Item_Frame, "Clear", "IQTE", True)
            ui.IQLE_ProductID.setReadOnly(True)
            ui.IQLE_ProductID.setText(str(Maximum_Product_ID()))

            ui.IQCB_Active.clear()
            ui.IQCB_UOM.clear()

            ui.IQCB_Active.setEnabled(True)
            ui.IQCB_UOM.setEnabled(True)

            ui.IQLE_CurrentStock.setReadOnly(True)

            ui.IQCB_Active.addItems(Active_Status)
            ui.IQCB_UOM.addItems(Units_List)
            ui.OQTB_Product.selectionModel().clearSelection()

            # model = ui.IQTB_StockEntry.model()
            # if model:
            #     model.removeRows(0, model.rowCount())
            empty_model = QStandardItemModel()
            ui.IQTB_StockEntry.setModel(empty_model)

    @Exception_Handle
    def Enable_Add_Product(): #Enable_Add_Item(state)
        # if state == Qt.Checked:
        if ui.IQCB_Add.isChecked():
            ui.IQPB_AddProduct.setEnabled(True)
            ui.IQPB_TamilKeyboard.setEnabled(True)

            ui.OQTB_Product.setEnabled(False)

            ui.IQLE_CurrentStock.setStyleSheet("background-color: lightgrey;")

            Update_Property(ui.Item_Frame, "Readonly", "IQLE", False)
            Update_Property(ui.Item_Frame, "Readonly", "IQTE", False)

        else:
            ui.IQLE_CurrentStock.setStyleSheet("")
            ui.IQPB_AddProduct.setEnabled(False)
            ui.IQPB_TamilKeyboard.setEnabled(False)
            ui.OQTB_Product.setEnabled(True)
            Update_Property(ui.Item_Frame, "Readonly", "IQLE", True)
            Update_Property(ui.Item_Frame, "Readonly", "IQTE", True)

        Update_Property(ui.Item_Frame, "Clear", "IQLE", True)
        Update_Property(ui.Item_Frame, "Clear", "IQTE", True)
        ui.IQLE_ProductID.setReadOnly(True)
        ui.IQLE_ProductID.setText(str(Maximum_Product_ID()))

        ui.IQCB_Active.clear()
        ui.IQCB_UOM.clear()

        ui.IQCB_Active.setEnabled(True)
        ui.IQCB_UOM.setEnabled(True)

        ui.IQLE_CurrentStock.setReadOnly(True)


        ui.IQCB_Active.addItems(Active_Status)
        ui.IQCB_UOM.addItems(Units_List)
        ui.OQTB_Product.selectionModel().clearSelection()

        empty_model = QStandardItemModel()
        ui.IQTB_StockEntry.setModel(empty_model)

    @Exception_Handle
    def Enable_Update_Product():#def Enable_Update_Product(state):

        if ui.IQLE_ProductName.text() != "":

            # if state == Qt.Checked:
            if ui.IQCB_Update.isChecked():
                ui.IQPB_UpdateProduct.setEnabled(True)
                ui.IQPB_TamilKeyboard.setEnabled(True)
                Update_Property(ui.Item_Frame, "Readonly", "IQLE", False)
                Update_Property(ui.Item_Frame, "Readonly", "IQTE", False)

                ui.IQCB_Active.setEnabled(True)
                ui.IQCB_UOM.setEnabled(True)

                Index_Status = Active_Status.index(ui.IQCB_Active.currentText())
                Index_Unit = Units_List.index(ui.IQCB_UOM.currentText())

                ui.IQCB_Active.clear()
                ui.IQCB_UOM.clear()

                ui.IQCB_Active.addItems(Active_Status)
                ui.IQCB_UOM.addItems(Units_List)

                ui.IQCB_Active.setCurrentIndex(Index_Status)
                ui.IQCB_UOM.setCurrentIndex(Index_Unit)

            else:
                ui.IQPB_UpdateProduct.setEnabled(False)
                ui.IQPB_TamilKeyboard.setEnabled(False)

                Update_Property(ui.Item_Frame, "Readonly", "IQLE", True)
                Update_Property(ui.Item_Frame, "Readonly", "IQTE", True)

                action = ui.IQCB_Active.currentText()
                uom = ui.IQCB_UOM.currentText()

                ui.IQCB_Active.clear()
                ui.IQCB_UOM.clear()

                ui.IQCB_Active.addItem(action)
                ui.IQCB_UOM.addItem(uom)

        else:
            Show_Msg_Infomation("Select The Product","Please Select the Product to be Updated and Try Again")


        ui.IQLE_ProductID.setReadOnly(True)
        ui.IQLE_CurrentStock.setReadOnly(True)

    @Exception_Handle
    def Enable_Stock_Product():

        if ui.OQTB_Product.selectionModel().hasSelection():
            Product_ID = ui.IQLE_ProductID.text()
            if ui.IQCB_UpdateStock.isChecked():

                ui.IQPB_UpdateStock.setEnabled(True)
                ui.IQPB_AddProduct.setEnabled(False)
                ui.IQPB_UpdateProduct.setEnabled(False)

                ui.IQLE_MRP.setStyleSheet("color: red; background-color: lightblue;")
                ui.IQLE_PurchaseRate.setStyleSheet("color: red; background-color: lightblue;")
                ui.IQLE_Stock.setStyleSheet("color: red; background-color: lightblue;")

                sql = fr"""select mrp,cost_price,purchase_qty,avail_qty from purchase_info where 
                product_id = {Product_ID} order by uid desc limit 1;"""

                lastStockData = DB_Fetch(sql,False,"DOC")

                if len(lastStockData) > 0:

                    stockSoldQty = lastStockData['purchase_qty'] - lastStockData['avail_qty']

                    ui.IQLE_Stock.setText(str(lastStockData['purchase_qty']))
                    ui.IQLE_MRP.setText(str(lastStockData['mrp']))
                    ui.IQLE_PurchaseRate.setText(str(lastStockData['cost_price']))


                    ui.IQLE_Stock.setReadOnly(False)
                    ui.IQLE_MRP.setReadOnly(False)
                    ui.IQLE_PurchaseRate.setReadOnly(False)


                else:
                    Show_Msg_Infomation("Selected Product has no Stock", "Please Add a Stock Before Updating")

                    ui.IQPB_UpdateStock.setEnabled(False)

                    ui.IQLE_Stock.setReadOnly(True)
                    ui.IQLE_MRP.setReadOnly(True)
                    ui.IQLE_PurchaseRate.setReadOnly(True)

                    ui.IQLE_MRP.setStyleSheet("")
                    ui.IQLE_PurchaseRate.setStyleSheet("")
                    ui.IQLE_Stock.setStyleSheet("")
                    ui.IQLE_Stock.setText('')

            else:
                ui.IQPB_UpdateStock.setEnabled(False)

                ui.IQLE_Stock.setReadOnly(True)
                ui.IQLE_MRP.setReadOnly(True)
                ui.IQLE_PurchaseRate.setReadOnly(True)

                ui.IQLE_MRP.setStyleSheet("")
                ui.IQLE_PurchaseRate.setStyleSheet("")
                ui.IQLE_Stock.setStyleSheet("")
                ui.IQLE_Stock.setText('')


        else:
            Show_Msg_Infomation("Select The Product", "Please Select the Product to be Updated and Try Again")

    @Exception_Handle
    def Update_Previous_StockData():

        Product_ID = ui.IQLE_ProductID.text()

        sql = fr"""select uid,mrp,cost_price,purchase_qty,avail_qty from purchase_info where 
                        product_id = {Product_ID} order by uid desc limit 1;"""

        lastStockData = DB_Fetch(sql, False, "DOC")

        # print(lastStockData)

        stockSoldQty = lastStockData['purchase_qty'] - lastStockData['avail_qty'] # Remaining Stock Hold

        currentStock = float(ui.IQLE_Stock.text())

        if currentStock > stockSoldQty :#and currentStock != lastStockData['purchase_qty'] :
            stockNewDict = dict()
            if lastStockData['mrp'] != float(ui.IQLE_MRP.text()) :
                stockNewDict['mrp'] = float(ui.IQLE_MRP.text())
            if lastStockData['cost_price'] != float(ui.IQLE_PurchaseRate.text()):
                stockNewDict['cost_price'] = float(ui.IQLE_PurchaseRate.text())
            if lastStockData['purchase_qty'] != currentStock:
                stockNewDict['purchase_qty'] = currentStock
            if lastStockData['avail_qty'] != currentStock - stockSoldQty :
                stockNewDict['avail_qty'] = currentStock - stockSoldQty
                ui.IQLE_CurrentStock.setText(str(currentStock - stockSoldQty))

                sql = fr"""update product_info set stock = '{currentStock - stockSoldQty}' where product_id = {Product_ID}"""
                DB_Cmt(sql,False)

                # dbc.execute(sql)
                # db.commit()
                # print(sql,"Finall")

            # print(stockNewDict)

            c_dict = {
                'uid' : lastStockData['uid']
            }

            if len(stockNewDict) > 0:
                # DB_Push_Dict(stockNewDict, 'purchase_info', False)
                DB_Update_Dict(stockNewDict,c_dict,'purchase_info', True)

                Show_Msg_Infomation("Stock Updated", "Stock Details Has been Updated !!!!")

                StockStatus = fr"""(select uid,pdate,product_id,mrp,cost_price,purchase_qty,avail_qty,
                        remark from purchase_info where avail_qty =0 and product_id = {Product_ID} order by uid desc limit 1) 
                        union (select uid,pdate,product_id,mrp,cost_price,purchase_qty,avail_qty,remark from purchase_info 
                        where avail_qty > 0 and product_id = {Product_ID})"""

                # Push_TableView_SqlData('Stock_Model', ui.IQTB_StockEntry, StockStatus)
                Push_TableView_SqlData_Wth_AdjColumName('Stock_Model', ui.IQTB_StockEntry, StockStatus,
                                                        ["UID", "Purchase Date", "Product ID", "MRP", "Cost Price",
                                                         "Total Quantity", "Available Quantity", "Remarks"])

                ui.IQPB_UpdateStock.setEnabled(False)

            else:
                Show_Msg_Infomation("No Stock Update", "No Stock Detail Has been Changed")

        else:
            Show_Msg_Infomation("Can't Alter Stock", "Stock Is added in bill so alter the bill and update the stock")
            # print('No')
            # print(stockSoldQty, currentStock, "No")

    @Exception_Handle
    def Add_Product():

        dict = {
            'barcode' :  int(ui.IQLE_ProductID.text()) if ui.IQLE_BarcodeInput.text() == "" else int(ui.IQLE_BarcodeInput.text()),
            'product_name' : '' if ui.IQLE_ProductName.text() == "" else  ui.IQLE_ProductName.text() ,
            'tamil_name' : ui.IQLE_ProductName.text() if ui.IQLE_TamilName.text() == "" else ui.IQLE_TamilName.text(),
            'cost_price' : 0 if ui.IQLE_PurchaseRate.text() == "" else  float(ui.IQLE_PurchaseRate.text()),
            'mrp' : 0 if ui.IQLE_MRP.text() == "" else float(ui.IQLE_MRP.text()),
            'wholesale' : "" if ui.IQLE_SalesPrice_W.text() == "" else float(ui.IQLE_SalesPrice_W.text()),
            'retail' : "" if ui.IQLE_SalesPrice_R.text() == "" else float(ui.IQLE_SalesPrice_R.text()),
            'uom' : ui.IQCB_UOM.currentText(),
            'active_status' : "Y" if ui.IQCB_Active.currentText() == "Yes" else "N",
            'gst' : 0 if ui.IQLE_GST.text() == "" else float(ui.IQLE_GST.text()),
            'hsn' : 'NA' if ui.IQLE_HsnCode.text() == "" else str(ui.IQLE_HsnCode.text()),
            'stock' : 0 if ui.IQLE_Stock.text() == "" else float(ui.IQLE_Stock.text())
        }
        tbl_nm = ['product_info','purchase_info']

        # uid, pdate, product_id, cost_price, purchase_qty, avail_qty, remark
        stock_dict = {
            'pdate' :Cur_Date_SQL,
            'product_id': int(ui.IQLE_ProductID.text()),
            'cost_price' : 0 if ui.IQLE_PurchaseRate.text() == "" else float(ui.IQLE_PurchaseRate.text()),
            'purchase_qty' : 0 if ui.IQLE_Stock.text() == "" else float(ui.IQLE_Stock.text()),
            'avail_qty': 0 if ui.IQLE_Stock.text() == "" else float(ui.IQLE_Stock.text()),
            'mrp': 0 if ui.IQLE_MRP.text() == "" else float(ui.IQLE_MRP.text()),
            'remark' : "S"
        }

        if "" not in list(dict.values()):
            produtSql,produtValues = DB_Push_Dict_Return(dict,tbl_nm[0],False)

            try:
                dbc.execute(produtSql,produtValues)
                db.commit()

                Show_Msg_Infomation("Adding Product", "Product Has Been Added Successfully")
                
                DB_Push_Dict(stock_dict,tbl_nm[1],False)

                Show_Msg_Infomation("Information", "Stock Has been Added Successfully ")

                Product_IPN = int(ui.IQLE_ProductID.text())
                StockStatus = fr"""(select uid,pdate,product_id,cost_price,purchase_qty,avail_qty,remark from 
                purchase_info where avail_qty = 0 and product_id = {Product_IPN} order by uid desc limit 1) 
                union (select uid,pdate,product_id,cost_price,purchase_qty,avail_qty,remark 
                from purchase_info where avail_qty > 0 and product_id = {Product_IPN})"""

                # Push_TableView_SqlData('Stock_Model', ui.IQTB_StockEntry, StockStatus)
                Push_TableView_SqlData_Wth_AdjColumName('Stock_Model', ui.IQTB_StockEntry, StockStatus,
                    ["UID", "Purchase Date", "Product ID", "MRP", "Cost Price","Total Quantity", 
                    "Available Quantity", "Remarks"])

                sql = fr"""select sum(avail_qty) from purchase_info where product_id = {Product_IPN} 
                                                    and  avail_qty>0 group by product_id"""

                maxi_stock = DB_Fetch(sql, False, "LOE")

                ui.IQLE_CurrentStock.setText(str(0 if len(maxi_stock) == 0 else maxi_stock[0]))
                ui.IQLE_Stock.setText("")

                Product_Viewtbl_SQlData()

            except Exception as e:
                print(e)

                Show_Msg_Infomation("Product Duplicate", "Product Has Been Duplicate")

        else:
            Show_Msg_Infomation("Information", "Please Enter the nessessary Details ")


    @Exception_Handle
    def Update_Product():
        
        try:
            selected_rows = ui.OQTB_Product.selectionModel().selectedRows()
            index = selected_rows[-1]
            Product_IPN = int(ui.OQTB_Product.model().index(index.row(), 0).data())

            actualData = {
            'barcode' : ui.OQTB_Product.model().index(index.row(), 1).data(),
            'product_name':ui.OQTB_Product.model().index(index.row(), 2).data(),
            'tamil_name':ui.OQTB_Product.model().index(index.row(), 3).data(),
            'cost_price':ui.OQTB_Product.model().index(index.row(), 4).data(),
            'mrp':ui.OQTB_Product.model().index(index.row(), 5).data(),
            'wholesale':ui.OQTB_Product.model().index(index.row(), 6).data(),
            'retail':ui.OQTB_Product.model().index(index.row(), 7).data(),
            'gst':ui.OQTB_Product.model().index(index.row(), 8).data(),
            'uom':ui.OQTB_Product.model().index(index.row(), 9).data(),
            'active_status':ui.OQTB_Product.model().index(index.row(), 10).data(),
            'hsn': ui.OQTB_Product.model().index(index.row(), 11).data()
            }

            dict = {
                'barcode': int(ui.IQLE_ProductID.text()) if ui.IQLE_BarcodeInput.text() == "" else int(
                    ui.IQLE_BarcodeInput.text()),
                'product_name': '' if ui.IQLE_ProductName.text() == "" else ui.IQLE_ProductName.text(),
                'tamil_name': ui.IQLE_ProductName.text() if ui.IQLE_TamilName.text() == "" else ui.IQLE_TamilName.text(),
                'cost_price': 0.0 if ui.IQLE_PurchaseRate.text() == "" else float(ui.IQLE_PurchaseRate.text()),
                'mrp': 0.0 if ui.IQLE_MRP.text() == "" else float(ui.IQLE_MRP.text()),
                'wholesale': "" if ui.IQLE_SalesPrice_W.text() == "" else float(ui.IQLE_SalesPrice_W.text()),
                'retail': "" if ui.IQLE_SalesPrice_R.text() == "" else float(ui.IQLE_SalesPrice_R.text()),
                'uom': ui.IQCB_UOM.currentText(),
                'active_status': "Y" if ui.IQCB_Active.currentText() == "Yes" else "N",
                'gst': 0.0 if ui.IQLE_GST.text() == "" else str(ui.IQLE_GST.text()),
                'hsn': 'NA' if ui.IQLE_HsnCode.text() == "" else str(ui.IQLE_HsnCode.text())
            }

            tbl_nm = ['product_info', 'purchase_info']
            # print(dict.values())

            c_dict = {
                'product_id': int(ui.IQLE_ProductID.text()),
            }

            stock_dict = {
                'pdate': Cur_Date_SQL,
                'product_id': int(ui.IQLE_ProductID.text()),
                'mrp': 0 if ui.IQLE_MRP.text() == "" else float(ui.IQLE_MRP.text()),
                'cost_price': 0 if ui.IQLE_PurchaseRate.text() == "" else float(ui.IQLE_PurchaseRate.text()),
                'purchase_qty': 0 if ui.IQLE_Stock.text() == "" else float(ui.IQLE_Stock.text()),
                'avail_qty': 0 if ui.IQLE_Stock.text() == "" else float(ui.IQLE_Stock.text()),
                'remark': "S"
            }

            for key, value in dict.items():
                if str(actualData[key]) != str(value):
                    sql = f"UPDATE {tbl_nm[0]} SET {key} = '{value}' WHERE {list(c_dict.keys())[0]} = {list(c_dict.values())[0]}"
                    DB_Cmt(sql,False)

            Product_Viewtbl_SQlData()
            Show_Msg_Infomation("Updating Product", "Product Has Been Updated Successfully")

            if ui.IQLE_Stock.text() not in ["",None]:

                DB_Push_Dict(stock_dict,tbl_nm[1],False)

                Show_Msg_Infomation("Stock Added", "Stock Has been Added Successfully ")

                StockStatus = fr"""(select uid,pdate,product_id,cost_price,purchase_qty,avail_qty,remark from
                purchase_info where avail_qty =0 and product_id = {Product_IPN} order by uid desc limit 1) union (select
                uid,pdate,product_id,cost_price,purchase_qty,avail_qty,remark from purchase_info where avail_qty > 0 and product_id = {Product_IPN})"""

                Push_TableView_SqlData_Wth_AdjColumName('Stock_Model', ui.IQTB_StockEntry, StockStatus,
                                                        ["UID", "Purchase Date", "Product ID", "MRP", "Cost Price",
                                                        "Total Quantity", "Available Quantity", "Remarks"])

                sql = fr"select sum(avail_qty) from purchase_info where product_id = {Product_IPN} and  avail_qty>0 group by product_id"
                maxi_stock = DB_Fetch(sql, False, "LOE")

                ui.IQLE_CurrentStock.setText(str(0 if len(maxi_stock) == 0 else maxi_stock[0]))
                ui.IQLE_Stock.setText("")
                sql = fr"update product_info set stock = {0 if len(maxi_stock) == 0 else maxi_stock[0]} where product_id = {Product_IPN}"
                DB_Cmt(sql,False)

        except Exception as e:
            print(e)
            Show_Msg_Infomation("Selection Disconnected", fr"The selected Product From the Product Table")
            

    @Exception_Handle
    def Delete_Product_Data():
        selected_rows = ui.OQTB_Product.selectionModel().selectedRows()

        if len(selected_rows) >0:
            index = selected_rows[-1]
            Product_IPN = ui.OQTB_Product.model().index(index.row(), 0).data()

            if get_info_msg("Delete Information"," Do You Want to Delete the Selected\n\n" +
                                                  " Product ID :" + fr"{Product_IPN}  " +
                                    f" \n Product Name :{ui.OQTB_Product.model().index(index.row(), 2).data()}"):
                # dbc = db.cursor()
                sql = fr"update product_info set active_status = 'D' where product_id = '{Product_IPN}'"
                DB_Cmt(sql,False)
                # dbc.execute(sql)
                # db.commit()

                Show_Msg_Infomation("Deleted Information", fr"The selected Product ID : {Product_IPN}" + "\n\n" 
                                        fr"Product Name : {ui.OQTB_Product.model().index(index.row(), 2).data()}"
                                                            +"\n\n"+ fr"Deleted Successfully ")

                Update_Property(ui.Item_Frame, "Clear", "IQLE", True)
                Update_Property(ui.Item_Frame, "Clear", "IQTE", True)

                ui.IQCB_Active.clear()
                ui.IQCB_UOM.clear()

                ui.IQCB_Active.setEnabled(True)
                ui.IQCB_UOM.setEnabled(True)

                ui.IQCB_Active.addItems(Active_Status)
                ui.IQCB_UOM.addItems(Units_List)

                Product_Viewtbl_SQlData()

                ui.IQLE_ProductID.setReadOnly(True)
                ui.IQLE_ProductID.setText(str(Maximum_Product_ID()))

                StockStatus = fr"""select uid,pdate,product_id,cost_price,purchase_qty,avail_qty,remark 
                from purchase_info where limit 0"""
                # print(StockStatus, 'StockStatus')
                # Push_TableView_SqlData('Stock_Model', ui.IQTB_StockEntry, StockStatus)
                Push_TableView_SqlData_Wth_AdjColumName('Stock_Model', ui.IQTB_StockEntry, StockStatus,
                                                        ["UID", "Purchase Date", "Product ID", "MRP", "Cost Price",
                                                         "Total Quantity", "Available Quantity", "Remarks"])


            else:
                Show_Msg_Infomation("Delete Information", "........The Selected Product Is Not Deleted ........")

        else:
            Show_Msg_Infomation("Select The Product","........Please Select the Product to be Deleted........")

        ui.OQTB_Product.selectionModel().clearSelection()


    #------------ Generic/Supporting Definitions ----------------------
    @Exception_Handle
    def Product_Viewtbl_SQlData():
        SQL_Product = """select product_id,barcode,product_name,tamil_name,cost_price,mrp,wholesale,retail,gst,uom,
        active_status,hsn from product_info where active_status not in ('D') order by product_name"""
        Push_TableView_SqlData_Wth_AdjColumName('Product_Model', ui.OQTB_Product, SQL_Product,
                                                ['Product ID','Barcode','Product Name','Tamil Name','Cost Price','MRP',
                                                 'Wholesale Price','Retail Price','GST','UOM','Status','HSN'])


    @Exception_Handle
    def Maximum_Product_ID():
        sql = fr"select ifnull(max(product_id)+1,1) from product_info"
        Maxi_Prod_ID = DB_Fetch(sql, False, "LOE")
        return str(Maxi_Prod_ID[-1])

    @Exception_Handle   
    def TamilKeyboardData():
        tamilWindow.show()
        if ui.IQLE_TamilName.text() not in [None,""]:
            tamilWindow.textbox.setText(ui.IQLE_TamilName.text())


    ### General Code Running
    Product_Viewtbl_SQlData()
    Adjust_Table_Width(ui.OQTB_Product, [0, 8, 15, 15, 10, 10, 10, 10, 0, 5, 0, 0])

    ui.IQLE_ProductID.setText(str(Maximum_Product_ID()))


    #------------------Function & Connection ------------------------
    StockStatus = fr""" select uid,pdate,product_id,mrp,cost_price,purchase_qty,avail_qty,remark from 
    purchase_info where product_id = '' """

    # print(StockStatus,'StockStatus')
    Push_TableView_SqlData_Wth_AdjColumName('Stock_Model', ui.IQTB_StockEntry, StockStatus,
                                            ["UID","Purchase Date","Product ID", "MRP","Cost Price",
                                             "Total Quantity","Available Quantity", "Remarks"])

    Adjust_Table_Width(ui.IQTB_StockEntry, [0, 15, 0, 10, 15, 15, 15, 10])


    ui.OQTB_Product.clicked.connect(lambda: On_Clicked_Product_ViewTbl())

    prod_filter_timer = QtCore.QTimer()
    prod_filter_timer.setSingleShot(True)
    prod_filter_timer.timeout.connect(Filter_Product_ViewTbl)
    ui.OQLE_ProductFilter.textChanged.connect(lambda: prod_filter_timer.start(150))

    ui.IQCB_Add.stateChanged.connect(lambda: Enable_Add_Product())

    ui.IQCB_Update.stateChanged.connect(lambda: Enable_Update_Product())

    ui.IQCB_UpdateStock.stateChanged.connect(lambda: Enable_Stock_Product())

    ui.IQPB_UpdateStock.clicked.connect(lambda: Update_Previous_StockData())

    ui.IQPB_AddProduct.clicked.connect(lambda: Add_Product())

    ui.IQPB_UpdateProduct.clicked.connect(lambda: Update_Product())

    ui.IQPB_DeleteProduct.clicked.connect(lambda: Delete_Product_Data())
    ui.IQPB_TamilKeyboard.clicked.connect(lambda: TamilKeyboardData())

    ui.IQPB_ClearProduct.clicked.connect(lambda : Enable_Add_Product() )


if __name__ == "__main__":
    Item_Master_FN()
    Itm_Mtr.showMaximized()
    sys.exit(app.exec_())