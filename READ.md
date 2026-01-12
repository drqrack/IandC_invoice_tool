# Build Instructions

To build the executable on Windows, run the following command in the terminal:

```powershell
pyinstaller --onefile --windowed --add-data "template_invoice.html;." --add-data "logo.png;." --name "IC_Billing_Tool" app.py
```

Result will be in `dist/IC_Billing_Tool.exe`.