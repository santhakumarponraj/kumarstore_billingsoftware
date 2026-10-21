from Env import *


@Exception_Handle
def Invoice_Register_FN():
    print("======Invoice Register Running=========")

    ui = Inv_RegUI

    @Exception_Handle
    def Customer_Detail_data():
        sqlCustomer = fr"""SELECT ci.cid, ci.phone_no, ci.name, ci.address,
                IF(ci.wholesale = 1, 'W', 'R') AS ws,
                COALESCE(SUM(im.amt_payabe), 0) - COALESCE(SUM(im.amt_received), 0) AS outstanding_amount
                FROM customer_info ci
                LEFT JOIN invoice_master im
                    ON ci.phone_no = im.mob_no
                    AND im.active_status IN ('Y', 'P')
                    AND im.fy = '{FY_Gen(Cur_Date)}'
                GROUP BY ci.cid, ci.phone_no, ci.name, ci.address, ci.wholesale
            """
        Push_TableView_SqlData_Wth_AdjColumName(
            'CustomerDetail_Model', ui.IQTV_CustomerDetail, sqlCustomer,
            ['Customer ID', 'Phone Number', 'Customer Name', 'Address', 'Type', 'Total Outstanding']
        )

    @Exception_Handle
    def Filter_Customer_ViewTbl():
        filterTxt = ui.IQLE_FilterCustomerTable.text()

        if filterTxt == "":
            # No filter — show all customers with outstanding (keep JOIN condition in ON, not WHERE)
            sqlFilter = fr"""SELECT ci.cid, ci.phone_no, ci.name, ci.address,
                    IF(ci.wholesale = 1, 'W', 'R') AS ws,
                    COALESCE(SUM(im.amt_payabe), 0) - COALESCE(SUM(im.amt_received), 0) AS outstanding_amount
                    FROM customer_info ci
                    LEFT JOIN invoice_master im
                        ON ci.phone_no = im.mob_no
                        AND im.active_status IN ('Y', 'P')
                        AND im.fy = '{FY_Gen(Cur_Date)}'
                    GROUP BY ci.cid, ci.phone_no, ci.name, ci.address, ci.wholesale
                """
        else:
            sqlFilter = fr"""SELECT ci.cid, ci.phone_no, ci.name, ci.address,
                    IF(ci.wholesale = 1, 'W', 'R') AS ws,
                    COALESCE(SUM(im.amt_payabe), 0) - COALESCE(SUM(im.amt_received), 0) AS outstanding_amount
                    FROM customer_info ci
                    LEFT JOIN invoice_master im
                        ON ci.phone_no = im.mob_no
                        AND im.active_status IN ('Y', 'P')
                        AND im.fy = '{FY_Gen(Cur_Date)}'
                    WHERE (ci.cid LIKE '%{filterTxt}%'
                        OR ci.phone_no LIKE '%{filterTxt}%'
                        OR ci.name LIKE '%{filterTxt}%')
                    GROUP BY ci.cid, ci.phone_no, ci.name, ci.address, ci.wholesale
                """

        Push_TableView_SqlData_Wth_AdjColumName(
            'CustomerDetail_Model', ui.IQTV_CustomerDetail, sqlFilter,
            ['Customer ID', 'Phone Number', 'Customer Name', 'Address', 'Type', 'Total Outstanding']
        )

    @Exception_Handle
    def On_Click_Customer_Details():
        selected_rows = ui.IQTV_CustomerDetail.selectionModel().selectedRows()
        index = selected_rows[-1]
        customerUID = ui.IQTV_CustomerDetail.model().index(index.row(), 0).data()
        phoneNumber = ui.IQTV_CustomerDetail.model().index(index.row(), 1).data()

        if ui.IQCB_DateRange.isChecked():

            sqlInvoice = fr"""SELECT gdate, fy,
                CASE WHEN active_status = 'Y' THEN inv_no
                     WHEN active_status = 'P' THEN CONCAT('PE-', inv_no)
                END AS inv_no,
                mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                FROM invoice_master
                WHERE mob_no = '{phoneNumber}'
                  AND active_status IN ('Y', 'P')
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND gdate BETWEEN '{ui.IQDE_From.date().toString("yyyy-MM-dd")}'
                                AND '{ui.IQDE_To.date().toString("yyyy-MM-dd")}'
                """
            Push_TableView_SqlData_Wth_AdjColumName(
                'InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                 'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
            )

            # BUG FIX: fy filter was placed in wrong position, breaking the WHERE clause
            currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                FROM invoice_master
                WHERE mob_no = '{phoneNumber}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND gdate BETWEEN '{ui.IQDE_From.date().toString("yyyy-MM-dd")}'
                                AND '{ui.IQDE_To.date().toString("yyyy-MM-dd")}'
                  AND active_status IN ('Y', 'P')
                GROUP BY mob_no"""

            beforeValue = fr"""SELECT SUM(amt_payabe) - SUM(amt_received)
                FROM invoice_master
                WHERE mob_no = '{phoneNumber}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND gdate < '{ui.IQDE_From.date().toString("yyyy-MM-dd")}'
                  AND active_status IN ('Y', 'P')
                GROUP BY mob_no"""

            dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")
            dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")

            totalInvAmt    = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[0]  is None else dateBtwnValue[0]
            totalPayedAmt  = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[1]  is None else dateBtwnValue[1]
            totalOpeningAmt = 0 if len(dateBeforeValue) == 0 or dateBeforeValue[0] is None else dateBeforeValue[0]
            totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

            ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
            ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
            ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
            ui.IQLE_InvAmount.setText(str(totalInvAmt))

        else:
            sqlInvoice = fr"""SELECT gdate, fy,
                CASE WHEN active_status = 'Y' THEN inv_no
                     WHEN active_status = 'P' THEN CONCAT('PE-', inv_no)
                END AS inv_no,
                mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                FROM invoice_master
                WHERE mob_no = '{phoneNumber}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND active_status IN ('Y', 'P')
                """
            Push_TableView_SqlData_Wth_AdjColumName(
                'InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                 'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
            )

            currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                FROM invoice_master
                WHERE mob_no = '{phoneNumber}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND active_status IN ('Y', 'P')
                GROUP BY mob_no"""

            dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

            totalInvAmt   = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] is None else dateBtwnValue[0]
            totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] is None else dateBtwnValue[1]
            totalOpeningAmt = 0
            totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

            ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
            ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
            ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
            ui.IQLE_InvAmount.setText(str(totalInvAmt))

        Adjust_Table_Width(ui.IQTV_Register, [10, 12, 13, 12, 12, 12, 10, 12, 14])

    @Exception_Handle
    def Enable_GuestDetails():
        if ui.IQCB_NoCustomerEntry.isChecked():
            if ui.IQCB_DateRange.isChecked():

                sql = fr"""SELECT gdate, fy, inv_no, mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                    FROM invoice_master
                    WHERE gdate BETWEEN '{ui.IQDE_From.date().toString("yyyy-MM-dd")}'
                                    AND '{ui.IQDE_To.date().toString("yyyy-MM-dd")}'
                      AND fy = '{FY_Gen(Cur_Date)}'
                      AND mob_no = 'NA'
                      AND active_status IN ('Y', 'P')
                    """
                Push_TableView_SqlData_Wth_AdjColumName(
                    'InvoiceMaster_Model', ui.IQTV_Register, sql,
                    ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                     'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
                )

                currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                    FROM invoice_master
                    WHERE mob_no = 'NA'
                      AND fy = '{FY_Gen(Cur_Date)}'
                      AND gdate BETWEEN '{ui.IQDE_From.date().toString("yyyy-MM-dd")}'
                                    AND '{ui.IQDE_To.date().toString("yyyy-MM-dd")}'
                      AND active_status IN ('Y', 'P')
                    GROUP BY mob_no"""

                beforeValue = fr"""SELECT SUM(amt_payabe) - SUM(amt_received)
                    FROM invoice_master
                    WHERE mob_no = 'NA'
                      AND fy = '{FY_Gen(Cur_Date)}'
                      AND gdate < '{ui.IQDE_From.date().toString("yyyy-MM-dd")}'
                      AND active_status IN ('Y', 'P')
                    GROUP BY mob_no"""

                dateBtwnValue  = DB_Fetch(currentWithDateSql, False, "LOE")
                dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")

                totalInvAmt    = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[0]  is None else dateBtwnValue[0]
                totalPayedAmt  = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[1]  is None else dateBtwnValue[1]
                # BUG FIX: was using `and` (IndexError when list empty), must be `or`
                totalOpeningAmt = 0 if len(dateBeforeValue) == 0 or dateBeforeValue[0] is None else dateBeforeValue[0]
                totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

                ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
                ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
                ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
                ui.IQLE_InvAmount.setText(str(totalInvAmt))

            else:
                noDataQuery = fr"""SELECT inv_no, mob_no, fy, gdate, sales_man, pay_mode
                    FROM invoice_master LIMIT 0"""
                Push_TableView_SqlData_Wth_AdjColumName(
                    'CustomerDetail_Model', ui.IQTV_CustomerDetail, noDataQuery,
                    ['Customer ID', 'Phone Number', 'Customer Name', 'Address', 'Type', 'Total Outstanding']
                )

                # BUG FIX: added active_status and fy filters (were missing)
                NoCustomerQuery = fr"""SELECT gdate, fy, inv_no, mob_no, sales_man, pay_mode,
                    discount, amt_payabe, amt_received
                    FROM invoice_master
                    WHERE mob_no = 'NA'
                      AND active_status IN ('Y', 'P')
                      AND fy = '{FY_Gen(Cur_Date)}'
                    """
                Push_TableView_SqlData_Wth_AdjColumName(
                    'InvoiceMaster_Model_NoCustomer', ui.IQTV_Register, NoCustomerQuery,
                    ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                     'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
                )

                currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                    FROM invoice_master
                    WHERE mob_no = 'NA'
                      AND fy = '{FY_Gen(Cur_Date)}'
                      AND active_status IN ('Y', 'P')
                    GROUP BY mob_no"""

                dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

                # BUG FIX: added length check before indexing
                totalInvAmt   = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] is None else dateBtwnValue[0]
                totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] is None else dateBtwnValue[1]
                totalOpeningAmt = 0
                totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

                ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
                ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
                ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
                ui.IQLE_InvAmount.setText(str(totalInvAmt))

        else:
            Customer_Detail_data()
            NoCustomerQuery = fr"""SELECT gdate, fy, inv_no, mob_no, sales_man, pay_mode,
                discount, amt_payabe, amt_received
                FROM invoice_master LIMIT 0"""
            Push_TableView_SqlData_Wth_AdjColumName(
                'InvoiceMaster_Model_NoCustomer', ui.IQTV_Register, NoCustomerQuery,
                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                 'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
            )

            currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                FROM invoice_master
                WHERE active_status IN ('Y', 'P')
                  AND fy = '{FY_Gen(Cur_Date)}'"""

            dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

            totalInvAmt   = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] is None else dateBtwnValue[0]
            totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] is None else dateBtwnValue[1]
            totalOpeningAmt = 0
            totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

            ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
            ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
            ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
            ui.IQLE_InvAmount.setText(str(totalInvAmt))

    @Exception_Handle
    def Enable_Date_Filter():
        if ui.IQCB_DateRange.isChecked():
            ui.IQDE_From.setEnabled(True)
            ui.IQDE_To.setEnabled(True)
        else:
            ui.IQDE_From.setEnabled(False)
            ui.IQDE_To.setEnabled(False)
            ui.IQDE_From.setDate(QDate(Cur_Date.year, Cur_Date.month, 1))
            ui.IQDE_To.setDate(QDate.currentDate())

        Enable_GuestDetails()

    @Exception_Handle
    def Changing_fromNto_Date():
        fromDate = ui.IQDE_From.date().toString("yyyy-MM-dd")
        toDate   = ui.IQDE_To.date().toString("yyyy-MM-dd")

        if ui.IQCB_NoCustomerEntry.isChecked():
            sql = fr"""SELECT gdate, fy, inv_no, mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                FROM invoice_master
                WHERE gdate BETWEEN '{fromDate}' AND '{toDate}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND mob_no = 'NA'
                  AND active_status IN ('Y', 'P')
                """
            Push_TableView_SqlData_Wth_AdjColumName(
                'InvoiceMaster_Model', ui.IQTV_Register, sql,
                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                 'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
            )

            currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                FROM invoice_master
                WHERE mob_no = 'NA'
                  AND gdate BETWEEN '{fromDate}' AND '{toDate}'
                  AND active_status IN ('Y', 'P')
                  AND fy = '{FY_Gen(Cur_Date)}'
                GROUP BY mob_no"""

            beforeValue = fr"""SELECT SUM(amt_payabe) - SUM(amt_received)
                FROM invoice_master
                WHERE mob_no = 'NA'
                  AND gdate < '{fromDate}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND active_status IN ('Y', 'P')
                GROUP BY mob_no"""

            dateBtwnValue  = DB_Fetch(currentWithDateSql, False, "LOE")
            dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")

            totalInvAmt   = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[0]  is None else dateBtwnValue[0]
            totalPayedAmt = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[1]  is None else dateBtwnValue[1]
            # BUG FIX: original had `> 0 and value is None` — inverted length check
            totalOpeningAmt = 0 if len(dateBeforeValue) == 0 or dateBeforeValue[0] is None else dateBeforeValue[0]
            totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

            ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
            ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
            ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
            ui.IQLE_InvAmount.setText(str(totalInvAmt))

        else:
            sql = fr"""SELECT gdate, fy, inv_no, mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                FROM invoice_master
                WHERE gdate BETWEEN '{fromDate}' AND '{toDate}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND active_status IN ('Y', 'P')"""
            Push_TableView_SqlData_Wth_AdjColumName(
                'InvoiceMaster_Model', ui.IQTV_Register, sql,
                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                 'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
            )

            currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                FROM invoice_master
                WHERE gdate BETWEEN '{fromDate}' AND '{toDate}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND active_status IN ('Y', 'P')"""

            beforeValue = fr"""SELECT SUM(amt_payabe) - SUM(amt_received)
                FROM invoice_master
                WHERE gdate < '{fromDate}'
                  AND fy = '{FY_Gen(Cur_Date)}'
                  AND active_status IN ('Y', 'P')"""

            dateBtwnValue  = DB_Fetch(currentWithDateSql, False, "LOE")
            dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")

            totalInvAmt    = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[0]  is None else dateBtwnValue[0]
            totalPayedAmt  = 0 if len(dateBtwnValue)  == 0 or dateBtwnValue[1]  is None else dateBtwnValue[1]
            totalOpeningAmt = 0 if len(dateBeforeValue) == 0 or dateBeforeValue[0] is None else dateBeforeValue[0]
            totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

            ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
            ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
            ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
            ui.IQLE_InvAmount.setText(str(totalInvAmt))

    @Exception_Handle
    def Add_Payment(customerUID, phoneNumber, customerName, lastInvoice):
        if get_info_msg("Confirmation Window Adding",
                        fr"Do You want to Add rs.{payUIUI.IQLE_Amount.text()}"
                        + "\n " + fr"For the Customer Number : {phoneNumber} and Customer Name : {customerName}"):

            paydictData = {
                'fy': fr"{int(Cur_Date_YR)}-{int(Cur_Date_YR) + 1}" if int(Cur_Date_MM) > 3
                      else fr"{int(Cur_Date_YR) - 1}-{int(Cur_Date_YR)}",
                'inv_no': lastInvoice,
                'gdate': payUIUI.IQDE_GenDate.date().toString("yyyy-MM-dd"),
                'mob_no': phoneNumber,
                'sales_man': "NA",
                'pay_mode': payUIUI.IQCB_PayMode.currentText(),
                'discount': 0,
                'amt_payabe': 0,
                'amt_received': payUIUI.IQLE_Amount.text(),
                'active_status': "P"
            }
            DB_Push_Dict(paydictData, "invoice_master", False)
            payUI.close()

            sqlInvoice = fr"""SELECT gdate, fy,
                CASE WHEN active_status = 'Y' THEN inv_no
                     WHEN active_status = 'P' THEN CONCAT('PE-', inv_no)
                END AS inv_no,
                mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                FROM invoice_master
                WHERE mob_no = '{phoneNumber}'
                  AND active_status IN ('Y', 'P')
                """
            Push_TableView_SqlData_Wth_AdjColumName(
                'InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                 'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
            )

            currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                FROM invoice_master
                WHERE mob_no = '{phoneNumber}'
                  AND active_status IN ('Y', 'P')
                GROUP BY mob_no"""

            dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

            totalInvAmt   = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] is None else dateBtwnValue[0]
            totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] is None else dateBtwnValue[1]
            totalOpeningAmt = 0
            totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

            ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
            ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
            ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
            ui.IQLE_InvAmount.setText(str(totalInvAmt))
            Customer_Detail_data()

        else:
            show_info_msg("Status Message", "Amount Is Not Added")

    @Exception_Handle
    def Update_Customer(customerUID, regMobno, customerName, regInvoice):
        if get_info_msg("Confirmation Window Update",
                        fr"Do You want to Add rs.{payUIUI.IQLE_Amount.text()}"
                        + "\n " + fr"For the Customer Number : {regMobno} and Customer Name : {customerName}"):

            updateDictData = {
                'gdate': payUIUI.IQDE_GenDate.date().toString("yyyy-MM-dd"),
                'pay_mode': payUIUI.IQCB_PayMode.currentText(),
                'amt_received': payUIUI.IQLE_Amount.text()
            }
            updateUID = {
                'inv_no': regInvoice,
                'active_status': "P"
            }
            DB_Update_Dict(updateDictData, updateUID, 'invoice_master', False)
            payUI.close()

            sqlInvoice = fr"""SELECT gdate, fy,
                CASE WHEN active_status = 'Y' THEN inv_no
                     WHEN active_status = 'P' THEN CONCAT('PE-', inv_no)
                END AS inv_no,
                mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                FROM invoice_master
                WHERE mob_no = '{regMobno}'
                  AND active_status IN ('Y', 'P')
                """
            Push_TableView_SqlData_Wth_AdjColumName(
                'InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                 'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
            )

            currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                FROM invoice_master
                WHERE mob_no = '{regMobno}'
                  AND active_status IN ('Y', 'P')
                GROUP BY mob_no"""

            dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

            totalInvAmt   = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] is None else dateBtwnValue[0]
            totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] is None else dateBtwnValue[1]
            totalOpeningAmt = 0
            totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

            ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
            ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
            ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
            ui.IQLE_InvAmount.setText(str(totalInvAmt))
            Customer_Detail_data()

        else:
            show_info_msg("Status Message", "Amount Is Not Updated")

    @Exception_Handle
    def AddUpdateDelete_PaymentEntry():
        selected_rows = ui.IQTV_CustomerDetail.selectionModel().selectedRows()

        if len(selected_rows) > 0 and ui.IQCB_AddUpdateDelete.currentText() == "Add":
            index = selected_rows[-1]
            customerUID  = ui.IQTV_CustomerDetail.model().index(index.row(), 0).data()
            phoneNumber  = ui.IQTV_CustomerDetail.model().index(index.row(), 1).data()
            customerName = ui.IQTV_CustomerDetail.model().index(index.row(), 2).data()

            sqllastInvoice = DB_Fetch(
                fr"""SELECT MAX(inv_no) FROM invoice_master WHERE active_status IN ('P', 'NP')""",
                False, "LOE"
            )[0]
            lastInvoice = 1 if sqllastInvoice is None else int(sqllastInvoice) + 1

            payUI.show()
            payUIUI.IQDE_GenDate.setDate(QDate.currentDate())
            payUIUI.IQLE_PhoneNo.setText(str(phoneNumber))
            payUIUI.IQLE_CustomerName.setText(str(customerName))
            payUIUI.IQLE_CustomerUID.setText(str(customerUID))
            payUIUI.IQLE_InvNumber.setText(fr"PE-{str(lastInvoice)}")
            payUIUI.IQLE_Amount.clear()

            try:
                payUIUI.IQPB_Action.clicked.disconnect()
            except:
                pass

            payUIUI.IQPB_Action.clicked.connect(
                lambda: Add_Payment(customerUID, phoneNumber, customerName, lastInvoice)
            )

        elif len(selected_rows) > 0 and ui.IQCB_AddUpdateDelete.currentText() == "Update":
            index = selected_rows[-1]
            customerUID  = ui.IQTV_CustomerDetail.model().index(index.row(), 0).data()
            phoneNumber  = ui.IQTV_CustomerDetail.model().index(index.row(), 1).data()
            customerName = ui.IQTV_CustomerDetail.model().index(index.row(), 2).data()

            selected_rows_regtbl = ui.IQTV_Register.selectionModel().selectedRows()

            if len(selected_rows_regtbl) > 0:
                regindex   = selected_rows_regtbl[-1]
                regInvoice = (ui.IQTV_Register.model().index(regindex.row(), 2).data()).replace("PE-", "")
                regMobno   = ui.IQTV_Register.model().index(regindex.row(), 3).data()
                regSaleMan = ui.IQTV_Register.model().index(regindex.row(), 4).data()

                if regSaleMan == "NA":
                    sql = fr"""SELECT gdate, pay_mode, amt_received
                        FROM invoice_master
                        WHERE active_status = 'P'
                          AND inv_no = '{regInvoice}'"""

                    updateData = DB_Fetch(sql, False, "LOE")
                    payUI.show()

                    # BUG FIX: QDate() can't parse a date object directly — use QDate.fromString or pass y/m/d ints
                    parsedDate = QDate.fromString(str(updateData[0]), "yyyy-MM-dd")
                    payUIUI.IQDE_GenDate.setDate(parsedDate)
                    payUIUI.IQLE_PhoneNo.setText(str(regMobno))
                    payUIUI.IQLE_CustomerName.setText(str(customerName))
                    payUIUI.IQLE_CustomerUID.setText(str(customerUID))
                    payUIUI.IQLE_InvNumber.setText(fr"PE-{str(regInvoice)}")
                    payUIUI.IQLE_Amount.setText(str(updateData[2]))
                    payUIUI.IQCB_PayMode.setCurrentIndex(["Cash", "Gpay", "NIFT"].index(updateData[1]))

                    try:
                        payUIUI.IQPB_Action.clicked.disconnect()
                    except:
                        pass

                    payUIUI.IQPB_Action.clicked.connect(
                        lambda: Update_Customer(customerUID, regMobno, customerName, regInvoice)
                    )

                else:
                    show_info_msg("Information", "Please Select the Payment Entry Data to Update")
            else:
                show_info_msg("Information", "Please Select the Customer from Register Table")

        elif len(selected_rows) > 0 and ui.IQCB_AddUpdateDelete.currentText() == "Delete":
            dindex = selected_rows[-1]

            dcustomerUID  = ui.IQTV_CustomerDetail.model().index(dindex.row(), 0).data()
            dphoneNumber  = ui.IQTV_CustomerDetail.model().index(dindex.row(), 1).data()
            dcustomerName = ui.IQTV_CustomerDetail.model().index(dindex.row(), 2).data()

            delselected_rows_Reg = ui.IQTV_Register.selectionModel().selectedRows()

            if len(delselected_rows_Reg) > 0:
                delindex    = delselected_rows_Reg[-1]
                delInvoice  = ui.IQTV_Register.model().index(delindex.row(), 2).data()
                delMobno    = ui.IQTV_Register.model().index(delindex.row(), 3).data()
                delSaleMan  = ui.IQTV_Register.model().index(delindex.row(), 4).data()
                delGivenamt = ui.IQTV_Register.model().index(delindex.row(), 8).data()

                if delSaleMan == "NA":
                    if get_info_msg("Confirmation Window Delete",
                                    "Are You Sure Do you Want To Delete\n\n"
                                    + fr"Invoice Number : {delInvoice}" + "\n"
                                    + fr"Customer UID : {dcustomerUID}" + "\n"
                                    + fr"Customer Name : {dcustomerName}" + "\n"
                                    + fr"Customer Number : {dphoneNumber}" + "\n"
                                    + fr"Given Amount : {delGivenamt}"):

                        deleteDictData = {'active_status': "NP"}
                        deletedUID = {
                            'inv_no': delInvoice.replace("PE-", ""),
                            'active_status': "P"
                        }
                        DB_Update_Dict(deleteDictData, deletedUID, 'invoice_master', False)

                        sqlInvoice = fr"""SELECT gdate, fy,
                            CASE WHEN active_status = 'Y' THEN inv_no
                                 WHEN active_status = 'P' THEN CONCAT('PE-', inv_no)
                            END AS inv_no,
                            mob_no, sales_man, pay_mode, discount, amt_payabe, amt_received
                            FROM invoice_master
                            WHERE mob_no = '{delMobno}'
                              AND active_status IN ('Y', 'P')"""

                        Push_TableView_SqlData_Wth_AdjColumName(
                            'InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
                            ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number',
                             'SaleMan Name', 'Payment Mode', 'Discount', 'Total Amount', 'Amount Received']
                        )

                        currentWithDateSql = fr"""SELECT SUM(amt_payabe), SUM(amt_received)
                            FROM invoice_master
                            WHERE mob_no = '{delMobno}'
                              AND active_status IN ('Y', 'P')
                            GROUP BY mob_no"""

                        dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

                        totalInvAmt   = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] is None else dateBtwnValue[0]
                        totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] is None else dateBtwnValue[1]
                        totalOpeningAmt = 0
                        totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

                        ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
                        ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
                        ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
                        ui.IQLE_InvAmount.setText(str(totalInvAmt))
                        Customer_Detail_data()

                    else:
                        show_info_msg("Status Message", "Amount Is Not Deleted")

                else:
                    show_info_msg("Information", "Please Select the Payment Entry Data to Delete")
            else:
                show_info_msg("Information", "Please Select the Customer from Register Table For Deleting")

        else:
            show_info_msg("Select the Customer", "Please Select the Customer Details")

    ### General Functions

    Customer_Detail_data()

    ui.IQDE_From.setDate(QDate(Cur_Date.year, Cur_Date.month, 1))
    ui.IQDE_To.setDate(QDate.currentDate())

    Adjust_Table_Width(ui.IQTV_CustomerDetail, [11, 13, 15, 15, 5, 12])
    Adjust_Table_Width(ui.IQTV_Register, [10, 12, 13, 12, 12, 12, 10, 12, 14])

    ### Signal Connections

    ui.IQLE_FilterCustomerTable.textChanged.connect(lambda: Filter_Customer_ViewTbl())
    ui.IQTV_CustomerDetail.clicked.connect(lambda: On_Click_Customer_Details())
    ui.IQCB_DateRange.stateChanged.connect(lambda: Enable_Date_Filter())
    ui.IQCB_NoCustomerEntry.stateChanged.connect(lambda: Enable_GuestDetails())
    ui.IQDE_From.dateChanged.connect(lambda: Changing_fromNto_Date())
    ui.IQDE_To.dateChanged.connect(lambda: Changing_fromNto_Date())
    ui.IQPB_PaymentEntry.clicked.connect(lambda: AddUpdateDelete_PaymentEntry())


