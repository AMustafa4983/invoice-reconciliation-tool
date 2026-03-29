import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# Product catalog
products = [
    ('ITM-101', 'Wireless Mouse Logitech', 45.00),
    ('ITM-102', 'USB-C Cable 2m', 12.50),
    ('ITM-103', 'HDMI Cable 3m', 28.00),
    ('ITM-104', 'Wireless Keyboard', 89.00),
    ('ITM-105', 'Monitor Stand Adjustable', 145.00),
    ('ITM-106', 'Laptop Cooling Pad', 67.00),
    ('ITM-107', 'External Hard Drive 1TB', 189.00),
    ('ITM-108', 'USB Hub 4-Port', 34.00),
    ('ITM-109', 'Webcam HD 1080p', 156.00),
    ('ITM-110', 'Headset with Mic', 78.00),
    ('ITM-111', 'Power Bank 20000mAh', 95.00),
    ('ITM-112', 'Screen Protector Pack', 22.00),
    ('ITM-113', 'Phone Case Universal', 18.00),
    ('ITM-114', 'Cable Organizer Set', 15.00),
    ('ITM-115', 'Desk Lamp LED', 112.00),
]

suppliers = ['TechSupply LLC', 'ElectroWare Trading', 'Office Depot UAE', 'Digital Solutions FZE']

print("Generating sample data...")

# Generate 60 Purchase Orders
po_data = []
for i in range(1, 61):
    num_items = np.random.randint(1, 6)
    selected_products = np.random.choice(len(products), num_items, replace=False)
    
    for item_idx in selected_products:
        item_code, item_name, unit_price = products[item_idx]
        
        po_data.append({
            'po_number': f'PO-{i:04d}',
            'item_code': item_code,
            'item_name': item_name,
            'quantity_ordered': np.random.choice([50, 100, 150, 200, 250, 500]),
            'unit_price': unit_price,
            'supplier_name': np.random.choice(suppliers),
            'po_date': (datetime.now() - timedelta(days=np.random.randint(1, 45))).strftime('%Y-%m-%d'),
            'total_value': 0
        })

po_df = pd.DataFrame(po_data)
po_df['total_value'] = po_df['quantity_ordered'] * po_df['unit_price']

print(f"✓ Generated {len(po_df)} PO line items across {po_df['po_number'].nunique()} purchase orders")

# Generate Invoices (75% of POs, with intentional issues)
invoice_data = []
invoice_counter = 5500

po_lines_to_invoice = po_df.sample(frac=0.75)

for idx, po_line in po_lines_to_invoice.iterrows():
    has_issue = np.random.random() < 0.30
    
    quantity = po_line['quantity_ordered']
    price = po_line['unit_price']
    
    if has_issue:
        issue_type = np.random.choice(['price', 'quantity', 'both'], p=[0.5, 0.4, 0.1])
        
        if issue_type in ['price', 'both']:
            variance = np.random.uniform(0.05, 0.15)
            direction = np.random.choice([-1, 1])
            price = round(price * (1 + direction * variance), 2)
        
        if issue_type in ['quantity', 'both']:
            variance = np.random.uniform(0.10, 0.25)
            direction = np.random.choice([-1, 1])
            quantity = int(quantity * (1 + direction * variance))
    
    invoice_data.append({
        'invoice_number': f'INV-{invoice_counter}',
        'po_number': po_line['po_number'],
        'item_code': po_line['item_code'],
        'item_name': po_line['item_name'],
        'quantity_invoiced': quantity,
        'unit_price_invoiced': price,
        'invoice_date': (datetime.now() - timedelta(days=np.random.randint(0, 20))).strftime('%Y-%m-%d'),
        'supplier_name': po_line['supplier_name'],
        'total_value_invoiced': quantity * price
    })
    invoice_counter += 1

# Add 5 rogue invoices (no matching PO)
for i in range(5):
    item_code, item_name, unit_price = products[np.random.randint(0, len(products))]
    qty = np.random.choice([25, 50, 75, 100])
    
    invoice_data.append({
        'invoice_number': f'INV-{invoice_counter}',
        'po_number': f'PO-9999',
        'item_code': item_code,
        'item_name': item_name,
        'quantity_invoiced': qty,
        'unit_price_invoiced': unit_price,
        'invoice_date': datetime.now().strftime('%Y-%m-%d'),
        'supplier_name': 'Unknown Supplier LLC',
        'total_value_invoiced': qty * unit_price
    })
    invoice_counter += 1

invoice_df = pd.DataFrame(invoice_data)

print(f"✓ Generated {len(invoice_df)} invoice line items")
print(f"✓ Rogue invoices (no PO): 5")
print(f"✓ Uninvoiced PO lines: {len(po_df) - len(po_lines_to_invoice)}")

# Save to CSV
po_df.to_csv('data/sample_po_data.csv', index=False)
invoice_df.to_csv('data/sample_invoice_data.csv', index=False)

print("\n✅ Sample data generated successfully!")
print(f"📁 Files created:")
print(f"   - data/sample_po_data.csv ({len(po_df)} rows)")
print(f"   - data/sample_invoice_data.csv ({len(invoice_df)} rows)")