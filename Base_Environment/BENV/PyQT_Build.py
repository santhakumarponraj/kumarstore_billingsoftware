from .Base_Build import *

#Same
@Exception_Handle
def show_info_msg(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QMessageBox.Ok)  # Corrected method
    msg.resize(400, 200)
    msg.exec_()

def get_info_msg(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.resize(400, 200)
    result = msg.exec_()  # Waits for user
    return result == QMessageBox.Ok


@Exception_Handle
def Show_Msg_Infomation(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QMessageBox.Ok)  # Corrected method
    msg.resize(400, 200)
    msg.exec()

@Exception_Handle
def Return_Confirmatiom(temp, stmnt):
    global UI_Confirm
    UI_Confirm=stmnt
    temp.close()

@Exception_Handle
def Quick_Dialog(QN):
    name, ok = QInputDialog.getText(Twink_UI, "User Input", QN)
    if ok and name:
        return name

@Exception_Handle
def UI_Confirmation(temp,inp):
    temp.NEX_Message.setText(inp)
    temp.IQDB_Confirmation.accepted.connect(lambda : Return_Confirmatiom(temp,True))
    temp.IQDB_Confirmation.rejected.connect(lambda : Return_Confirmatiom(temp,False))
    temp.exec_()
    Window_Holder(temp)
    try:
        return UI_Confirm
    except:
        pass

@Exception_Handle
def Fetch_Table_Values(inp):
    if "QTableView" in str(type(inp)):
        model = inp.model()
        data = []

        for r in range(model.rowCount()):
            row = []
            for c in range(model.columnCount()):
                row.append(model.data(model.index(r, c)))
            data.append(row)

        return data

    else:
        values = []

        for row in range(inp.rowCount()):
            row_data = []

            for col in range(inp.columnCount()):
                widget = inp.cellWidget(row, col)

                if widget:
                    if isinstance(widget, QCheckBox):
                        row_data.append(widget.isChecked())

                    elif isinstance(widget, QSpinBox):
                        row_data.append(widget.value())

                    elif isinstance(widget, QDateEdit):
                        row_data.append(widget.date().toString("dd-MM-yyyy"))

                    elif isinstance(widget, QComboBox):
                        row_data.append(widget.currentText())

                    elif isinstance(widget, QLineEdit):
                        row_data.append(widget.text())   # 👈 FIX

                    else:
                        row_data.append("")

                else:
                    item = inp.item(row, col)
                    row_data.append(item.text() if item else "")

            values.append(row_data)
        return values

@Exception_Handle
def Fetch_ListBox_Values(output):
    list_values = []
    for index in range(output.count()):
        item = output.item(index)
        list_values.append(item.text())
    return list_values

@Exception_Handle
def Dynamic_Filter_ComboBox(combo_box):
    combo_box.setFocusPolicy(Qt.StrongFocus)
    combo_box.setEditable(True)
    pFilterModel = QSortFilterProxyModel(combo_box)
    pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
    pFilterModel.setSourceModel(combo_box.model())
    completer = QCompleter(pFilterModel, combo_box)
    completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
    combo_box.setCompleter(completer)
    completer.popup().setFont(QFont("Courier New", 10))


    def on_completer_activated(text):
        if text:
            index = combo_box.findText(text)
            combo_box.setCurrentIndex(index)
            combo_box.activated[str].emit(combo_box.itemText(index))
    combo_box.lineEdit().textEdited.connect(pFilterModel.setFilterFixedString)
    completer.activated.connect(on_completer_activated)
    combo_box.setInsertPolicy(QComboBox.NoInsert)

@Exception_Handle
def Push_Table_Values_sort(element, data, edit):
    element.setSortingEnabled(False)
    element.clearContents()
    element.setRowCount(0)
    try:
        element.setRowCount(len(data))
        if len(data[0])>0:
            element.setColumnCount(len(data[0]))
    except:return
    for i in range(len(data)):
        for j in range(len(data[i])):
            if str(type(data[i][j]))[:23] == "<class 'PyQt5.QtWidgets":
                element.setCellWidget (i, j,data[i][j])
            else:
                temp = T_itm(str(data[i][j]))

                if isinstance(edit,list):
                    if j not in edit:
                        temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                if edit == False:
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                element.setItem(i,j,temp)
    element.setSortingEnabled(True)


@Exception_Handle
def Push_Table_Values(element, data, edit):
    element.clearContents()
    element.setRowCount(0)
    try:
        element.setRowCount(len(data))
        if len(data[0])>0:
            element.setColumnCount(len(data[0]))
    except:return
    for i in range(len(data)):
        for j in range(len(data[i])):
            if str(type(data[i][j]))[:23] == "<class 'PyQt5.QtWidgets":
                element.setCellWidget (i, j,data[i][j])
            else:
                temp = T_itm(str(data[i][j]))

                if isinstance(edit,list):
                    if j not in edit:
                        temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                if edit == False:
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                element.setItem(i,j,temp)


@Exception_Handle
def colour_value(item, color):
    if item:  # Ensure the item exists before setting color
        item.setBackground(color)

@Exception_Handle
def Push_Table_Values_Color(element, data, edit):
    # print(element.objectName(),"element")
    element.setSortingEnabled(False)
    element.clearContents()
    element.setRowCount(0)
    try:
        element.setRowCount(len(data))
        if len(data[0])>0:
            element.setColumnCount(len(data[0]))
    except:return
    for i in range(len(data)):
        print(data[i])
        for j in range(len(data[i])):

            if str(type(data[i][j]))[:23] == "<class 'PyQt5.QtWidgets":
                element.setCellWidget(i, j,data[i][j])
            else:
                temp = T_itm(str(data[i][j]))

                if isinstance(edit,list):
                    if j not in edit:
                        temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                if edit == False:
                    temp.setFlags(temp.flags() & ~Qt.ItemIsEditable)
                element.setItem(i,j,temp)
                item = element.item(i, j)

                if data[i][3].startswith("GCN") and element.objectName() == 'OQTW_InvoiceInfo':
                    colour_value(item,QColor(255, 200, 200))
                elif data[i][3].startswith("Cancelled") and element.objectName() == 'OQTW_InvoiceInfo':
                    colour_value(item,QColor(255, 255, 0))
                elif element.objectName() == "IQTB_NetInvoice" and data[i][5] == "YTP":
                    colour_value(item,QColor(210, 180, 140))
                elif element.objectName() == "IQTB_NetInvoice" and data[i][5] == "PPD":
                    colour_value(item,QColor(255, 255, 0))
                elif element.objectName() == "IQTB_NetInvoice" and data[i][5] == "CPD":
                    colour_value(item,QColor(0, 255, 0))

    element.setSortingEnabled(True)

@Exception_Handle
def Adjust_Table_Width(element,col_width):
    fixed_font = QFont("Courier New", 10)
    for i, width in enumerate(col_width):
        element.setColumnWidth(i, fixed_font.pointSize() * width)

@Exception_Handle
def Filter_Table_Data(element,src_txt,data,col):
    if element.horizontalHeader().sortIndicatorSection() < len(data[0]):
        col=element.horizontalHeader().sortIndicatorSection()
    temp=[]
    for step in data:
        if str(src_txt).lower()in str(step[col]).lower():
            temp.append(step)
    element.setSortingEnabled(False)
    Push_Table_Values(element,temp,False)

@Exception_Handle
def Format_Table_Column(TBL,col,color):
    # Change the color of the entire column
    for step in col:
        for row in range(TBL.rowCount()-1):
            item = TBL.item(row, step)
            item.setBackground(color)

@Exception_Handle
def Format_Table_Row(TBL,row,color):
    # Change the color of the entire column
    for step in row:
        for col in range(TBL.columnCount()-1):
            item = TBL.item(step, col)
            item.setBackground(color)

@Exception_Handle
def Fetch_Table_Values_SPL_Col(inp,Col):#___Fetch_Table_Values___
    values = []
    for row in range(inp.rowCount()):
        item = inp.item(row, Col)
        if item is not None:
            values.append(item.text())
        else:
            values.append("")
    return values

@Exception_Handle
def Export_to_excel(Table,file_name):
    headings_list = []
    for col in range(Table.columnCount()):
        item = Table.horizontalHeaderItem(col)
        headings_list.append(item.text())
    export_data = Fetch_Table_Values(Table)
    df = pd.DataFrame(export_data, columns=headings_list)
    df.to_csv(fr'{ldir}\Export\{file_name}.csv')
    subprocess.run(['start', 'excel', fr'{ldir}\Export\{file_name}.csv'], shell=True, check=True)

@Exception_Handle
def Export_to_excel_Mail(Table,file_name):
    headings_list = []
    for col in range(Table.columnCount()):
        item = Table.horizontalHeaderItem(col)
        headings_list.append(item.text())
    export_data = Fetch_Table_Values(Table)
    df = pd.DataFrame(export_data, columns=headings_list)
    df.to_csv(fr'{ldir}\Export\{file_name}.csv')

@Exception_Handle
def Update_Property(inp,mode,name,stat):
    data = inp.findChildren(QWidget)
    # print(data)
    for step in data:
        if mode == "Readonly":
            if name in step.objectName():
                step.setReadOnly(stat)
        elif mode == "Enable":
            if name in step.objectName():
                step.setEnabled(stat)
        elif mode=="Visible":
            if name in step.objectName():
                step.setVisible(stat)
        elif mode=="Clear":
            if name in step.objectName():
                step.clear()
                step.setText("")
        elif mode == "Null":
            if name in step.objectName():

                try:
                    if step.isReadOnly() and stat:
                        step.setReadOnly(False)
                        step.setText("")
                        step.setReadOnly(True)
                    else:
                        step.setText("")
                except:
                    step.setText("")


class NoDoubleClickDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, role=Qt.DisplayRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, role=Qt.EditRole)

# print("XX3")