if __name__ == "__main__":
    Invoice_Register_FN(Inv_Reg)
    Inv_Reg.showMaximized()
    sys.exit(app.exec_())


















# from Env import *


# @Exception_Handle
# def Invoice_Register_FN():
#     print("======Invoice Register Running=========")

#     ui = Inv_RegUI

#     @Exception_Handle
#     def Customer_Detail_data():
#         sqlCustomer = fr"""SELECT ci.cid,ci.phone_no,ci.name,ci.address,IF(ci.wholesale = 1 ,'W','R') AS ws,
#                 COALESCE(SUM(im.amt_payabe), 0) - COALESCE(SUM(im.amt_received), 0) AS outstanding_amount
#                 FROM customer_info ci
#                 LEFT JOIN invoice_master im
#                 ON ci.phone_no = im.mob_no
#                 and im.active_status in ('Y','P') and im.fy = '{FY_Gen(Cur_Date)}' 
#                 GROUP BY ci.cid, ci.phone_no, ci.name, ci.address
#             """
#         # sqlCustomer = """select cid,phone_no,name,address,wholesale,if(wholesale = 1 ,'W','R') as ws from customer_info"""
#         Push_TableView_SqlData_Wth_AdjColumName('CustomerDetail_Model', ui.IQTV_CustomerDetail, sqlCustomer,
#              ['Customer ID', 'Phone Number', 'Customer Name', 'Address','Type', 'Total Outstanding'])

