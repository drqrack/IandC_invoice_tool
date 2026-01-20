import sys
from pathlib import Path
from app import Bill

def test_cbm_logic():
    # Test case: CBM < 0.05
    small_bill = Bill(
        shipping_mark="TEST",
        customer_id="123",
        customer_name="Test Customer",
        phone="1234567890",
        location="Accra",
        total_cbm=0.01,
        rate_usd_per_cbm=240.0,
        other_cost_usd=0.0,
        item_description="Test Item"
    )

    print(f"Testing Bill with CBM={small_bill.total_cbm}, Rate={small_bill.rate_usd_per_cbm}")
    
    expected_subtotal = 0.01 * 240.0 # 2.4
    print(f"Expected Subtotal: {expected_subtotal}")
    print(f"Actual Subtotal: {small_bill.subtotal_usd}")

    if abs(small_bill.subtotal_usd - expected_subtotal) > 0.001:
        print("FAIL: Subtotal mismatch")
        return

    expected_total = expected_subtotal
    print(f"Expected Total: {expected_total}")
    print(f"Actual Total: {small_bill.total_usd}")

    if abs(small_bill.total_usd - expected_total) > 0.001:
        print("FAIL: Total mismatch. Likely still applying min charge.")
        return

    # Check min_charge_usd property just in case
    print(f"Min Charge Property: {small_bill.min_charge_usd}")
    if small_bill.min_charge_usd != 0.0:
        print("FAIL: min_charge_usd should be 0.0")
        return

    print("PASS: Small CBM bill calculated correctly (no fixed $10 charge).")

if __name__ == "__main__":
    test_cbm_logic()
