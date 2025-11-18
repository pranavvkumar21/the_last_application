"""
Applications Manager Page - View and manage all applications
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from utils.styles import apply_custom_css, create_status_badge
from utils.db_helper import (
    get_all_applications,
    get_unique_companies,
    get_application_details,
    retry_failed_application,
    export_data_to_csv
)
from config import COLORS, STATUS_COLORS, APPLICATION_STATUSES, ITEMS_PER_PAGE

# Page config
st.set_page_config(page_title="Applications", page_icon="📝", layout="wide")
apply_custom_css()

# Initialize session state
if 'page_number' not in st.session_state:
    st.session_state.page_number = 0
if 'selected_app_id' not in st.session_state:
    st.session_state.selected_app_id = None

# Header
st.title("📝 Applications Manager")
st.markdown("### View, search, and manage all your job applications")
st.markdown("---")

# Filters Section
st.markdown("## 🔍 Search & Filter")

col1, col2, col3, col4 = st.columns(4)

with col1:
    search_term = st.text_input("🔎 Search", placeholder="Job title, company, location...")

with col2:
    status_filter = st.multiselect(
        "📊 Status",
        options=APPLICATION_STATUSES,
        default=None
    )

with col3:
    companies = get_unique_companies()
    company_filter = st.multiselect(
        "🏢 Company",
        options=companies,
        default=None
    )

with col4:
    date_range = st.date_input(
        "📅 Date Range",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now()
    )

# Additional filters in expander
with st.expander("🔧 Advanced Filters"):
    col1, col2, col3 = st.columns(3)
    with col1:
        items_per_page = st.selectbox("Items per page", [25, 50, 100, 250, 500], index=1)
    with col2:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Company A-Z", "Status"])
    with col3:
        application_method = st.multiselect("Application Method", ["Easy Apply", "Standard Apply", "External"])

st.markdown("---")

# Load data with filters
try:
    # Convert date range to tuple
    date_filter = None
    if len(date_range) == 2:
        date_filter = (date_range[0], date_range[1])
    
    df = get_all_applications(
        status_filter=status_filter if status_filter else None,
        company_filter=company_filter if company_filter else None,
        date_range=date_filter,
        search_term=search_term if search_term else None,
        limit=items_per_page,
        offset=st.session_state.page_number * items_per_page
    )
    
    if not df.empty:
        # Summary stats
        st.markdown("## 📊 Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Results", len(df))
        with col2:
            submitted = len(df[df['status'] == 'submitted'])
            st.metric("Submitted", submitted, delta=None)
        with col3:
            failed = len(df[df['status'] == 'failed'])
            st.metric("Failed", failed, delta=None)
        with col4:
            pending = len(df[df['status'] == 'pending'])
            st.metric("Pending", pending, delta=None)
        with col5:
            success_rate = (submitted / len(df) * 100) if len(df) > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        st.markdown("---")
        
        # Interactive Table with AgGrid
        st.markdown("## 📋 Applications Table")
        
        # Prepare dataframe for display
        display_df = df.copy()
        display_df['applied_date'] = pd.to_datetime(display_df['applied_date']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Configure AgGrid
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=items_per_page)
        gb.configure_side_bar()
        gb.configure_selection(
            selection_mode='multiple',
            use_checkbox=True,
            pre_selected_rows=[],
            groupSelectsChildren=True,
            groupSelectsFiltered=True
        )
        
        # Configure columns
        gb.configure_column("application_id", hide=True)
        gb.configure_column("job_id", hide=True)
        gb.configure_column("title", header_name="Job Title", width=300, pinned='left')
        gb.configure_column("company", header_name="Company", width=200)
        gb.configure_column("location", header_name="Location", width=180)
        gb.configure_column("status", header_name="Status", width=120)
        gb.configure_column("applied_date", header_name="Applied Date", width=150)
        gb.configure_column("application_method", header_name="Method", width=150)
        gb.configure_column("confirmation_number", header_name="Confirmation", width=150)
        gb.configure_column("job_link", hide=True)
        gb.configure_column("hirer_name", header_name="Hirer", width=180)
        
        # Set default column properties
        gb.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            editable=False,
            sortable=True,
            filter=True,
            resizable=True
        )
        
        gridOptions = gb.build()
        
        # Display AgGrid
        grid_response = AgGrid(
            display_df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,
            theme='streamlit',
            height=500,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False
        )
        
        # Get selected rows
        selected_rows = grid_response['selected_rows']
        
        # Action buttons for selected rows
        if selected_rows is not None and len(selected_rows) > 0:
            st.markdown("---")
            st.markdown(f"### 🎯 Actions for {len(selected_rows)} selected application(s)")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔄 Retry Selected", use_container_width=True):
                    for row in selected_rows:
                        if row['status'] == 'failed':
                            retry_failed_application(row['application_id'])
                    st.success(f"✅ Retry queued for {len(selected_rows)} application(s)")
                    st.rerun()
            
            with col2:
                if st.button("📥 Export Selected", use_container_width=True):
                    selected_df = pd.DataFrame(selected_rows)
                    csv = export_data_to_csv(selected_df, "selected_applications.csv")
                    st.download_button(
                        "⬇️ Download CSV",
                        csv,
                        "selected_applications.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            with col3:
                if st.button("🔗 Open Job Links", use_container_width=True):
                    st.info("Opening job links in new tabs...")
                    for row in selected_rows:
                        if row['job_link']:
                            st.markdown(f"[{row['title']} at {row['company']}]({row['job_link']})")
            
            with col4:
                if st.button("🗑️ Delete Selected", use_container_width=True):
                    st.warning("⚠️ Delete functionality requires confirmation")
        
        st.markdown("---")
        
        # Export all button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("📥 Export All Results", use_container_width=True):
                csv = export_data_to_csv(df, "all_applications.csv")
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "all_applications.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        # Detailed View Section
        st.markdown("---")
        st.markdown("## 🔍 Application Details")
        
        # Application selector
        app_options = {f"{row['title']} at {row['company']} ({row['application_id']})": row['application_id'] 
                      for _, row in df.iterrows()}
        
        selected_app_key = st.selectbox(
            "Select an application to view details",
            options=list(app_options.keys())
        )
        
        if selected_app_key:
            app_id = app_options[selected_app_key]
            details = get_application_details(app_id)
            
            if details and details['application']:
                app = details['application']
                
                # Application info
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📄 Job Information")
                    st.markdown(f"**Title:** {app[4]}")  # title
                    st.markdown(f"**Company:** {app[5]}")  # company
                    st.markdown(f"**Location:** {app[6]}")  # location
                    st.markdown(f"**Status:** {create_status_badge(app[3])}", unsafe_allow_html=True)
                    if app[11]:  # hirer_name
                        st.markdown(f"**Hirer:** {app[11]}")
                        if app[12]:  # hirer_profile_link
                            st.markdown(f"[View Hirer Profile]({app[12]})")
                
                with col2:
                    st.markdown("### 📊 Application Details")
                    st.markdown(f"**Application ID:** {app[0]}")
                    st.markdown(f"**Applied Date:** {app[2]}")
                    st.markdown(f"**Method:** {app[5] if len(app) > 5 else 'N/A'}")
                    if app[6]:  # confirmation_number
                        st.markdown(f"**Confirmation:** {app[6]}")
                    if app[10]:  # job_link
                        st.markdown(f"[🔗 View Job Posting]({app[10]})")
                
                # Job Description
                with st.expander("📝 Job Description"):
                    if app[7]:  # description
                        st.markdown(app[7])
                    else:
                        st.info("No description available")
                
                # Q&A Section
                if details['qa']:
                    st.markdown("### ❓ Questions & Answers")
                    qa_df = pd.DataFrame(
                        details['qa'],
                        columns=['Question', 'Answer', 'Additional Data', 'Answered At']
                    )
                    st.dataframe(qa_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No Q&A data available for this application")
                
                # Action buttons
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 Retry Application", use_container_width=True):
                        retry_failed_application(app_id)
                        st.success("✅ Retry queued!")
                        st.rerun()
                
                with col2:
                    if st.button("📋 Copy Details", use_container_width=True):
                        st.info("Copy functionality coming soon!")
                
                with col3:
                    if st.button("🗑️ Delete Application", use_container_width=True):
                        st.warning("⚠️ Delete confirmation required")
    
    else:
        st.info("📭 No applications found matching your filters. Try adjusting your search criteria.")
        
        if st.button("🔄 Reset Filters"):
            st.session_state.page_number = 0
            st.rerun()

except Exception as e:
    st.error(f"❌ Error loading applications: {str(e)}")
    with st.expander("🔍 Error Details"):
        st.code(str(e))
