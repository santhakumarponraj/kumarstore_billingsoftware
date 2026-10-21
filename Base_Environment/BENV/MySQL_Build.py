import os

from .Base_Build import *

from PyQt5.QtCore import Qt, QIdentityProxyModel
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtSql import QSqlQueryModel



# ___DB Functions___
@Exception_Handle
def DB_Connect(cred):
    # print(cred['db_host'],cred["database"])
    MySQL_database = mysql.connector.connect(host=cred['db_host'], user=cred['db_user'], passwd=cred['db_pass'],
                                             database=cred["database"],port = cred['db_port'],
                                             )
    
    db_con = MySQL_database.cursor()
    print("=========SQL Connected===========")
    return db_con,MySQL_database

# ___Database Dictioanry___
dbv = 'Primary'
dbc,db = DB_Connect(ConfigData[dbv])


dbod = QSqlDatabase.addDatabase("QODBC")
# SQLODC_Name = "Driver={MySQL ODBC 9.4 ANSI Driver};"
dbod.setDatabaseName("Driver={MySQL ODBC 9.4 UNICODE Driver};" + fr"Server={ConfigData[dbv]['db_host']};Database={ConfigData[dbv]['database']};User={ConfigData[dbv]['db_user']};Password={ConfigData[dbv]['db_pass']};")
if dbod.open():
    print("======ODBC Connected!=====")
else:
    print("Error:", dbod.lastError().text())

models = {}

@Exception_Handle
def Push_TableView_SqlData(tbl_name,tbl,sql):
    model = QSqlQueryModel()
    model.setQuery(sql, dbod)
    if model.lastError().isValid():
        print("SQL Error:", model.lastError().text())
    tbl.setModel(model)
    models[tbl_name] = model

@Exception_Handle
def Push_TableView_SqlData_Wth_AdjColumName(tbl_name,tbl,sql,lst):
    model = QSqlQueryModel()
    model.setQuery(sql, dbod)
    if model.lastError().isValid():
        print("SQL Error:", model.lastError().text())
    tbl.setModel(model)
    models[tbl_name] = model

    for index, data in enumerate(lst):
        model.setHeaderData(index, Qt.Horizontal, data)


@Exception_Handle
def Push_TableView_SqlData_Wth_AdjColumName_color(tbl_name, tbl, sql, lst):

    class _ActiveStatusColorProxy(QIdentityProxyModel):
        def data(self, index, role):
            if role == Qt.BackgroundRole:
                status_index = self.sourceModel().index(index.row(), 5)
                status = self.sourceModel().data(status_index)

                if status == 'C':
                    return QColor("#FFD6D6")   # Cancelled → red
                elif status == 'Y':
                    return QColor("#E6FFE6")   # Active → green

            if role == Qt.FontRole:
                status_index = self.sourceModel().index(index.row(), 5)
                if self.sourceModel().data(status_index) == 'C':
                    font = QFont()
                    font.setBold(True)
                    return font

            return super().data(index, role)

    base_model = QSqlQueryModel()
    base_model.setQuery(sql, dbod)

    if base_model.lastError().isValid():
        print("SQL Error:", base_model.lastError().text())

    proxy_model = _ActiveStatusColorProxy()
    proxy_model.setSourceModel(base_model)

    tbl.setModel(proxy_model)
    models[tbl_name] = proxy_model

    for index, header in enumerate(lst):
        base_model.setHeaderData(index, Qt.Horizontal, header)



@Exception_Handle
def Adjust_ViewTbl_ColName(tbl,lst):
    model = tbl.model()
    for index,data in enumerate(lst):
        model.setHeaderData(index, Qt.Horizontal, data)

@Exception_Handle
def DB_Exe(sql,prnt):
    if prnt == True:
        print(sql)
    dbc.execute(sql)

@Exception_Handle
def DB_Cmt(sql,prnt):
    if prnt == True:
        print(sql)
    dbc.execute(sql)
    db.commit()
    return True

