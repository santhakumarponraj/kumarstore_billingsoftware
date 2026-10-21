"""
Lists every printer name exactly as the Windows Print Spooler knows it.
Run this, find your Posiflex printer in the output, and copy that
EXACT string into PRINTER_NAME in print_via_winspool.py.

No pywin32 needed — uses ctypes -> winspool.drv directly.
"""

import ctypes
from ctypes import wintypes

winspool = ctypes.WinDLL("winspool.drv")

PRINTER_ENUM_LOCAL = 0x00000002
PRINTER_ENUM_CONNECTIONS = 0x00000004


def list_printers():
    flags = PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
    needed = wintypes.DWORD(0)
    returned = wintypes.DWORD(0)

    # First call: find out how much buffer we need
    winspool.EnumPrintersW(flags, None, 2, None, 0,
                            ctypes.byref(needed), ctypes.byref(returned))

    buf = ctypes.create_string_buffer(needed.value)
    ok = winspool.EnumPrintersW(flags, None, 2, buf, needed.value,
                                 ctypes.byref(needed), ctypes.byref(returned))
    if not ok:
        raise OSError("EnumPrintersW failed.")

    class PRINTER_INFO_2W(ctypes.Structure):
        _fields_ = [
            ("pServerName", wintypes.LPWSTR),
            ("pPrinterName", wintypes.LPWSTR),
            ("pShareName", wintypes.LPWSTR),
            ("pPortName", wintypes.LPWSTR),
            ("pDriverName", wintypes.LPWSTR),
            ("pComment", wintypes.LPWSTR),
            ("pLocation", wintypes.LPWSTR),
            ("pDevMode", ctypes.c_void_p),
            ("pSepFile", wintypes.LPWSTR),
            ("pPrintProcessor", wintypes.LPWSTR),
            ("pDatatype", wintypes.LPWSTR),
            ("pParameters", wintypes.LPWSTR),
            ("pSecurityDescriptor", ctypes.c_void_p),
            ("Attributes", wintypes.DWORD),
            ("Priority", wintypes.DWORD),
            ("DefaultPriority", wintypes.DWORD),
            ("StartTime", wintypes.DWORD),
            ("UntilTime", wintypes.DWORD),
            ("Status", wintypes.DWORD),
            ("cJobs", wintypes.DWORD),
            ("AveragePPM", wintypes.DWORD),
        ]

    array_type = PRINTER_INFO_2W * returned.value
    printers = ctypes.cast(buf, ctypes.POINTER(array_type)).contents

    print(f"Found {returned.value} printer(s):\n")
    for pr in printers:
        print(f"  Name: {pr.pPrinterName}")
        print(f"  Port: {pr.pPortName}")
        print(f"  Driver: {pr.pDriverName}")
        print("-" * 40)


if __name__ == "__main__":
    list_printers()