#     @Exception_Handle
#     def Filter_Customer_ViewTbl():

#         filterTxt = ui.IQLE_FilterCustomerTable.text()

#         if filterTxt == "":

#             sqlFilter = fr"""SELECT ci.cid,ci.phone_no,ci.name,ci.address,ci.wholesale,IF(ci.wholesale = 1 ,'W','R') AS ws,
#                     COALESCE(SUM(im.amt_payabe), 0) - COALESCE(SUM(im.amt_received), 0) AS outstanding_amount
#                     FROM customer_info ci
#                     LEFT JOIN invoice_master im 
#                     ON ci.phone_no = im.mob_no 
#                     where (ci.cid like '%{filterTxt}%' or ci.phone_no like '%{filterTxt}%' 
#                     or ci.name like '%{filterTxt}%') and im.fy = '{FY_Gen(Cur_Date)}' 
#                     GROUP BY ci.cid, ci.phone_no, ci.name, ci.address, ci.wholesale 
#                 """
#         else:
#             sqlFilter = fr"""SELECT ci.cid,ci.phone_no,ci.name,ci.address,ci.wholesale,IF(ci.wholesale = 1 ,'W','R') AS ws,
#                                 COALESCE(SUM(im.amt_payabe), 0) - COALESCE(SUM(im.amt_received), 0) AS outstanding_amount
#                                 FROM customer_info ci
#                                 LEFT JOIN invoice_master im 
#                                 ON ci.phone_no = im.mob_no 
#                                 where (ci.cid like '%{filterTxt}%' or ci.phone_no like '%{filterTxt}%' or ci.name like '%{filterTxt}%') 
#                                 and im.active_status in ('Y','P') and im.fy = '{FY_Gen(Cur_Date)}' 
#                                 GROUP BY ci.cid, ci.phone_no, ci.name, ci.address, ci.wholesale 
#                             """



