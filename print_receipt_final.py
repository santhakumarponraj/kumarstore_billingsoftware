"""
Direct ESC/POS print using python-escpos's Win32Raw class.

NOTE: Win32Raw requires the pywin32 package (it uses win32print
internally). If you need to avoid pywin32, use the ctypes/winspool
version instead (print_receipt_final.py) — that one has no pywin32
dependency at all.

Install once:
    pip install python-escpos pywin32
Run:
    python print_bill_win32raw.py
"""

from escpos.printer import Win32Raw

# =================================================================
# DATA
# =================================================================
items = [
    ['அஸ்கா', '3.0', '46.0', '138.0'],
    ['மகாராஜா உளுந்து', '1.0', '134.0', '134.0'],
    ['வடை பரூப்பு நயம்', '1.0', '70.0', '70.0'],
    ['500g.அரிசி மாவு 32ரூ', '1.0', '27.0', '27.0'],
]
# Schema: [Item Name, Qty, Rate, Amount]

STORE_NAME = "MY SHOP"
STORE_ADDRESS = "Coimbatore"
STORE_PHONE = "9876543210"
BILL_NO = "1001"
BILL_DATE = "30-08-2026"

LINE_WIDTH = 42
COL_QTY, COL_RATE, COL_AMT = 6, 8, 10
COL_NAME = LINE_WIDTH - (COL_QTY + COL_RATE + COL_AMT)

# =================================================================
# PRINT
# =================================================================

def print_bill():
    printer_name = "Posiflex PP6900 Printer"  # exact spooler name confirmed earlier
    p = Win32Raw(printer_name)

    # Header
    p.set(align="center", bold=True, width=2, height=2)
    p.text(f"{STORE_NAME}\n")

    p.set(align="center", bold=False, width=1, height=1)
    p.text(f"{STORE_ADDRESS}\n")
    p.text(f"Phone: {STORE_PHONE}\n")
    p.text("-" * LINE_WIDTH + "\n")

    # Bill info
    p.set(align="left")
    p.text(f"Bill No : {BILL_NO}\n")
    p.text(f"Date    : {BILL_DATE}\n")
    p.text("-" * LINE_WIDTH + "\n")

    # Items header
    p.set(bold=True)
    p.text(f"{'Item'.ljust(COL_NAME)}{'Qty'.rjust(COL_QTY)}"
           f"{'Rate'.rjust(COL_RATE)}{'Amount'.rjust(COL_AMT)}\n")
    p.set(bold=False)
    p.text("-" * LINE_WIDTH + "\n")

    # Products
    subtotal = 0.0
    for name, qty, rate, amt in items:
        p.text(f"{name[:COL_NAME].ljust(COL_NAME)}{qty.rjust(COL_QTY)}"
               f"{rate.rjust(COL_RATE)}{amt.rjust(COL_AMT)}\n")
        subtotal += float(amt)

    p.text("-" * LINE_WIDTH + "\n")

    # Total
    p.set(align="right", bold=True)
    p.text(f"TOTAL : Rs. {subtotal:.2f}\n")

    p.set(align="center", bold=False)
    p.text("-" * LINE_WIDTH + "\n")
    p.text("Thank You!\n")
    p.text("Visit Again\n\n")

    # Feed and cut
    p.control("LF")
    p.cut()


if __name__ == "__main__":
    print_bill()
    print("Receipt sent to printer.")