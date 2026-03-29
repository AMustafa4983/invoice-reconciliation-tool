import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.reconciler import reconcile_data, get_summary_stats, get_exceptions_only
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Invoice Reconciliation System",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f9fafb;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

st.warning("⚠️ **Demo Environment** - This version uses sample data only. Production deployments run on secure client infrastructure with proper access controls and data encryption.")

# Header
st.markdown('<div class="main-header">📊 Invoice Reconciliation System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated reconciliation tool - Match invoices against purchase orders in minutes</div>', unsafe_allow_html=True)

# File uploaders
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Purchase Orders")
    po_file = st.file_uploader("Upload PO Data (CSV)", type=['csv'], key='po')
    
with col2:
    st.subheader("📄 Supplier Invoices")
    invoice_file = st.file_uploader("Upload Invoice Data (CSV)", type=['csv'], key='invoice')

# Load data
if not po_file or not invoice_file:
    st.info("💡 **Demo Mode:** No files uploaded. Using sample data to demonstrate the tool.")
    po_df = pd.read_csv('data/sample_po_data.csv')
    invoice_df = pd.read_csv('data/sample_invoice_data.csv')
else:
    po_df = pd.read_csv(po_file)
    invoice_df = pd.read_csv(invoice_file)

# Data preview
with st.expander("👀 Preview Uploaded Data"):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Purchase Orders:**")
        st.dataframe(po_df.head(), use_container_width=True)
    with col2:
        st.write("**Invoices:**")
        st.dataframe(invoice_df.head(), use_container_width=True)

st.divider()

# Reconciliation button
if st.button("🔍 Run Reconciliation", type="primary", use_container_width=True):
    with st.spinner("Processing reconciliation..."):
        reconciled = reconcile_data(po_df, invoice_df)
        stats = get_summary_stats(reconciled)
        exceptions = get_exceptions_only(reconciled)
        
        st.session_state['reconciled'] = reconciled
        st.session_state['stats'] = stats
        st.session_state['exceptions'] = exceptions
        st.success("✅ Reconciliation complete!")

# Display results
if 'reconciled' in st.session_state:
    stats = st.session_state['stats']
    reconciled = st.session_state['reconciled']
    exceptions = st.session_state['exceptions']
    
    # Summary metrics
    st.subheader("📈 Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total POs Processed",
            f"{stats['total_pos']:,}",
            help="Number of unique purchase orders"
        )
    
    with col2:
        st.metric(
            "Perfect Matches",
            f"{stats['perfect_matches']:,}",
            delta=f"{stats['perfect_match_pct']:.1f}%",
            help="Invoices that match POs exactly"
        )
    
    with col3:
        st.metric(
            "Discrepancies Found",
            f"{stats['discrepancies']:,}",
            delta=f"AED {stats['total_value_impact']:,.2f}",
            delta_color="inverse",
            help="Price/quantity mismatches requiring review"
        )
    
    with col4:
        st.metric(
            "Uninvoiced POs",
            f"{stats['uninvoiced_pos']:,}",
            help="Purchase orders with no matching invoice"
        )
    
    st.divider()
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "⚠️ Exceptions Only", "📋 Full Data"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            status_counts = reconciled['status'].value_counts()
            fig_pie = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Reconciliation Status Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Top discrepancies
            if len(exceptions) > 0:
                top_exceptions = exceptions.head(10)[['po_number', 'item_name_invoice', 'value_impact', 'status']]
                fig_bar = px.bar(
                    top_exceptions,
                    x='value_impact',
                    y='po_number',
                    color='status',
                    title="Top 10 Discrepancies by Value Impact",
                    labels={'value_impact': 'Value Impact (AED)', 'po_number': 'PO Number'},
                    orientation='h'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No exceptions found - all invoices match perfectly!")
    
    with tab2:
        st.subheader("⚠️ Exception Report")
        st.write(f"**{len(exceptions)}** records requiring attention (sorted by $ impact)")
        
        if len(exceptions) > 0:
            # Display columns
            display_cols = [
                'status', 'po_number', 'invoice_number', 'item_name_invoice',
                'supplier_name_invoice', 'quantity_ordered', 'quantity_invoiced',
                'unit_price', 'unit_price_invoiced', 'value_impact'
            ]
            
            exceptions_display = exceptions[display_cols].copy()
            
            # Format currency columns
            exceptions_display['unit_price'] = exceptions_display['unit_price'].apply(lambda x: f"AED {x:,.2f}" if pd.notna(x) else "")
            exceptions_display['unit_price_invoiced'] = exceptions_display['unit_price_invoiced'].apply(lambda x: f"AED {x:,.2f}" if pd.notna(x) else "")
            exceptions_display['value_impact'] = exceptions_display['value_impact'].apply(lambda x: f"AED {x:,.2f}")
            
            # Rename columns for display
            exceptions_display.columns = [
                'Status', 'PO Number', 'Invoice Number', 'Item Name',
                'Supplier', 'Qty Ordered', 'Qty Invoiced',
                'Price (PO)', 'Price (Invoice)', 'Value Impact'
            ]
            
            st.dataframe(
                exceptions_display,
                use_container_width=True,
                height=400
            )
            
            # Export button
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                exceptions.to_excel(writer, sheet_name='Exceptions', index=False)
            
            st.download_button(
                label="📥 Download Exception Report (Excel)",
                data=output.getvalue(),
                file_name=f"reconciliation_exceptions_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("🎉 No exceptions found - all records match perfectly!")
    
    with tab3:
        st.subheader("📋 Complete Reconciliation Data")
        
        # Filter options
        status_filter = st.multiselect(
            "Filter by Status:",
            options=reconciled['status'].unique(),
            default=reconciled['status'].unique()
        )
        
        filtered_data = reconciled[reconciled['status'].isin(status_filter)]
        
        st.write(f"Showing **{len(filtered_data):,}** of **{len(reconciled):,}** records")
        
        st.dataframe(filtered_data, use_container_width=True, height=400)
        
        # Full export
        output_full = BytesIO()
        with pd.ExcelWriter(output_full, engine='openpyxl') as writer:
            reconciled.to_excel(writer, sheet_name='Full Reconciliation', index=False)
        
        st.download_button(
            label="📥 Download Full Report (Excel)",
            data=output_full.getvalue(),
            file_name=f"reconciliation_full_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #6b7280; font-size: 0.9rem;'>
Built by <strong>RedBlueLab</strong> | Finance Automation for UAE SMEs
</div>
""", unsafe_allow_html=True)