#         Push_TableView_SqlData_Wth_AdjColumName('CustomerDetail_Model', ui.IQTV_CustomerDetail, sqlFilter,
#            ['Customer ID', 'Phone Number', 'Customer Name', 'Address', 'Wholesale','Detail','Total Outstanding'])

#     @Exception_Handle
#     def On_Click_Customer_Details():


#         selected_rows = ui.IQTV_CustomerDetail.selectionModel().selectedRows()
#         index = selected_rows[-1]
#         customerUID = ui.IQTV_CustomerDetail.model().index(index.row(), 0).data()
#         phoneNumber = ui.IQTV_CustomerDetail.model().index(index.row(), 1).data()

#         if ui.IQCB_DateRange.isChecked():

#             sqlInvoice = fr"""select gdate,fy,CASE WHEN active_status = 'Y' THEN inv_no WHEN active_status = 'P' THEN 
#                 CONCAT('PE-', inv_no) END AS inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received               
#                 from invoice_master where mob_no = '{phoneNumber}' and active_status in ('Y','P') and 
#                 fy = '{FY_Gen(Cur_Date)}' and 
#                 gdate between '{ui.IQDE_From.date().toString("yyyy-MM-dd")}' and '{ui.IQDE_To.date().toString("yyyy-MM-dd")}'
#                 """

