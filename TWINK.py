from Env import *


# print(os.getcwd())

# Attach UI to window
Twink.Base_Tab = TwinkUI.Base_Tab
Twink.setWindowTitle('Twink Software Solutions')
while Twink.Base_Tab.count() > 0:
    Twink.Base_Tab.removeTab(0)

Twink.Base_Tab.addTab(Inv_Mtr,"Invoice")
from MODULES.INVOICE_MASTER import Invoice_Master
Invoice_Master.Invoice_Master_FN()

Twink.Base_Tab.addTab(Itm_Mtr,"Product")
from MODULES.ITEM_MASTER import Item_Master
Item_Master.Item_Master_FN()

Twink.Base_Tab.addTab(Prc_Mtr,"Purchase")
from MODULES.PURCHASE_MASTER import Purchase_Master
Purchase_Master.Purchase_Master_FN()

Twink.Base_Tab.addTab(Inv_Reg,"Register")
from MODULES.REGISTER import INVOICE_REGISTER
INVOICE_REGISTER.Invoice_Register_FN()



if __name__ == "__main__":
    Twink.showMaximized()
    print("Good")
    sys.exit(app.exec_())