@Exception_Handle
def DB_Cmt_WOE(sql,prnt):
    if prnt == True:
        print(sql)
    try:
        dbc.execute(sql)
        db.commit()
    except:
        pass

@Exception_Handle
def DB_Fetch(sql,prnt,type):
    global dbc, db

    if prnt == True:
        print(sql)
    dbc.execute(sql)
    if type == "LOE":
        return list(sum(dbc.fetchall(),()))
    if type == "LOL":
        return [list(x) for x in dbc.fetchall()]
    if type == "DIC":
        try:
            return {key: value for key, value in [list(x) for x in dbc.fetchall()]}
        except: return None
    if type == "DOC":
        data = list(sum(dbc.fetchall(),()))
        column= dbc.column_names
        try:
            return {key:value for key,value in zip(column,data)}
        except:
            return None
    if type == "DOL":
        return {x[0] : list(x[1:]) for x in dbc.fetchall()}
    if type == "DOD":
        columns = [desc[0] for desc in dbc.description]
        dictData = dict()
        for data in dbc.fetchall():
            dictData[data[0]] = dict()
            for col1, data1 in zip(columns[1:], data[1:]):
                dictData[data[0]][col1] = data1

        return dictData

@Exception_Handle
def DB_TBL_Fetch(tbl,indexlist,active):
    if active == True:
        dbc.execute(f'select * from {tbl} where active ="Y"')
    if active == False:
        dbc.execute(f'select * from {tbl} where active ="N"')
    if active == None:
        dbc.execute(f'select * from {tbl}')

    data=[list(x) for x in dbc.fetchall()]
    if indexlist == True:
        return data
    if isinstance(indexlist, int):
        return [inner_list[:indexlist] for inner_list in data]
    if isinstance(indexlist, list):
        return [[inner_list[index] for index in indexlist] for inner_list in data]

@Exception_Handle
def DB_Push_Dict(dict,tbl_nm,prnt):

    # if len(dict) != 1:
    columns = ', '.join(dict.keys())
    placeholders = ', '.join(['%s'] * len(dict))
    values = tuple(dict.values())
    sql = f"INSERT INTO {tbl_nm} ({columns}) VALUES ({placeholders})"
    if prnt == True:
        print(sql,values)
    dbc.execute(sql, values)
    db.commit()
    # else:
    #     print(dict,tbl_nm,prnt)



    # placeholders = ', '.join([f'"{element}"' for element in dict.values()])
    # columns = ', '.join(dict.keys())
    # sql = f"INSERT INTO {tbl_nm} ( {columns} ) VALUES ( {placeholders} )"
    # if DB_Cmt(sql,prnt):
    #     return True

@Exception_Handle
def DB_Push_Dict_WOE(dict,tbl_nm,prnt):
    placeholders = ', '.join([f'"{element}"' for element in dict.values()])
    columns = ', '.join(dict.keys())
    sql = f"INSERT INTO {tbl_nm} ( {columns} ) VALUES ( {placeholders} )"
    if DB_Cmt_WOE(sql,prnt):
        return True

@Exception_Handle
def DB_Delete_Dict(dict,tbl_nm,prnt):
    # DB_Cmt('SET SQL_SAFE_UPDATES = 0;',False)
    c_dict = ' AND '.join([f"{key} = '{value}'" for key, value in dict.items()])
    sql = f"DELETE FROM {tbl_nm} WHERE {c_dict};"
    if DB_Cmt(sql,prnt):
        return True
    
    # DB_Cmt('SET SQL_SAFE_UPDATES = 1;',False)

@Exception_Handle
def DB_Update_Dict(dict,c_dict,tbl_nm,prnt):
    dict =', '.join([f"{key} = '{value}'" for key, value in dict.items()])
    c_dict = ' AND '.join([f"{key} = '{value}'" for key, value in c_dict.items()])
    sql = f" UPDATE {tbl_nm} SET {dict} WHERE {c_dict} LIMIT 1"
    if DB_Cmt(sql, prnt):
        return True