#             Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
#             ['Gen_Date','Financial Year','Invoice Number', 'Mobile Number','SaleMan Name','Payment Mode',
#                                                                     'Discount', 'Total Amount', 'Amount Received'])

#             currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master where mob_no = '{phoneNumber}'
#                                  and gdate between '{ui.IQDE_From.date().toString("yyyy-MM-dd")}' and 
#                                  fy = '{FY_Gen(Cur_Date)}' and 
#                                  '{ui.IQDE_To.date().toString("yyyy-MM-dd")}' and active_status in ('Y','P') group by mob_no"""

#             beforeValue = fr"""select sum(amt_payabe) - sum(amt_received) from invoice_master
#                 where mob_no = '{phoneNumber}' and fy = '{FY_Gen(Cur_Date)}' and 
#                 gdate < '{ui.IQDE_From.date().toString("yyyy-MM-dd")}' 
#                                         and active_status in ('Y','P') group by mob_no"""

#             dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")
#             dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")

#             totalInvAmt = 0 if len(dateBtwnValue)==0 or dateBtwnValue[0] == None else dateBtwnValue[0]
#             totalPayedAmt = 0 if len(dateBtwnValue)==0 or dateBtwnValue[1] == None else dateBtwnValue[1]
#             totalOpeningAmt = 0 if (len(dateBeforeValue) == 0  or dateBeforeValue[0] == None) else dateBeforeValue[0]
#             totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#             ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#             ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#             ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#             ui.IQLE_InvAmount.setText(str(totalInvAmt))

#         else:

#             sqlInvoice = fr"""select gdate,fy,CASE WHEN active_status = 'Y' THEN inv_no WHEN active_status = 'P' THEN 
#                 CONCAT('PE-', inv_no) END AS inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received                
#                 from invoice_master where mob_no = '{phoneNumber}' and fy = '{FY_Gen(Cur_Date)}' and active_status in ('Y','P')
#                             """
#             Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
#             ['Gen_Date','Financial Year','Invoice Number', 'Mobile Number','SaleMan Name',
#                                         'Payment Mode', 'Discount','Total Amount', 'Amount Received'])

#             currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received)
#                from invoice_master where mob_no = '{phoneNumber}' and fy = '{FY_Gen(Cur_Date)}' and active_status in ('Y','P') group by mob_no"""

#             dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

#             totalInvAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] == None else dateBtwnValue[0]
#             totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] == None else dateBtwnValue[1]
#             totalOpeningAmt = 0
#             totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#             ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#             ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#             ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#             ui.IQLE_InvAmount.setText(str(totalInvAmt))

#         Adjust_Table_Width(ui.IQTV_Register, [10,12,13,12,12,12,10,12,14])

#     @Exception_Handle
#     def Enable_GuestDetails():
#         if ui.IQCB_NoCustomerEntry.isChecked():
#             if ui.IQCB_DateRange.isChecked():

#                 sql = fr"""select gdate,fy,inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received
#                     from invoice_master where gdate between '{ui.IQDE_From.date().toString("yyyy-MM-dd")}' 
#                     and fy = '{FY_Gen(Cur_Date)}' and 
#                     '{ui.IQDE_To.date().toString("yyyy-MM-dd")}' and mob_no = 'NA' and active_status in ('Y','P');
#                             """
#                 Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sql,
#                     ['Gen_Date','Financial Year','Invoice Number', 'Mobile Number', 'SaleMan Name', 'Payment Mode',
#                                                          'Discount', 'Total Amount', 'Amount Received'])

