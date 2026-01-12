#!/usr/bin/env python3
"""Test script to verify the changes to app.py"""

import sys
from pathlib import Path

# Add current directory to path to allow importing app
sys.path.insert(0, str(Path(__file__).parent))

from app import load_and_prepare_rows, build_bills, parse_item_description

# Test parse_item_description function
print('Testing parse_item_description function:')
print('  "1pallet" ->', parse_item_description('1pallet'))
print('  "1" ->', parse_item_description('1'))
print('  "10" ->', parse_item_description('10'))
print('  "40" ->', parse_item_description('40'))
print('  "2" ->', parse_item_description('2'))
print()

# Test with actual Excel file
print('Testing with Excel file:')
excel_path = Path("N005-N006 CONTAINER LIST.xlsx")
df = load_and_prepare_rows(excel_path)
print(f'Loaded {len(df)} rows from Excel')
print()

# Build bills with test rate (matching the PDF example: $235/CBM)
bills = build_bills(df, rate_usd_per_cbm=235, other_cost_usd=0)
print(f'Generated {len(bills)} bills')
print()

# Show first 5 bills to verify item descriptions
print('Sample bills (first 5):')
for i, bill in enumerate(bills[:5], 1):
    print(f'{i}. Customer: {bill.customer_name}')
    print(f'   Phone: {bill.phone}')
    print(f'   Item Description: {bill.item_description}')
    print(f'   Total CBM: {bill.total_cbm}')
    print(f'   Total: ${bill.total_usd:.2f}')
    print()

print('✓ Test completed successfully!')
