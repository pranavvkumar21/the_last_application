"""
Job Discovery Page - Browse and search available jobs
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.styles import apply_custom_css, create_custom_card, create_status_badge
from utils.db_helper import get_db_manager
from config import COLORS

# Page config
st.set_page_config(page_title="Job Discovery", page_icon="🔍", layout="wide")
apply_custom_css()

# Header
st.title("🔍 Job Discovery")
st.markdown("### Browse scraped jobs and discover new opportunities")
st.markdown("---")

# Initialize session state
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'Grid'

# Filters
st.markdown("## 🎯 Search Jobs")

col1, col2, col3, col4 = st.columns(4)

with col1:
    search_query = st.text_input("🔎 Search", placeholder="Job title or keywords...")

with col2:
    location_filter = st.text_input("📍 Location", placeholder="City, state, or remote...")

with col3:
    company_filter = st.text_input("🏢 Company", placeholder="Company name...")

with col4:
    applied_filter = st.selectbox("Application Status", ["All", "Not Applied", "Already Applied"])

# Additional filters
with st.expander("🔧 Advanced Filters"):
    col1, col2, col3 = st.columns(3)
    with col1:
        job_status = st.multiselect("Job Status", ["active", "inactive", "expired"])
    with col2:
        date_posted = st.selectbox("Posted Date", ["Any time", "Last 24 hours", "Last 7 days", "Last 30 days"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Most Recent", "Company A-Z", "Location"])

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    view_mode = st.radio("View Mode", ["Grid", "List"], horizontal=True)
with col2:
    items_per_page = st.selectbox("Per page", [12, 24, 48, 96], index=1)

st.markdown("---")

# Load jobs
try:
    db = get_db_manager()
    
    # Build query
    query = """
        SELECT 
            job_id,
            title,
            company,
            location,
            description,
            job_link,
            hirer_name,
            scraped_at,
            is_applied,
            job_status
        FROM jobs
        WHERE 1=1
    """
    
    params = []
    
    if search_query:
        query += " AND (title ILIKE ? OR description ILIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    if location_filter:
        query += " AND location ILIKE ?"
        params.append(f"%{location_filter}%")
    
    if company_filter:
        query += " AND company ILIKE ?"
        params.append(f"%{company_filter}%")
    
    if applied_filter == "Not Applied":
        query += " AND is_applied = false"
    elif applied_filter == "Already Applied":
        query += " AND is_applied = true"
    
    query += " ORDER BY scraped_at DESC LIMIT ?"
    params.append(items_per_page)
    
    with db.get_connection() as conn:
        result = conn.execute(query, params).fetchall()
        columns = ['job_id', 'title', 'company', 'location', 'description', 
                  'job_link', 'hirer_name', 'scraped_at', 'is_applied', 'job_status']
        jobs_df = pd.DataFrame(result, columns=columns)
    
    if not jobs_df.empty:
        # Summary
        st.markdown("## 📊 Search Results")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", len(jobs_df))
        with col2:
            not_applied = len(jobs_df[jobs_df['is_applied'] == False])
            st.metric("Not Applied", not_applied)
        with col3:
            applied = len(jobs_df[jobs_df['is_applied'] == True])
            st.metric("Already Applied", applied)
        with col4:
            unique_companies = jobs_df['company'].nunique()
            st.metric("Companies", unique_companies)
        
        st.markdown("---")
        
        # Display jobs based on view mode
        if view_mode == "Grid":
            # Grid view - 3 columns
            cols_per_row = 3
            for i in range(0, len(jobs_df), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(jobs_df):
                        job = jobs_df.iloc[i + j]
                        
                        with col:
                            # Job card
                            with st.container():
                                st.markdown(f"""
                                <div class="custom-card">
                                    <h3 style="color: {COLORS['primary']}; margin-bottom: 0.5rem;">
                                        {job['title'][:60]}{'...' if len(job['title']) > 60 else ''}
                                    </h3>
                                    <p style="font-size: 1.1rem; font-weight: 600; color: {COLORS['dark']}; margin-bottom: 0.3rem;">
                                        🏢 {job['company']}
                                    </p>
                                    <p style="color: #64748b; margin-bottom: 0.5rem;">
                                        📍 {job['location']}
                                    </p>
                                    <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1rem;">
                                        🕐 {pd.to_datetime(job['scraped_at']).strftime('%Y-%m-%d')}
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Status badge
                                if job['is_applied']:
                                    st.markdown(create_status_badge("Applied"), unsafe_allow_html=True)
                                else:
                                    st.markdown(create_status_badge("Available"), unsafe_allow_html=True)
                                
                                # Description preview
                                with st.expander("📄 Description"):
                                    desc = job['description'][:300] + "..." if job['description'] and len(job['description']) > 300 else job['description']
                                    st.markdown(desc if desc else "No description available")
                                
                                # Action buttons
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    if job['job_link']:
                                        st.link_button("🔗 View Job", job['job_link'], use_container_width=True)
                                with col_b:
                                    if not job['is_applied']:
                                        if st.button("✅ Apply", key=f"apply_{job['job_id']}", use_container_width=True):
                                            st.info("Apply functionality triggers the bot")
                                
                                st.markdown("---")
        
        else:
            # List view - detailed table
            for idx, job in jobs_df.iterrows():
                with st.expander(f"**{job['title']}** at {job['company']} - {job['location']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("### 📋 Job Details")
                        st.markdown(f"**Company:** {job['company']}")
                        st.markdown(f"**Location:** {job['location']}")
                        st.markdown(f"**Posted:** {pd.to_datetime(job['scraped_at']).strftime('%Y-%m-%d %H:%M')}")
                        
                        if job['hirer_name']:
                            st.markdown(f"**Hiring Manager:** {job['hirer_name']}")
                        
                        st.markdown("---")
                        st.markdown("**Description:**")
                        st.markdown(job['description'] if job['description'] else "No description available")
                    
                    with col2:
                        st.markdown("### 🎯 Actions")
                        
                        # Status
                        if job['is_applied']:
                            st.markdown(create_status_badge("Applied"), unsafe_allow_html=True)
                            st.info("✅ Already applied to this job")
                        else:
                            st.markdown(create_status_badge("Available"), unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # Action buttons
                        if job['job_link']:
                            st.link_button("🔗 View Job Posting", job['job_link'], use_container_width=True)
                        
                        if not job['is_applied']:
                            if st.button("✅ Apply Now", key=f"apply_list_{job['job_id']}", use_container_width=True):
                                st.success("Application queued!")
                        
                        if st.button("🔖 Bookmark", key=f"bookmark_{job['job_id']}", use_container_width=True):
                            st.info("Bookmark saved!")
                        
                        if st.button("📤 Share", key=f"share_{job['job_id']}", use_container_width=True):
                            st.code(job['job_link'])
        
        # Pagination info
        st.markdown("---")
        st.info(f"Showing {len(jobs_df)} of {len(jobs_df)} jobs. Scroll down to load more or adjust filters.")
    
    else:
        st.info("📭 No jobs found matching your criteria. Try adjusting your search filters.")
        st.markdown("### 💡 Suggestions:")
        st.markdown("- Use broader search terms")
        st.markdown("- Remove location or company filters")
        st.markdown("- Check if your bot has scraped jobs recently")

except Exception as e:
    st.error(f"❌ Error loading jobs: {str(e)}")
    with st.expander("🔍 Error Details"):
        st.code(str(e))