#                 currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master 
#                 where mob_no = 'NA' and fy = '{FY_Gen(Cur_Date)}' 
#                 and gdate between '{ui.IQDE_From.date().toString("yyyy-MM-dd")}' and
#                         '{ui.IQDE_To.date().toString("yyyy-MM-dd")}' and active_status in ('Y','P') group by mob_no"""

#                 beforeValue = fr"""select sum(amt_payabe) - sum(amt_received)
#                                 from invoice_master where mob_no = 'NA' and fy = '{FY_Gen(Cur_Date)}' and 
#                                 gdate < '{ui.IQDE_From.date().toString("yyyy-MM-dd")}'
#                                 and active_status in ('Y','P') group by mob_no"""
#                 dateBtwnValue = DB_Fetch(currentWithDateSql,False,"LOE")
#                 dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")


#                 totalInvAmt = 0 if len(dateBtwnValue)== 0 or dateBtwnValue[0] == None else dateBtwnValue[0]
#                 totalPayedAmt = 0 if len(dateBtwnValue)== 0 or dateBtwnValue[1] == None else dateBtwnValue[1]
#                 totalOpeningAmt = 0 if (len(dateBeforeValue) == 0 and dateBeforeValue[0] == None) else (
#                     dateBeforeValue)[0]
#                 totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#                 ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#                 ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#                 ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#                 ui.IQLE_InvAmount.setText(str(totalInvAmt))

#             else:

#                 noDataQuery = fr"""select inv_no,mob_no,fy,gdate,sales_man,pay_mode from invoice_master limit 0"""
#                 Push_TableView_SqlData_Wth_AdjColumName('CustomerDetail_Model', ui.IQTV_CustomerDetail, noDataQuery,
#                     ['Customer ID', 'Phone Number', 'Customer Name', 'Address', 'Wholesale','Detail', 'Total Outstanding'])


#                 NoCustomerQuery = fr"""select gdate,fy,inv_no,mob_no,sales_man,pay_mode,discount,
#                                 amt_payabe,amt_received 
#                                 from invoice_master
#                                 where mob_no in ('NA','',NULL)
#                                 """
#                 Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model_NoCustomer', ui.IQTV_Register, NoCustomerQuery,
#                    ['Gen_Date','Financial Year','Invoice Number', 'Mobile Number','SaleMan Name',
#                                                         'Payment Mode', 'Discount', 'Total Amount', 'Amount Received'])

#                 currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master 
#                                     where mob_no = 'NA' and active_status in ('Y','P') group by mob_no"""

#                 dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

#                 totalInvAmt = 0 if dateBtwnValue[0] == None else dateBtwnValue[0]
#                 totalPayedAmt = 0 if dateBtwnValue[1] == None else dateBtwnValue[1]
#                 totalOpeningAmt = 0
#                 totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#                 ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#                 ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#                 ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#                 ui.IQLE_InvAmount.setText(str(totalInvAmt))


#         else:

#             Customer_Detail_data()
#             NoCustomerQuery = fr"""select gdate,fy,inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received 
#                                         from invoice_master limit 0"""
#             Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model_NoCustomer', ui.IQTV_Register, NoCustomerQuery,
#                ['Gen_Date','Financial Year','Invoice Number', 'Mobile Number','SaleMan Name',
#                                                      'Payment Mode', 'Discount', 'Total Amount', 'Amount Received'])

#             currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master where active_status 
#             in ('Y','P')"""

#             dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")


#             totalInvAmt = 0 if dateBtwnValue[0] == None else dateBtwnValue[0]
#             totalPayedAmt = 0 if dateBtwnValue[1] == None else dateBtwnValue[1]
#             totalOpeningAmt = 0
#             totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#             ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#             ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#             ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#             ui.IQLE_InvAmount.setText(str(totalInvAmt))

#     @Exception_Handle
#     def Enable_Date_Filter():
#         if ui.IQCB_DateRange.isChecked():
#             # print("Selected date:", ui.IQDE_From.date().toString("yyyy-MM-dd"))
#             ui.IQDE_From.setEnabled(True)
#             ui.IQDE_To.setEnabled(True)

#         else:
#             ui.IQDE_From.setEnabled(False)
#             ui.IQDE_To.setEnabled(False)
#             ui.IQDE_From.setDate(QDate(Cur_Date.year, Cur_Date.month, 1))
#             ui.IQDE_To.setDate(QDate.currentDate())

#         Enable_GuestDetails()

#     @Exception_Handle
#     def Changing_fromNto_Date():
#         fromDate = ui.IQDE_From.date().toString("yyyy-MM-dd")
#         toDate = ui.IQDE_To.date().toString("yyyy-MM-dd")

#         if ui.IQCB_NoCustomerEntry.isChecked():
#             sql = fr"""select gdate,fy,inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,
#             amt_received from invoice_master 
#             where gdate between '{fromDate}' and '{toDate}' and fy = '{FY_Gen(Cur_Date)}' and 
#             mob_no = 'NA' and active_status in ('Y','P');
#             """
#             Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sql,
#               ['Gen_Date','Financial Year','Invoice Number', 'Mobile Number','SaleMan Name','Payment Mode',
#                                                      'Discount', 'Total Amount', 'Amount Received'])


#             currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master where mob_no = 
#             'NA' and gdate between '{fromDate}' and '{toDate}' and active_status in ('Y','P') 
#             and fy = '{FY_Gen(Cur_Date)}' 
#             group by mob_no"""
            
#             beforeValue = fr"""select sum(amt_payabe) - sum(amt_received) from invoice_master where mob_no = 'NA' 
#             and gdate < '{fromDate}' and fy = '{FY_Gen(Cur_Date)}' and active_status in ('Y','P') group by mob_no"""
#             dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")
#             dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")

#             totalInvAmt = 0 if dateBtwnValue[0] == None else dateBtwnValue[0]
#             totalPayedAmt = 0 if dateBtwnValue[1] == None else dateBtwnValue[1]
#             totalOpeningAmt = 0 if (len(dateBeforeValue) > 0 and dateBeforeValue[0] == None) else dateBeforeValue[0]
#             totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#             ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#             ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#             ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#             ui.IQLE_InvAmount.setText(str(totalInvAmt))


#         else:
#             sql = fr"""select gdate,fy,inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received
#                 from invoice_master where gdate between '{fromDate}' and '{toDate}' 
#                 and fy = '{FY_Gen(Cur_Date)}' and active_status in ('Y','P')"""
#             Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sql,
#               ['Gen_Date','Financial Year','Invoice Number', 'Mobile Number','SaleMan Name', 'Payment Mode',
#                                                      'Discount', 'Total Amount', 'Amount Received'])

#             currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master where gdate 
#             between '{fromDate}' and '{toDate}' and fy = '{FY_Gen(Cur_Date)}' and active_status in ('Y','P')"""
#             beforeValue = fr"""select sum(amt_payabe) - sum(amt_received) from invoice_master 
#             where gdate < '{fromDate}' and fy = '{FY_Gen(Cur_Date)}' and active_status in ('Y','P')"""
#             dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")
#             dateBeforeValue = DB_Fetch(beforeValue, False, "LOE")