@Exception_Handle
def DB_Update_Dict_WOL(dict,c_dict,tbl_nm,prnt):
    dict =', '.join([f"{key} = '{value}'" for key, value in dict.items()])
    c_dict = ' AND '.join([f"{key} = '{value}'" for key, value in c_dict.items()])
    sql = f" UPDATE {tbl_nm} SET {dict} WHERE {c_dict} "
    DB_Cmt(sql, prnt)

@Exception_Handle
def DB_Push_Update_Dict(dict, tbl_nm, prnt):
    columns = ', '.join(dict.keys())
    values = ', '.join([f"'{element}'" for element in dict.values()])
    update_part = ', '.join([f"{key} = '{value}'" for key, value in dict.items()])
    sql = f"INSERT INTO {tbl_nm} ({columns}) VALUES ({values}) ON DUPLICATE KEY UPDATE {update_part}"

    DB_Cmt(sql, prnt)

@Exception_Handle
def Button_DB_Connect(cred):
    global dbc, db
    dbase = DB_Connect(cred)
    # print('dbase',dbase)
    dbc = dbase[0]
    db = dbase[1]
    UI_Confirmation(UI_Confirm_Win, fr"MYSQL Connection done Successfully")

@Exception_Handle
def Push_Table_Row(element, data, edit, row):
  # print(row)
    element.insertRow(row)
    element.setSortingEnabled(False)
    for j in range(len(data)):
        if str(type(data[j]))[:23] == "<class 'PyQt5.QtWidgets":
            element.setCellWidget(row, j, data[j])
        else:
            temp = T_itm(str(data[j]))
            if isinstance(edit, list):
                if j not in edit:
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
            if edit == False:
                temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
            element.setItem(row, j, temp)

@Exception_Handle
def Format_Table_Values(inp):
    for i in range(len(inp)):
        temp = T_itm(str(inp[i]))
        temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
        inp[i] = temp
    return inp

@Exception_Handle
def Fetch_Table_Rows(temp, row, column):
    row_data = []
    for col in range(temp.columnCount()):
        item = temp.item(row, col)
        if item is not None:
            row_data.append(item.text())
        else:
            row_data.append('')
    return row_data

@Exception_Handle
def Set_TableColumn_colors(temp, columns, color):
    column_count = temp.columnCount()  # Get the total number of columns
    for col in columns:
        if col >= column_count:  # Ignore invalid column indexes
            print(f"Column {col} is out of range (Total columns: {column_count})")
            continue
        for row in range(temp.rowCount()):
            item = temp.item(row, col)
            if item is None:  # If the cell is empty, create a new item
                item = QTableWidgetItem("")  # Empty string to avoid NoneType errors
                temp.setItem(row, col, item)
            item.setBackground(QColor(color))  # Apply background color

@Exception_Handle
def create_numeric_delegate(table, columns):
    delegate = QStyledItemDelegate(table)

    def create_editor(parent, option, index):
        editor = QLineEdit(parent)
        validator = QDoubleValidator(editor)
        validator.setBottom(0)  # Set minimum value to 0
        editor.setValidator(validator)
        return editor

    delegate.createEditor = create_editor
    for column in columns:
        table.setItemDelegateForColumn(column, delegate)

# @Exception_Handle
# def Adjust_Table_Width(element, col_width):
#     print("I'm here")
#     fixed_font = QFont("Courier New", 10)
#     for i, width in enumerate(col_width):
#         element.setColumnWidth(i, fixed_font.pointSize() * width)


@Exception_Handle
def Freeze_Column(tbl, lst, edit):
    for row in range(tbl.rowCount()):
        for col in lst:
            if edit == True:
                item = tbl.item(row, col)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                item = tbl.item(row, col)
                item.setFlags(item.flags() | Qt.ItemIsEditable)


