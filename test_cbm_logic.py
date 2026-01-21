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
    
    expected_subtotal = 3.00 # Fixed charge for 0.01 CBM
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

    print("PASS: Small CBM bill calculated correctly (fixed $3.00 charge).")

    # Test case: Rounding
    # Rate 240, CBM 0.17833... -> Subtotal 42.8 -> Total 43.0
    # Let's just force values to make it clear.
    # We can't easily force subtotal_usd without changing CBM/Rate, so let's pick values.
    # 240 * 0.17833333 = ~42.8
    rounding_bill = Bill(
        shipping_mark="ROUND",
        customer_id="456",
        customer_name="Round Test",
        phone="0000",
        location="Accra",
        total_cbm=0.17833333,
        rate_usd_per_cbm=240.0,
        other_cost_usd=0.0,
        item_description="Rounding Test"
    )
    # Expected subtotal approx 42.8
    print(f"Rounding Bill Subtotal: {rounding_bill.subtotal_usd}")
    print(f"Rounding Bill Total USD: {rounding_bill.total_usd}")
    
    if rounding_bill.total_usd != 43.0:
        print(f"FAIL: Expected 43.0 but got {rounding_bill.total_usd}")
        return
        
    print("PASS: Rounding 42.8 -> 43.0 successful.")

if __name__ == "__main__":
    test_cbm_logic()
