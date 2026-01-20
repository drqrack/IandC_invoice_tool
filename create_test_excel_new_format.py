import pandas as pd
from pathlib import Path

def create_test_excel():
    # Header row at index 3 (0-indexed)
    # Row 0: Empty
    # Row 1: Container info 1
    # Row 2: Container info 2
    # Row 3: Data Headers
    
    # Columns: INVOICE N0., TRACKING N0., CONTACT, CUSTOMER NAME, LOCATION, QTY PER TRACKING, CBM PER TRACKING, PRODUCT DESCRIPTION
    
    data = {
        'INVOICE N0.': [101, 102, 103],
        'TRACKING N0.': ['KK12345678', 'S987654321', 'S999888777'],
        'CONTACT': ["201698812", "540789320", "540789320"], # Tilly (1), Christian (2)
        'CUSTOMER NAME': ['Tilly', 'Christian', 'Christian'], 
        'LOCATION': ['ACCRA GHANA', 'ACCRA', 'ACCRA'],
        'QTY PER TRACKING': ['1pallet', '1', '4'],
        'CBM PER TRACKING': [0.18, 0.42, 0.14],
        'PRODUCT DESCRIPTION': ['LEARNING MACHINE', 'SHOES', 'SHOES'],
        'RECEIVING DATE': ['2025-01-01', '2025-01-01', '2025-01-01']
    }
    
    df = pd.DataFrame(data)
    
    # write with startrow=3 so we can put headers in rows 0-2
    path = Path('1ST CONTAINER LIST.xlsx')
    
    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        worksheet = writer.book.add_worksheet('Sheet1')
        # Row 0 empty
        worksheet.write(1, 0, "2th/Jan GHANA 2025--001=TGBU9600716") # Row 1
        worksheet.write(2, 0, "2th/Jan GHANA 2025--001=TGBU9600716") # Row 2
        
        # Write df starting at row 3
        df.to_excel(writer, sheet_name='Sheet1', startrow=3, index=False)
        
    print(f"Created {path}")

if __name__ == "__main__":
    create_test_excel()
