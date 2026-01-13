
import os
import sys
from pathlib import Path
import datetime as dt

# Add current directory to path to import app
sys.path.append(str(Path.cwd()))

from app import load_and_prepare_rows, build_bills, render_pdf_for_bill

def verify():
    excel_path = Path("N005-N006 CONTAINER LIST.xlsx")
    if not excel_path.exists():
        print(f"Error: {excel_path} not found")
        return

    print("Loading Excel...")
    df = load_and_prepare_rows(excel_path)
    print(f"Loaded {len(df)} rows")

    print("Building bills...")
    bills = build_bills(df, rate_usd_per_cbm=240.0, other_cost_usd=0.0)
    print(f"Built {len(bills)} bills")

    # Find a bill with multiple breakdown items
    multi_item_bills = [b for b in bills if len(b.breakdown_items) > 1]
    print(f"Found {len(multi_item_bills)} bills with multiple tracking numbers")

    if not multi_item_bills:
        print("No bills with multiple tracking numbers found to test breakdown table!")
        # fall back to printing first bill to check basic function
        to_print = bills[:1]
    else:
        to_print = multi_item_bills[:3] # Print first 3 multi-item bills

    out_dir = Path("test_output")
    out_dir.mkdir(exist_ok=True)
    
    template_html = Path("template_invoice.html").read_text(encoding="utf-8")
    invoice_date = dt.datetime.now().strftime("%dTH %b, %Y").upper()

    for i, bill in enumerate(to_print):
        print(f"Generating PDF for {bill.customer_name} (Items: {len(bill.breakdown_items)})")
        invoice_no = f"TEST-{i}"
        safe_name = "".join([c for c in bill.customer_name if c.isalnum() or c in " -_"])
        out_pdf = out_dir / f"TEST_INVOICE_{safe_name}.pdf"
        
        render_pdf_for_bill(bill, template_html, out_pdf, invoice_no, invoice_date)
        print(f"Generated: {out_pdf}")
        
    print("Verification complete.")

if __name__ == "__main__":
    verify()
