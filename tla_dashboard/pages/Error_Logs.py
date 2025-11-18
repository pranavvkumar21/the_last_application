"""
Error Logs Page - Monitor and troubleshoot application errors
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.styles import apply_custom_css, create_status_badge
from utils.db_helper import get_db_manager
from config import COLORS, CHART_HEIGHT

# Page config
st.set_page_config(page_title="Error Logs", page_icon="⚠️", layout="wide")
apply_custom_css()

# Header
st.title("⚠️ Error Logs & Troubleshooting")
st.markdown("### Monitor and resolve application errors")
st.markdown("---")

try:
    db = get_db_manager()
    
    # Error statistics
    with db.get_connection() as conn:
        error_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_errors,
                SUM(CASE WHEN DATE(applied_date) = CURRENT_DATE THEN 1 ELSE 0 END) as errors_today,
                SUM(CASE WHEN DATE(applied_date) >= CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END) as errors_this_week
            FROM applications
            WHERE status = 'failed'
        """).fetchone()
        
        session_errors = conn.execute("""
            SELECT COUNT(*) as session_errors
            FROM scraping_sessions
            WHERE status = 'failed'
        """).fetchone()
        
        if error_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Application Errors", error_stats[0] or 0)
            
            with col2:
                st.metric("Errors Today", error_stats[1] or 0)
            
            with col3:
                st.metric("Errors This Week", error_stats[2] or 0)
            
            with col4:
                st.metric("Session Errors", session_errors[0] or 0)
    
    st.markdown("---")
    
    # Error trends
    st.markdown("## 📈 Error Trends")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=1)
    
    with db.get_connection() as conn:
        trend_result = conn.execute(f"""
            SELECT 
                DATE(applied_date) as date,
                COUNT(*) as error_count
            FROM applications
            WHERE status = 'failed'
                AND applied_date >= CURRENT_DATE - INTERVAL '{days_back} days'
            GROUP BY DATE(applied_date)
            ORDER BY date
        """).fetchall()
        
        if trend_result:
            trend_df = pd.DataFrame(trend_result, columns=['date', 'error_count'])
            
            fig = px.line(
                trend_df,
                x='date',
                y='error_count',
                title=f'Application Errors - Last {days_back} Days',
                labels={'date': 'Date', 'error_count': 'Error Count'},
                markers=True
            )
            fig.update_traces(line_color=COLORS['danger'], marker=dict(size=10))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No error data available for the selected time period")
    
    st.markdown("---")
    
    # Failed applications
    st.markdown("## 🚫 Failed Applications")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        time_filter = st.selectbox("Time Range", ["All Time", "Today", "Last 7 Days", "Last 30 Days"], index=2)
    
    with col2:
        company_filter = st.text_input("Company", placeholder="Filter by company...")
    
    with col3:
        search_term = st.text_input("Search", placeholder="Job title or keywords...")
    
    with col4:
        sort_by = st.selectbox("Sort By", ["Most Recent", "Company", "Job Title"])
    
    # Build query
    query = """
        SELECT 
            a.application_id,
            a.job_id,
            j.title,
            j.company,
            j.location,
            a.applied_date,
            a.notes,
            j.job_link
        FROM applications a
        LEFT JOIN jobs j ON a.job_id = j.job_id
        WHERE a.status = 'failed'
    """
    
    params = []
    
    # Time filter
    if time_filter == "Today":
        query += " AND DATE(a.applied_date) = CURRENT_DATE"
    elif time_filter == "Last 7 Days":
        query += " AND a.applied_date >= CURRENT_DATE - INTERVAL '7 days'"
    elif time_filter == "Last 30 Days":
        query += " AND a.applied_date >= CURRENT_DATE - INTERVAL '30 days'"
    
    # Company filter
    if company_filter:
        query += " AND j.company ILIKE ?"
        params.append(f"%{company_filter}%")
    
    # Search filter
    if search_term:
        query += " AND (j.title ILIKE ? OR j.company ILIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    # Sorting
    if sort_by == "Most Recent":
        query += " ORDER BY a.applied_date DESC"
    elif sort_by == "Company":
        query += " ORDER BY j.company ASC"
    elif sort_by == "Job Title":
        query += " ORDER BY j.title ASC"
    
    query += " LIMIT 100"
    
    with db.get_connection() as conn:
        errors_result = conn.execute(query, params).fetchall()
        
        if errors_result:
            errors_df = pd.DataFrame(
                errors_result,
                columns=['app_id', 'job_id', 'title', 'company', 'location', 'failed_date', 'error_message', 'job_link']
            )
            
            st.markdown(f"### 📋 Found {len(errors_df)} failed applications")
            
            # Format dates
            errors_df['failed_date'] = pd.to_datetime(errors_df['failed_date']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Display table
            st.dataframe(
                errors_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "app_id": "App ID",
                    "job_id": "Job ID",
                    "title": "Job Title",
                    "company": "Company",
                    "location": "Location",
                    "failed_date": "Failed Date",
                    "error_message": st.column_config.TextColumn("Error Message", width="large"),
                    "job_link": st.column_config.LinkColumn("Link")
                }
            )
            
            st.markdown("---")
            
            # Batch actions
            st.markdown("### ⚡ Bulk Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Retry All Failed Applications", use_container_width=True):
                    from utils.db_helper import retry_failed_application
                    for _, row in errors_df.iterrows():
                        retry_failed_application(row['app_id'])
                    st.success(f"✅ Queued {len(errors_df)} applications for retry!")
                    st.rerun()
            
            with col2:
                if st.button("📥 Export Failed Applications", use_container_width=True):
                    csv = errors_df.to_csv(index=False)
                    st.download_button(
                        "⬇️ Download CSV",
                        csv,
                        "failed_applications.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            with col3:
                if st.button("🗑️ Clear Old Errors (30+ days)", use_container_width=True):
                    st.warning("⚠️ This action requires confirmation")
            
            st.markdown("---")
            
            # Error details view
            st.markdown("### 🔍 Error Details")
            
            error_options = {
                f"{row['title']} at {row['company']} (ID: {row['app_id']})": row['app_id']
                for _, row in errors_df.iterrows()
            }
            
            selected_error_key = st.selectbox(
                "Select an error to view details",
                options=list(error_options.keys())
            )
            
            if selected_error_key:
                error_id = error_options[selected_error_key]
                error_data = errors_df[errors_df['app_id'] == error_id].iloc[0]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("#### 📄 Application Information")
                    st.markdown(f"**Job Title:** {error_data['title']}")
                    st.markdown(f"**Company:** {error_data['company']}")
                    st.markdown(f"**Location:** {error_data['location']}")
                    st.markdown(f"**Failed Date:** {error_data['failed_date']}")
                    
                    if error_data['job_link']:
                        st.markdown(f"[🔗 View Job Posting]({error_data['job_link']})")
                    
                    st.markdown("---")
                    
                    st.markdown("#### ⚠️ Error Message")
                    if error_data['error_message']:
                        st.error(error_data['error_message'])
                    else:
                        st.info("No specific error message recorded")
                
                with col2:
                    st.markdown("#### 🔧 Actions")
                    
                    if st.button("🔄 Retry This Application", use_container_width=True):
                        from utils.db_helper import retry_failed_application
                        retry_failed_application(error_id)
                        st.success("✅ Application queued for retry!")
                        st.rerun()
                    
                    if st.button("📋 View Full Application", use_container_width=True):
                        st.switch_page("pages/2_Applications.py")
                    
                    if st.button("📝 Add Note", use_container_width=True):
                        st.info("Note functionality coming soon")
                    
                    if st.button("🗑️ Delete", use_container_width=True):
                        st.warning("⚠️ Confirm deletion")
        else:
            st.success("🎉 No failed applications found! Great job!")
    
    st.markdown("---")
    
    # Session errors
    st.markdown("## 🔴 Session Errors")
    
    with db.get_connection() as conn:
        session_errors_result = conn.execute("""
            SELECT 
                session_id,
                start_time,
                end_time,
                search_query,
                error_log
            FROM scraping_sessions
            WHERE status = 'failed'
            ORDER BY start_time DESC
            LIMIT 50
        """).fetchall()
        
        if session_errors_result:
            session_errors_df = pd.DataFrame(
                session_errors_result,
                columns=['session_id', 'start_time', 'end_time', 'search_query', 'error_log']
            )
            
            st.markdown(f"### 📋 Found {len(session_errors_df)} failed sessions")
            
            # Format dates
            session_errors_df['start_time'] = pd.to_datetime(session_errors_df['start_time']).dt.strftime('%Y-%m-%d %H:%M')
            session_errors_df['end_time'] = pd.to_datetime(session_errors_df['end_time']).dt.strftime('%Y-%m-%d %H:%M')
            
            for _, session in session_errors_df.iterrows():
                with st.expander(f"Session {session['session_id']} - {session['start_time']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Session Information:**")
                        st.markdown(f"- **Session ID:** {session['session_id']}")
                        st.markdown(f"- **Start Time:** {session['start_time']}")
                        st.markdown(f"- **End Time:** {session['end_time']}")
                        st.markdown(f"- **Search Query:** {session['search_query']}")
                    
                    with col2:
                        st.markdown("**Error Log:**")
                        if session['error_log']:
                            st.code(session['error_log'], language='text')
                        else:
                            st.info("No error log available")
        else:
            st.success("✅ No failed sessions found!")
    
    st.markdown("---")
    
    # Error analytics
    st.markdown("## 📊 Error Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Errors by company
        with db.get_connection() as conn:
            company_errors = conn.execute("""
                SELECT 
                    j.company,
                    COUNT(*) as error_count
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                WHERE a.status = 'failed'
                    AND j.company IS NOT NULL
                GROUP BY j.company
                ORDER BY error_count DESC
                LIMIT 10
            """).fetchall()
            
            if company_errors:
                company_errors_df = pd.DataFrame(company_errors, columns=['company', 'error_count'])
                
                fig = px.bar(
                    company_errors_df,
                    y='company',
                    x='error_count',
                    orientation='h',
                    title='Top 10 Companies by Error Count',
                    labels={'company': 'Company', 'error_count': 'Errors'},
                    color='error_count',
                    color_continuous_scale='Reds'
                )
                fig.update_layout(height=CHART_HEIGHT, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No error data by company")
    
    with col2:
        # Error rate over time
        with db.get_connection() as conn:
            error_rate = conn.execute("""
                SELECT 
                    DATE(applied_date) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    ROUND(SUM(CASE WHEN status = 'failed' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as error_rate
                FROM applications
                WHERE applied_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(applied_date)
                ORDER BY date
            """).fetchall()
            
            if error_rate:
                error_rate_df = pd.DataFrame(error_rate, columns=['date', 'total', 'failed', 'error_rate'])
                
                fig = px.line(
                    error_rate_df,
                    x='date',
                    y='error_rate',
                    title='Error Rate Over Time (%)',
                    labels={'date': 'Date', 'error_rate': 'Error Rate (%)'},
                    markers=True
                )
                fig.update_traces(line_color=COLORS['warning'])
                fig.update_layout(height=CHART_HEIGHT)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No error rate data available")

except Exception as e:
    st.error(f"❌ Error loading error logs: {str(e)}")
    with st.expander("🔍 Error Details"):
        st.code(str(e))
