import os
import re
import math
import csv
import uuid
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from jinja2 import Template
from weasyprint import HTML


# =========================
# Helpers
# =========================

def money_usd(x: float) -> str:
    return f"${x:,.2f}"



def safe_filename(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r'[\\/:*?"<>|]+', " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:180] if len(s) > 180 else s

def parse_phone_name(value: Any) -> tuple[Optional[str], Optional[str]]:
    """Column C: often '0202425612 BLESSING KUMASI' or '61466818614'."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None, None
    s = str(value).strip()
    if not s:
        return None, None
    if " " in s:
        first, rest = s.split(" ", 1)
        phone = re.sub(r"\D", "", first)
        name = rest.strip() or None
        return (phone or None), name
    phone = re.sub(r"\D", "", s)
    return (phone or None), None

def normalize_shipping_mark(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    s = str(value).strip()
    if not s:
        return None
    # Some cells have multiple numbers separated by spaces; take the first token
    return s.split()[0].strip() or None

def parse_item_description(value: str) -> str:
    """Parse column D value (like '1pallet', '10', '1', etc.) into formatted description."""
    value = value.strip().lower()
    
    # Try to extract number
    import re
    match = re.search(r'(\d+)', value)
    quantity = int(match.group(1)) if match else 1
    
    # Determine the unit
    if 'pallet' in value:
        unit = 'PALLET' if quantity == 1 else 'PALLETS'
    elif 'carton' in value:
        unit = 'CARTON' if quantity == 1 else 'CARTONS'
    elif 'box' in value or 'boxes' in value:
        unit = 'BOX' if quantity == 1 else 'BOXES'
    else:
        # Default to cartons for plain numbers
        unit = 'CARTON' if quantity == 1 else 'CARTONS'
    
    return f"{quantity} {unit}"

def is_container_header_line(colA: Any) -> bool:
    if colA is None or (isinstance(colA, float) and math.isnan(colA)):
        return False
    s = str(colA)
    return ("N005=" in s) or ("N006=" in s)


@dataclass
class Bill:
    shipping_mark: str
    customer_id: Optional[str]
    customer_name: str
    phone: str
    location: str
    total_cbm: float
    rate_usd_per_cbm: float

    other_cost_usd: float
    item_description: str
    breakdown_items: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def subtotal_usd(self) -> float:
        return self.rate_usd_per_cbm * self.total_cbm

    @property
    def min_charge_usd(self) -> float:
        # As per NOTE in PDF: below 0.05 CBM => $10 fixed
        return 10.0 if self.total_cbm < 0.05 else 0.0

    @property
    def total_usd(self) -> float:
        base = self.subtotal_usd
        if self.total_cbm < 0.05:
            base = 10.0
        return base + self.other_cost_usd




# =========================
# Parsing Excel
# =========================

def load_and_prepare_rows(excel_path: Path) -> pd.DataFrame:
    # Read first sheet, no header assumption
    raw = pd.read_excel(excel_path, sheet_name=0, header=None)

    # Remove container header lines
    mask_header = raw[0].apply(is_container_header_line)
    raw = raw[~mask_header].copy()

    # Keep rows where column B (index 1) exists (tracking/shipping mark)
    raw = raw[raw[1].notna()].copy()

    # Map columns A-F by your confirmed structure:
    # A=0, B=1, C=2, D=3, E=4 (CBM), F=5 (item)
    work = raw[[0, 1, 2, 3, 4, 5]].copy()
    work.columns = ["A_customer_id", "B_shipping_mark", "C_name_phone", "D_misc", "E_cbm", "F_item"]

    # Fill-down for continuation lines
    work["A_customer_id"] = work["A_customer_id"].astype(object).ffill()
    work["C_name_phone"] = work["C_name_phone"].astype(object).ffill()

    # Parse phone/name
    parsed = work["C_name_phone"].apply(parse_phone_name)
    work["Phone"] = parsed.apply(lambda x: x[0])
    work["CustomerName"] = parsed.apply(lambda x: x[1])

    # Normalize shipping mark
    work["ShippingMark"] = work["B_shipping_mark"].apply(normalize_shipping_mark)

    # Ensure CBM numeric
    work["E_cbm"] = pd.to_numeric(work["E_cbm"], errors="coerce").fillna(0.0)

    return work


def build_bills(df: pd.DataFrame,
                rate_usd_per_cbm: float,

                other_cost_usd: float,
                location_default: str = "ACCRA GHANA") -> List[Bill]:

    bills: List[Bill] = []

    # # Grouping rule: per shipping mark; fallback to phone if shipping mark missing
    # df = df.copy()
    # df["BillKey"] = df["ShippingMark"]
    # df.loc[df["BillKey"].isna(), "BillKey"] = df["Phone"]

    # grouped = df.groupby("BillKey", dropna=False)

    # Grouping rule: per customer (combine multiple shipping marks)
    df = df.copy()

    # Primary key = phone (best identifier). Fallback to customer name, then customer id.
    df["PhoneKey"] = df["Phone"].fillna("").astype(str).str.strip()
    df["NameKey"] = df["CustomerName"].fillna("").astype(str).str.strip()

    df["BillKey"] = df["PhoneKey"]
    df.loc[df["BillKey"] == "", "BillKey"] = df["NameKey"]
    df.loc[df["BillKey"] == "", "BillKey"] = df["A_customer_id"].astype(str).fillna("UNKNOWN")

    grouped = df.groupby("BillKey", dropna=False)

    for key, g in grouped:
        # shipping_mark = str(g["ShippingMark"].dropna().iloc[0]) if g["ShippingMark"].notna().any() else "NO_SHIPPING_MARK"
        marks = sorted(set([str(x) for x in g["ShippingMark"].dropna().tolist() if str(x).strip()]))
        shipping_mark = ", ".join(marks) if marks else "NO_SHIPPING_MARK"
        customer_id = str(g["A_customer_id"].iloc[0]) if pd.notna(g["A_customer_id"].iloc[0]) else None

        phone = g["Phone"].dropna().astype(str).iloc[0] if g["Phone"].notna().any() else "NO_PHONE"
        name = g["CustomerName"].dropna().astype(str).iloc[0] if g["CustomerName"].notna().any() else "UNKNOWN"

        total_cbm = float(g["E_cbm"].sum())

        # Build breakdown items: one entry per unique shipping mark
        breakdown_items = []
        for mark in marks:
            mark_rows = g[g["ShippingMark"] == mark]
            mark_cbm = float(mark_rows["E_cbm"].sum())
            # Sum quantity by parsing column D
            mark_qty = 0
            for misc_curr in mark_rows["D_misc"].dropna().astype(str):
                parsed = parse_item_description(misc_curr)
                # Try to extract number from parsed string; default to 1 if row exists
                # parse_item_description returns e.g. "10 CARTONS"
                # We can re-use the regex logic briefly here or trust the row count if D is empty?
                # Actually, better to use the same logic as aggregate item_desc:
                match_q = re.search(r'(\d+)', parsed)
                if match_q:
                    mark_qty += int(match_q.group(1))
                else:
                    mark_qty += 1
            
            breakdown_items.append({
                "tracking_number": mark,
                "quantity": mark_qty,
                "cbm": round(mark_cbm, 2)
            })

        # Build item description: use column D (D_misc) which contains quantity/pallet info
        items_d = [x for x in g["D_misc"].dropna().astype(str).tolist() if x.strip()]
        
        if items_d:
            # Sum up all quantities and determine the most common unit type
            total_qty = 0
            has_pallet = False
            
            for item in items_d:
                parsed = parse_item_description(item)
                # Extract quantity from parsed string
                qty_match = re.search(r'(\d+)', parsed)
                if qty_match:
                    total_qty += int(qty_match.group(1))
                if 'PALLET' in parsed:
                    has_pallet = True
            
            # Build final description
            if has_pallet:
                unit = 'PALLET' if total_qty == 1 else 'PALLETS'
            else:
                unit = 'CARTON' if total_qty == 1 else 'CARTONS'
            
            item_desc = f"{total_qty} {unit} OF PERSONAL USE"
        else:
            # Fallback to column F if D is empty
            items_f = [x for x in g["F_item"].dropna().astype(str).tolist() if x.strip()]
            if items_f:
                item_desc = ", ".join(items_f).upper()
            else:
                item_desc = "PERSONAL USE"

        bills.append(Bill(
            shipping_mark=shipping_mark,
            customer_id=customer_id,
            customer_name=name,
            phone=phone,
            location=location_default,
            total_cbm=round(total_cbm, 3),
            rate_usd_per_cbm=rate_usd_per_cbm,

            other_cost_usd=other_cost_usd,
            item_description=item_desc,
            breakdown_items=breakdown_items
        ))

    # Stable sort for nice outputs
    bills.sort(key=lambda b: (b.shipping_mark or "", b.phone or ""))
    return bills


# =========================
# PDF + Exports
# =========================

def render_pdf_for_bill(bill: Bill, template_html: str, out_path: Path,
                        invoice_no: str, invoice_date: str) -> None:

    # payment details line exactly like sample: "240*0.42"
    payment_details = f"{int(bill.rate_usd_per_cbm)}*{bill.total_cbm:.2f}"

    html = Template(template_html).render(
        invoice_no=invoice_no,
        invoice_date=invoice_date,
        customer_name=bill.customer_name,
        location=bill.location,
        phone=bill.phone,
        item_description=bill.item_description,
        rate_usd_str=money_usd(bill.rate_usd_per_cbm),
        cbm_str=f"{bill.total_cbm:.2f}",
        payment_details=payment_details,
        subtotal_usd_str=money_usd(bill.subtotal_usd if bill.total_cbm >= 0.05 else 10.0),
        other_cost_usd_str=money_usd(bill.other_cost_usd),
        total_usd_str=money_usd(bill.total_usd),
        # shipping_mark=bill.shipping_mark,
        shipping_mark=bill.shipping_mark.replace(", ", "\n"),
        breakdown_items=bill.breakdown_items

    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # base_url="." allows WeasyPrint to find "logo.png" in the current directory
    HTML(string=html, base_url=".").write_pdf(str(out_path))


def make_whatsapp_message(bill: Bill) -> str:
    calc_usd = (bill.subtotal_usd if bill.total_cbm >= 0.05 else 10.0)
    payment_line = f"{int(bill.rate_usd_per_cbm)} * {bill.total_cbm:.2f} = {money_usd(calc_usd)}"
    if bill.total_cbm < 0.05:
        payment_line = f"Min charge (CBM<0.05) = {money_usd(10.0)}"

    msg = (
        "I&C CARGO – GOODS BILL\n"
        f"Name: {bill.customer_name}\n"
        f"Phone: {bill.phone}\n"
        f"Shipping Mark: {bill.shipping_mark}\n"
        f"Total CBM: {bill.total_cbm:.2f}\n"
        f"Rate: {money_usd(bill.rate_usd_per_cbm)}/CBM → {payment_line}\n"
        f"Other Cost: {money_usd(bill.other_cost_usd)}\n"
        f"Total: {money_usd(bill.total_usd)}\n"
        "Note: CBM below 0.05 is charged fixed $10."
    )
    return msg


def export_summary_xlsx(bills: List[Bill], out_xlsx: Path) -> None:
    rows = []
    for b in bills:
        rows.append({
            "ShippingMark": b.shipping_mark,
            "CustomerName": b.customer_name,
            "Phone": b.phone,
            "TotalCBM": b.total_cbm,
            "Rate_USD_per_CBM": b.rate_usd_per_cbm,
            "Subtotal_USD": (b.subtotal_usd if b.total_cbm >= 0.05 else 10.0),
            "OtherCost_USD": b.other_cost_usd,
            "Total_USD": b.total_usd,

        })
    df = pd.DataFrame(rows)
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Summary")


def export_whatsapp_csv(bills: List[Bill], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Phone", "ShippingMark", "CustomerName", "Message"])
        for b in bills:
            w.writerow([b.phone, b.shipping_mark, b.customer_name, make_whatsapp_message(b)])


# =========================
# GUI (Tkinter)
# =========================

import tkinter as tk
from tkinter import filedialog, messagebox

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("I&C Billing Tool (Excel → PDFs + WhatsApp)")
        self.geometry("720x420")
        self.resizable(False, False)

        self.excel_path_var = tk.StringVar(value="")
        self.out_dir_var = tk.StringVar(value="")
        self.rate_var = tk.StringVar(value="240")

        self.other_cost_var = tk.StringVar(value="0")

        self._build()

    def _build(self):
        pad = 10

        frm = tk.Frame(self)
        frm.pack(fill="both", expand=True, padx=pad, pady=pad)

        row = 0
        tk.Label(frm, text="Excel file (from China):").grid(row=row, column=0, sticky="w")
        tk.Entry(frm, textvariable=self.excel_path_var, width=70).grid(row=row, column=1, sticky="w")
        tk.Button(frm, text="Select...", command=self.select_excel).grid(row=row, column=2, padx=6)

        row += 1
        tk.Label(frm, text="Output folder:").grid(row=row, column=0, sticky="w", pady=(8,0))
        tk.Entry(frm, textvariable=self.out_dir_var, width=70).grid(row=row, column=1, sticky="w", pady=(8,0))
        tk.Button(frm, text="Choose...", command=self.select_out_dir).grid(row=row, column=2, padx=6, pady=(8,0))

        row += 1
        tk.Label(frm, text="Rate (USD per CBM):").grid(row=row, column=0, sticky="w", pady=(12,0))
        tk.Entry(frm, textvariable=self.rate_var, width=20).grid(row=row, column=1, sticky="w", pady=(12,0))

        row += 1

        tk.Label(frm, text="Other cost (USD) [optional]:").grid(row=row, column=0, sticky="w", pady=(8,0))
        tk.Entry(frm, textvariable=self.other_cost_var, width=20).grid(row=row, column=1, sticky="w", pady=(8,0))

        row += 1
        tk.Button(frm, text="Generate", command=self.generate, width=20, height=2).grid(row=row, column=1, sticky="w", pady=(18,0))

        row += 1
        self.log = tk.Text(frm, height=10, width=90)
        self.log.grid(row=row, column=0, columnspan=3, pady=(14,0))
        self._log("Ready. Select Excel, enter Rate, click Generate.")

    def _log(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.update_idletasks()

    def select_excel(self):
        p = filedialog.askopenfilename(
            title="Select Excel file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if p:
            self.excel_path_var.set(p)
            # default output folder same as excel
            self.out_dir_var.set(str(Path(p).parent))

    def select_out_dir(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p:
            self.out_dir_var.set(p)

    def generate(self):
        excel_path = Path(self.excel_path_var.get().strip())
        out_dir = Path(self.out_dir_var.get().strip())
        if not excel_path.exists():
            messagebox.showerror("Error", "Please select a valid Excel file.")
            return
        if not out_dir.exists():
            messagebox.showerror("Error", "Please choose a valid output folder.")
            return

        try:
            rate = float(self.rate_var.get().strip())

            other_cost = float(self.other_cost_var.get().strip() or "0")
        except Exception:
            messagebox.showerror("Error", "Rate/Other cost must be valid numbers.")
            return



        try:
            template_html = Path("template_invoice.html").read_text(encoding="utf-8")
        except Exception:
            messagebox.showerror("Error", "Missing template_invoice.html (must be in same folder as app.py).")
            return

        self._log(f"Loading Excel: {excel_path.name}")
        df = load_and_prepare_rows(excel_path)
        self._log(f"Rows loaded: {len(df)}")

        bills = build_bills(df, rate_usd_per_cbm=rate, other_cost_usd=other_cost)

        run_stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = out_dir / f"IC_OUTPUT_{run_stamp}"
        pdf_dir = run_dir / "PDFs"

        self._log(f"Generating {len(bills)} bills...")

        invoice_date = dt.datetime.now().strftime("%dTH %b, %Y").upper()

        for i, b in enumerate(bills, start=1):
            # Invoice number: simple unique per bill (can be changed to your exact sequence later)
            invoice_no = "1C" + dt.datetime.now().strftime("%Y") + str(uuid.uuid4().int)[0:8]

            name_part = safe_filename(b.customer_name) or "UNKNOWN"
            phone_part = safe_filename(b.phone) or "NO_PHONE"
            # ship_part = safe_filename(b.shipping_mark) or "NO_SHIPPING_MARK"

            # pdf_name = f"{ship_part} - {name_part} - {phone_part}.pdf"
            pdf_name = f"CUSTOMER - {name_part} - {phone_part}.pdf"
            out_pdf = pdf_dir / pdf_name

            render_pdf_for_bill(b, template_html, out_pdf, invoice_no=invoice_no, invoice_date=invoice_date)

            if i % 20 == 0:
                self._log(f"... {i}/{len(bills)} PDFs done")

        export_whatsapp_csv(bills, run_dir / "WhatsApp_Messages.csv")
        export_summary_xlsx(bills, run_dir / "Summary.xlsx")

        self._log(f"Done. Output folder: {run_dir}")
        messagebox.showinfo("Done", f"Generated {len(bills)} PDFs + WhatsApp CSV + Summary.xlsx\n\n{run_dir}")

if __name__ == "__main__":
    App().mainloop()