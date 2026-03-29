import pandas as pd
import numpy as np

def reconcile_data(po_df, invoice_df):
    """
    Reconcile invoices against purchase orders
    Returns merged dataframe with status flags
    """
    
    # Merge on PO number and item code
    merged = pd.merge(
        invoice_df,
        po_df,
        on=['po_number', 'item_code'],
        how='outer',
        suffixes=('_invoice', '_po'),
        indicator=True
    )
    
    # Determine reconciliation status
    def get_status(row):
        # Invoice with no PO
        if pd.isna(row['invoice_number']):
            return 'Uninvoiced PO'
        
        # PO not found
        if pd.isna(row['quantity_ordered']):
            return 'PO Not Found'
        
        # Check for mismatches
        qty_match = row['quantity_invoiced'] == row['quantity_ordered']
        price_match = abs(row['unit_price_invoiced'] - row['unit_price']) < 0.01
        
        if qty_match and price_match:
            return 'Perfect Match'
        elif not qty_match and not price_match:
            return 'Both Mismatch'
        elif not price_match:
            return 'Price Mismatch'
        else:
            return 'Quantity Mismatch'
    
    merged['status'] = merged.apply(get_status, axis=1)
    
    # Calculate discrepancies
    merged['qty_difference'] = merged['quantity_invoiced'] - merged['quantity_ordered']
    merged['price_difference'] = merged['unit_price_invoiced'] - merged['unit_price']
    
    # Calculate value impact
    merged['value_impact'] = (
        (merged['quantity_invoiced'] * merged['unit_price_invoiced']) - 
        (merged['quantity_ordered'] * merged['unit_price'])
    )
    
    # Fill NaN for uninvoiced POs
    merged['value_impact'] = merged['value_impact'].fillna(0)
    
    return merged


def get_summary_stats(reconciled_df):
    """Generate summary statistics"""
    
    total_pos = reconciled_df[
        reconciled_df['status'] != 'PO Not Found'
    ]['po_number'].nunique()
    
    total_invoices = reconciled_df[
        reconciled_df['status'] != 'Uninvoiced PO'
    ]['invoice_number'].nunique()
    
    status_counts = reconciled_df['status'].value_counts().to_dict()
    
    perfect_matches = status_counts.get('Perfect Match', 0)
    perfect_match_pct = (perfect_matches / total_invoices * 100) if total_invoices > 0 else 0
    
    discrepancies = sum([
        status_counts.get('Price Mismatch', 0),
        status_counts.get('Quantity Mismatch', 0),
        status_counts.get('Both Mismatch', 0)
    ])
    
    total_value_impact = reconciled_df[
        reconciled_df['status'].isin(['Price Mismatch', 'Quantity Mismatch', 'Both Mismatch'])
    ]['value_impact'].sum()
    
    return {
        'total_pos': total_pos,
        'total_invoices': total_invoices,
        'perfect_matches': perfect_matches,
        'perfect_match_pct': perfect_match_pct,
        'discrepancies': discrepancies,
        'po_not_found': status_counts.get('PO Not Found', 0),
        'uninvoiced_pos': status_counts.get('Uninvoiced PO', 0),
        'total_value_impact': total_value_impact
    }


def get_exceptions_only(reconciled_df):
    """Filter to show only problematic records"""
    
    exception_statuses = [
        'Price Mismatch',
        'Quantity Mismatch',
        'Both Mismatch',
        'PO Not Found'
    ]
    
    exceptions = reconciled_df[
        reconciled_df['status'].isin(exception_statuses)
    ].copy()
    
    # Sort by absolute value impact (biggest issues first)
    exceptions['abs_impact'] = exceptions['value_impact'].abs()
    exceptions = exceptions.sort_values('abs_impact', ascending=False)
    exceptions = exceptions.drop('abs_impact', axis=1)
    
    return exceptions