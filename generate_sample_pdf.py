#!/usr/bin/env python3
"""Generate a sample PDF to demonstrate the changes"""

import sys
from pathlib import Path
import datetime as dt

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import load_and_prepare_rows, build_bills, render_pdf_for_bill

# Load Excel and build bills
excel_path = Path("N005-N006 CONTAINER LIST.xlsx")
df = load_and_prepare_rows(excel_path)
bills = build_bills(df, rate_usd_per_cbm=235, other_cost_usd=0)

# Get a sample bill (find one with interesting description)
sample_bill = bills[0]  # First bill

# Read template
template_path = Path("template_invoice.html")
template_html = template_path.read_text(encoding='utf-8')

# Generate PDF
output_path = Path("SAMPLE_INVOICE.pdf")
invoice_no = "1C202600001"
invoice_date = dt.datetime.now().strftime("%dTH %b, %Y").upper()

print(f"Generating sample PDF for:")
print(f"  Customer: {sample_bill.customer_name}")
print(f"  Phone: {sample_bill.phone}")
print(f"  Item Description: {sample_bill.item_description}")
print(f"  Total CBM: {sample_bill.total_cbm}")
print(f"  Total: ${sample_bill.total_usd:.2f}")
print()

render_pdf_for_bill(sample_bill, template_html, output_path, 
                    invoice_no=invoice_no, invoice_date=invoice_date)

print(f"✓ Sample PDF generated successfully: {output_path}")
print()
print("You can now open this PDF to verify the new styling and item description format.")
