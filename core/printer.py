import platform

def send_to_printer(receipt_text: str, document_name: str = "Receipt"):
    current_os = platform.system()
    if current_os == "Windows":
        try:
            import win32print
            printer_name = win32print.GetDefaultPrinter()
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                win32print.StartDocPrinter(hPrinter, 1, (document_name, None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, receipt_text.encode('utf-8'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"პრინტერის შეცდომა (Windows): {e}")
    else:
        print(f"\n[MOCK PRINT - {document_name}]")
        print(receipt_text)