@Exception_Handle
def Table_ClipBoard(table):
    table.setContextMenuPolicy(Qt.ActionsContextMenu)

    def create_action(name, shortcut, slot):
        action = QAction(name, table)
        action.setShortcut(shortcut)
        action.triggered.connect(lambda: slot(table))
        return action

    def copy_to_clipboard(table):
        selected = table.selectedRanges()
        if not selected:
            return

        text = ""
        for r in selected:
            for row in range(r.topRow(), r.bottomRow() + 1):
                row_data = []
                for col in range(r.leftColumn(), r.rightColumn() + 1):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                text += "\t".join(row_data) + "\n"

        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text.strip())
        else:
            print("Error: Clipboard not available")

    def paste_from_clipboard(table):
        clipboard = QApplication.clipboard()
        if clipboard is None:
            print("Error: Clipboard not available")
            return

        text = clipboard.text()
        if not text:
            return

        selected = table.selectedRanges()
        if not selected:
            return
        start_row = selected[0].topRow()
        start_col = selected[0].leftColumn()

        rows = text.split("\n")
        for i, row in enumerate(rows):
            cols = row.split("\t")
            for j, value in enumerate(cols):
                row_idx = start_row + i
                col_idx = start_col + j
                if row_idx < table.rowCount() and col_idx < table.columnCount():
                    item = table.item(row_idx, col_idx)
                    # Create a new item if none exists, but only set text if editable
                    if item is None:
                        item = QTableWidgetItem()
                        table.setItem(row_idx, col_idx, item)
                    # Only paste if the cell is editable
                    if item.flags() & Qt.ItemIsEditable:
                        item.setText(value)

    def delete_selected(table):
        selected = table.selectedRanges()
        if not selected:
            return

        for r in selected:
            for row in range(r.topRow(), r.bottomRow() + 1):
                for col in range(r.leftColumn(), r.rightColumn() + 1):
                    item = table.item(row, col)
                    if item and item.flags() & Qt.ItemIsEditable:
                        item.setText("")  # Clear the text of editable cells

    def delete_row_selected(table):
        selected = table.selectedRanges()
        if not selected:
            return
        for r in selected:
            for row in range(r.topRow(), r.bottomRow() + 1):
                for col in range(r.leftColumn(), r.rightColumn() + 1):
                    item = table.item(row, col)
                    datas = Fetch_Table_Rows(table, row, 1)
                    if str(datas[1]) != '1':
                        table.removeRow(row)
                    # else:
                    #     print('elase')
                    # UI_Confirmation(UI_Confirm_Win, f"Cannot delete this row")

    # Add actions to the table
    table.addAction(create_action("Copy", QKeySequence.Copy, copy_to_clipboard))
    table.addAction(create_action("Paste", QKeySequence.Paste, paste_from_clipboard))
    table.addAction(create_action("Delete", QKeySequence.Delete, delete_selected))
    table.addAction(create_action("Delete Row", QKeySequence.Delete, delete_row_selected))


def DB_Push_Dict_Return(dict,tbl_nm,prnt):
    columns = ', '.join(dict.keys())
    placeholders = ', '.join(['%s'] * len(dict))
    values = tuple(dict.values())
    sql = f"INSERT INTO {tbl_nm} ({columns}) VALUES ({placeholders})"
    if prnt == True:
        print(sql,values)
    return sql,values

def DB_Update_Dict_Return(dict,c_dict,tbl_nm,prnt):
    dict =', '.join([f"{key} = '{value}'" for key, value in dict.items()])
    c_dict = ' AND '.join([f"{key} = '{value}'" for key, value in c_dict.items()])
    sql = f" UPDATE {tbl_nm} SET {dict} WHERE {c_dict} LIMIT 1"
    if prnt:
        print(sql)
    return sql