#             totalInvAmt = 0 if dateBtwnValue[0] == None else dateBtwnValue[0]
#             totalPayedAmt = 0 if dateBtwnValue[1] == None else dateBtwnValue[1]
#             totalOpeningAmt = 0 if dateBeforeValue[0] == None else dateBeforeValue[0]
#             totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#             ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#             ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#             ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#             ui.IQLE_InvAmount.setText(str(totalInvAmt))

#     @Exception_Handle
#     def Add_Payment(customerUID,phoneNumber,customerName,lastInvoice):

#         if get_info_msg("Confirmation Window Adding",fr"Do You want to Add rs.{payUIUI.IQLE_Amount.text()}"
#             +"\n " + fr"For the Customer Number : {phoneNumber} and Customer Name : {customerName}"):

#             paydictData = {
#                 'fy':fr"{int(Cur_Date_YR)}-{int(Cur_Date_YR)+1}" if int(Cur_Date_MM) > 3 else
#                 fr"{int(Cur_Date_YR)-1}-{int(Cur_Date_YR)}",
#                 'inv_no':lastInvoice,
#                 'gdate' :payUIUI.IQDE_GenDate.date().toString("yyyy-MM-dd"),
#                 'mob_no':phoneNumber,
#                 'sales_man':"NA",
#                 'pay_mode' : payUIUI.IQCB_PayMode.currentText(),
#                 'discount':0,
#                 'amt_payabe':0,
#                 'amt_received' : payUIUI.IQLE_Amount.text(),
#                 'active_status':"P"
#             }
#             DB_Push_Dict(paydictData,"invoice_master",False)
#             payUI.close()

#             sqlInvoice = fr"""select gdate,fy,CASE WHEN active_status = 'Y' THEN inv_no WHEN active_status = 'P' THEN 
#                             CONCAT('PE-', inv_no) END AS inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received                
#                             from invoice_master where mob_no = '{phoneNumber}' and active_status in ('Y','P')
#                                         """
#             Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
#                ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number','SaleMan Name',
#                                                      'Payment Mode', 'Discount', 'Total Amount', 'Amount Received'])

#             currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master where mob_no = 
#                                                 '{phoneNumber}' and active_status in ('Y','P') group by mob_no"""

#             dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

#             totalInvAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] == None else dateBtwnValue[0]
#             totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] == None else dateBtwnValue[1]
#             totalOpeningAmt = 0
#             totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#             ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#             ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#             ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#             ui.IQLE_InvAmount.setText(str(totalInvAmt))
#             Customer_Detail_data()

#         else:
#             show_info_msg("Status Message","Amount Is Not Added")

#     @Exception_Handle
#     def Update_Customer(customerUID,regMobno,customerName,regInvoice):

#         if get_info_msg("Confirmation Window Update",
#                         fr"Do You want to Add rs.{payUIUI.IQLE_Amount.text()}" + "\n "
#                             "For " + fr"the Customer Number : {regMobno} and Customer Name : {customerName}"):

#             updateDictData = {
#                 'gdate': payUIUI.IQDE_GenDate.date().toString("yyyy-MM-dd"),
#                 'pay_mode': payUIUI.IQCB_PayMode.currentText(),
#                 'amt_received': payUIUI.IQLE_Amount.text()
#             }
#             updateUID = {
#                 'inv_no': regInvoice,
#                 'active_status': "P"
#             }

#             DB_Update_Dict(updateDictData, updateUID, 'invoice_master', False)

#             payUI.close()
#             sqlInvoice = fr"""select gdate,fy,CASE WHEN active_status = 'Y' THEN inv_no WHEN active_status = 'P' THEN 
#                             CONCAT('PE-', inv_no) END AS inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received                
#                             from invoice_master where mob_no = '{regMobno}' and active_status in ('Y','P')
#                                         """
#             Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
#                  ['Gen_Date', 'Financial Year', 'Invoice Number', 'Mobile Number','SaleMan Name',
#                                                      'Payment Mode', 'Discount', 'Total Amount', 'Amount Received'])

#             currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master where
#                                 mob_no = '{regMobno}' and active_status in ('Y','P') group by mob_no"""

#             dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

#             totalInvAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] == None else dateBtwnValue[0]
#             totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] == None else dateBtwnValue[1]
#             totalOpeningAmt = 0
#             totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#             ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#             ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#             ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#             ui.IQLE_InvAmount.setText(str(totalInvAmt))
#             Customer_Detail_data()
#         else:
#             show_info_msg("Status Message","Amount Is Not Updated")

#     @Exception_Handle
#     def AddUpdateDelete_PaymentEntry():
#         selected_rows = ui.IQTV_CustomerDetail.selectionModel().selectedRows()

#         if len(selected_rows)>0 and ui.IQCB_AddUpdateDelete.currentText() == "Add":
#             index = selected_rows[-1]
#             customerUID = ui.IQTV_CustomerDetail.model().index(index.row(), 0).data()
#             phoneNumber = ui.IQTV_CustomerDetail.model().index(index.row(), 1).data()
#             customerName = ui.IQTV_CustomerDetail.model().index(index.row(), 2).data()

#             sqllastInvoice = DB_Fetch(fr"""select max(inv_no) from invoice_master where active_status in ('P','NP')""",
#                                       False,"LOE")[0]
#             lastInvoice = 1 if sqllastInvoice == None else int(sqllastInvoice) + 1

#             payUI.show()

#             payUIUI.IQDE_GenDate.setDate(QDate.currentDate())
#             payUIUI.IQLE_PhoneNo.setText(str(phoneNumber))
#             payUIUI.IQLE_CustomerName.setText(str(customerName))
#             payUIUI.IQLE_CustomerUID.setText(str(customerUID))
#             payUIUI.IQLE_InvNumber.setText(fr"PE-{str(lastInvoice)}")
#             payUIUI.IQLE_Amount.clear()

#             try:
#                 payUIUI.IQPB_Action.clicked.disconnect()
#             except:
#                 pass

#             # customerUID,phoneNumber,customerName,lastInvoice

#             payUIUI.IQPB_Action.clicked.connect(lambda : Add_Payment(customerUID,phoneNumber,customerName,lastInvoice))

#         elif len(selected_rows) > 0 and ui.IQCB_AddUpdateDelete.currentText() == "Update":
#             index = selected_rows[-1]
#             customerUID = ui.IQTV_CustomerDetail.model().index(index.row(), 0).data()
#             phoneNumber = ui.IQTV_CustomerDetail.model().index(index.row(), 1).data()
#             customerName = ui.IQTV_CustomerDetail.model().index(index.row(), 2).data()

#             selected_rows_regtbl = ui.IQTV_Register.selectionModel().selectedRows()

#             if len(selected_rows_regtbl)>0:
#                 # print("selected")
#                 regindex = selected_rows_regtbl[-1]
#                 regInvoice = (ui.IQTV_Register.model().index(regindex.row(), 2).data()).replace("PE-","")
#                 regMobno = ui.IQTV_Register.model().index(regindex.row(), 3).data()
#                 regSaleMan = ui.IQTV_Register.model().index(regindex.row(), 4).data()
#                 # print(regInvoice,regMobno,regSaleMan,"=================")

