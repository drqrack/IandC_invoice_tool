import sys
from pathlib import Path
from app import load_and_prepare_rows, build_bills, render_pdf_for_bill
import datetime as dt

def verify():
    excel_path = Path('1ST CONTAINER LIST.xlsx')
    if not excel_path.exists():
        print("Excel file not found. Run create_test_excel_new_format.py first")
        return

    print("Loading Excel...")
    df = load_and_prepare_rows(excel_path)
    print("Columns found:", df.columns.tolist())
    print(df.head())
    
    bills = build_bills(df, rate_usd_per_cbm=240, other_cost_usd=0)
    print(f"Generated {len(bills)} bills (Expect 2: Tilly, Christian)")
    
    template_html = Path('template_invoice.html').read_text(encoding='utf-8')
    invoice_date = dt.datetime.now().strftime("%dTH %b, %Y").upper()
    
    for bill in bills:
        print(f"BILL: {bill.customer_name} (Phone: {bill.phone})")
        print(f"  Items: {len(bill.breakdown_items)}")
        print(f"  Total CBM: {bill.total_cbm}")
        print(f"  Desc: {bill.item_description}")
        
        out_path = Path(f"TEST_NEW_{bill.customer_name.strip()}.pdf")
        render_pdf_for_bill(bill, template_html, out_path, "INV-TEST", invoice_date)
        print(f"  -> Generated {out_path}")

if __name__ == "__main__":
    verify()
