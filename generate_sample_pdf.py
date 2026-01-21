#!/usr/bin/env python3
"""Generate a sample PDF to demonstrate the changes"""

import sys
from pathlib import Path
import datetime as dt

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import load_and_prepare_rows, build_bills, render_pdf_for_bill

# Load Excel and build bills
# Mock a bill with 0.01 CBM
from app import Bill
sample_bill = Bill(
    shipping_mark="TEST-001",
    customer_id="999",
    customer_name="Test Customer 0.01 CBM",
    phone="0000000000",
    location="Test Location",
    total_cbm=0.01,
    rate_usd_per_cbm=240.0,
    other_cost_usd=0.0,
    item_description="1 PACKET OF TEST"
)

# Read template
template_path = Path("template_invoice.html")
template_html = template_path.read_text(encoding='utf-8')

# Generate PDF
output_path = Path("SAMPLE_INVOICE_0.01CBM.pdf")
invoice_no = "TEST-0.01"
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