#                 if regSaleMan == "NA":
#                     # print("yes its a Payment Entry")

#                     sql = fr""" select gdate,pay_mode,amt_received from invoice_master where active_status = 'P' 
#                     and inv_no = '{regInvoice}'"""

#                     payUI.show()
#                     updateData = DB_Fetch(sql,False,"LOE")
#                     payUIUI.IQDE_GenDate.setDate(QDate(updateData[0]))
#                     payUIUI.IQLE_PhoneNo.setText(str(regMobno))
#                     payUIUI.IQLE_CustomerName.setText(str(customerName))
#                     payUIUI.IQLE_CustomerUID.setText(str(customerUID))
#                     payUIUI.IQLE_InvNumber.setText(fr"PE-{str(regInvoice)}")
#                     payUIUI.IQLE_Amount.setText(str(updateData[2]))
#                     payUIUI.IQCB_PayMode.setCurrentIndex(["Cash","Gpay","NIFT"].index(updateData[1]))


#                     try:
#                         payUIUI.IQPB_Action.clicked.disconnect()
#                     except:
#                         pass

#                     payUIUI.IQPB_Action.clicked.connect(lambda: Update_Customer(customerUID,regMobno,customerName,regInvoice))

#                 else:
#                     show_info_msg("Information", "Please Select the Payment Entry Data to Update")

#             else:
#                 show_info_msg("Information", "Please Select the Customer from Register Table")

#         elif len(selected_rows) > 0 and ui.IQCB_AddUpdateDelete.currentText() == "Delete":

#             dindex = selected_rows[-1]

#             dcustomerUID = ui.IQTV_CustomerDetail.model().index(dindex.row(), 0).data()
#             dphoneNumber = ui.IQTV_CustomerDetail.model().index(dindex.row(), 1).data()
#             dcustomerName = ui.IQTV_CustomerDetail.model().index(dindex.row(), 2).data()

#             delselected_rows_Reg = ui.IQTV_Register.selectionModel().selectedRows()

#             if len(delselected_rows_Reg) > 0:
#                 print("selected")
#                 delindex = delselected_rows_Reg[-1]
#                 delInvoice = ui.IQTV_Register.model().index(delindex.row(), 2).data()
#                 delMobno = ui.IQTV_Register.model().index(delindex.row(), 3).data()
#                 delSaleMan = ui.IQTV_Register.model().index(delindex.row(), 4).data()
#                 delGivenamt = ui.IQTV_Register.model().index(delindex.row(), 8).data()

#                 # print(delInvoice, delMobno, delSaleMan, "=================")

#                 if delSaleMan == "NA":

#                     if get_info_msg("Confirmation Window Delete", "Are You Sure Do you Want To Delete\n\n" +
#                                                                   fr"Invoice Number : {delInvoice}"+ "\n"+ fr"Customer UID : {dcustomerUID}"+ "\n" +
#                                                                   fr"Customer Name : {dcustomerName}"+"\n" +fr"Customer Number : {dphoneNumber}"
#                                                                   +"\n" +fr"Given Amount : {delGivenamt}"):

#                         deleteDictData = {
#                             'active_status': "NP"
#                         }
#                         deletedUID = {
#                             'inv_no': delInvoice.replace("PE-",""),
#                             'active_status': "P"
#                         }

#                         DB_Update_Dict(deleteDictData, deletedUID, 'invoice_master', False)

#                         sqlInvoice = fr"""select gdate,fy,CASE WHEN active_status = 'Y' THEN inv_no WHEN active_status = 'P' THEN 
#                                CONCAT('PE-', inv_no) END AS inv_no,mob_no,sales_man,pay_mode,discount,amt_payabe,amt_received                
#                                from invoice_master where mob_no = '{delMobno}' and active_status in ('Y','P')"""

#                         Push_TableView_SqlData_Wth_AdjColumName('InvoiceMaster_Model', ui.IQTV_Register, sqlInvoice,
#                                                                 ['Gen_Date', 'Financial Year', 'Invoice Number','Mobile Number', 'SaleMan Name',
#                                                                  'Payment Mode', 'Discount', 'Total Amount','Amount Received'])

#                         currentWithDateSql = fr"""select sum(amt_payabe),sum(amt_received) from invoice_master where 
#                                     mob_no = '{delMobno}' and active_status in ('Y','P') group by mob_no"""

#                         dateBtwnValue = DB_Fetch(currentWithDateSql, False, "LOE")

#                         totalInvAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[0] == None else dateBtwnValue[0]
#                         totalPayedAmt = 0 if len(dateBtwnValue) == 0 or dateBtwnValue[1] == None else dateBtwnValue[1]
#                         totalOpeningAmt = 0
#                         totalClosingAmt = float(totalInvAmt) + float(totalOpeningAmt) - float(totalPayedAmt)

#                         ui.IQLE_PaidAmount.setText(str(totalPayedAmt))
#                         ui.IQLE_OpeningBalance.setText(str(totalOpeningAmt))
#                         ui.IQLE_ClosingBalance.setText(str(totalClosingAmt))
#                         ui.IQLE_InvAmount.setText(str(totalInvAmt))

#                         Customer_Detail_data()

#                     else:
#                         show_info_msg("Status Message", "Amount Is Not Deleted")


#                 else:
#                     show_info_msg("Information", "Please Select the Payment Entry Data to Delete")

#             else:
#                 show_info_msg("Information", "Please Select the Customer from Register Table For Deleting")

#         else:
#             show_info_msg("Select the Customer","Please Select the Customer Details")


#     ### General Functions

#     Customer_Detail_data()

#     ui.IQDE_From.setDate(QDate(Cur_Date.year, Cur_Date.month, 1))
#     ui.IQDE_To.setDate(QDate.currentDate())

#     Adjust_Table_Width(ui.IQTV_CustomerDetail, [11,13,15,15,5,12])
#     Adjust_Table_Width(ui.IQTV_Register, [10,12,13,12,12,12,10,12,14])


#     ### Function & Connections Def

#     ui.IQLE_FilterCustomerTable.textChanged.connect(lambda : Filter_Customer_ViewTbl())

#     ui.IQTV_CustomerDetail.clicked.connect(lambda: On_Click_Customer_Details())

#     ui.IQCB_DateRange.stateChanged.connect(lambda : Enable_Date_Filter())

#     ui.IQCB_NoCustomerEntry.stateChanged.connect(lambda: Enable_GuestDetails())

#     ui.IQDE_From.dateChanged.connect(lambda : Changing_fromNto_Date())

#     ui.IQDE_To.dateChanged.connect(lambda: Changing_fromNto_Date())

#     ui.IQPB_PaymentEntry.clicked.connect(lambda : AddUpdateDelete_PaymentEntry())



# if __name__ == "__main__":
#     Invoice_Register_FN(Inv_Reg)
#     Inv_Reg.showMaximized()
#     sys.exit(app.exec_())