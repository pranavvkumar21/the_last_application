"""
Bot Performance Page - Monitor bot sessions and performance metrics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.styles import apply_custom_css, create_status_badge, create_metric_card
from utils.db_helper import get_scraping_sessions, get_db_manager
from config import COLORS, CHART_HEIGHT

# Page config
st.set_page_config(page_title="Bot Performance", page_icon="⚙️", layout="wide")
apply_custom_css()

# Header
st.title("⚙️ Bot Performance Monitor")
st.markdown("### Track bot activity, sessions, and performance metrics")
st.markdown("---")

# Real-time status indicator
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("## 🤖 Bot Status")
with col2:
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
with col3:
    if st.button("↻ Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Bot status card
try:
    db = get_db_manager()
    
    # Check for active sessions
    with db.get_connection() as conn:
        active_session = conn.execute("""
            SELECT session_id, start_time, search_query, jobs_found
            FROM scraping_sessions
            WHERE status = 'in_progress'
            ORDER BY start_time DESC
            LIMIT 1
        """).fetchone()
        
        if active_session:
            st.success("✅ Bot is currently running")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Session ID", active_session[0])
            with col2:
                duration = datetime.now() - pd.to_datetime(active_session[1])
                st.metric("Running Time", f"{int(duration.total_seconds() / 60)} min")
            with col3:
                st.metric("Search Query", active_session[2] or "N/A")
            with col4:
                st.metric("Jobs Found", active_session[3] or 0)
            
            # Progress bar (simulated)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            if auto_refresh:
                import time
                for percent_complete in range(100):
                    time.sleep(0.05)
                    progress_bar.progress(percent_complete + 1)
                    status_text.text(f"Processing... {percent_complete + 1}%")
                st.rerun()
        else:
            st.info("⏸️ Bot is currently idle")
    
    st.markdown("---")
    
    # Performance metrics
    st.markdown("## 📊 Performance Metrics")
    
    with db.get_connection() as conn:
        # Overall stats
        overall_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(jobs_found) as total_jobs_found,
                SUM(jobs_new) as total_new_jobs,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))/60) as avg_duration_minutes,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_sessions,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_sessions
            FROM scraping_sessions
            WHERE end_time IS NOT NULL
        """).fetchone()
        
        if overall_stats:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(
                    create_metric_card(
                        "Total Sessions",
                        overall_stats[0] or 0,
                        delta=None
                    ),
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    create_metric_card(
                        "Jobs Found",
                        overall_stats[1] or 0,
                        delta=None
                    ),
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    create_metric_card(
                        "New Jobs",
                        overall_stats[2] or 0,
                        delta=None
                    ),
                    unsafe_allow_html=True
                )
            
            with col4:
                avg_duration = overall_stats[3] or 0
                st.markdown(
                    create_metric_card(
                        "Avg Duration",
                        f"{avg_duration:.1f} min",
                        delta=None
                    ),
                    unsafe_allow_html=True
                )
            
            with col5:
                success_rate = (overall_stats[4] / overall_stats[0] * 100) if overall_stats[0] > 0 else 0
                st.markdown(
                    create_metric_card(
                        "Success Rate",
                        f"{success_rate:.1f}%",
                        delta=None
                    ),
                    unsafe_allow_html=True
                )
    
    st.markdown("---")
    
    # Session history
    st.markdown("## 📜 Session History")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.multiselect(
            "Status",
            ["completed", "failed", "in_progress"],
            default=None
        )
    
    with col2:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=1)
    
    with col3:
        min_jobs = st.number_input("Min Jobs Found", min_value=0, value=0)
    
    with col4:
        sort_order = st.selectbox("Sort By", ["Most Recent", "Most Jobs", "Longest Duration"])
    
    # Load sessions
    sessions_df = get_scraping_sessions()
    
    if not sessions_df.empty:
        # Filter by date
        sessions_df['start_time'] = pd.to_datetime(sessions_df['start_time'])
        cutoff_date = datetime.now() - timedelta(days=days_back)
        sessions_df = sessions_df[sessions_df['start_time'] >= cutoff_date]
        
        # Apply filters
        if status_filter:
            sessions_df = sessions_df[sessions_df['status'].isin(status_filter)]
        
        if min_jobs > 0:
            sessions_df = sessions_df[sessions_df['jobs_found'] >= min_jobs]
        
        # Display sessions table
        st.markdown(f"### 📋 Found {len(sessions_df)} sessions")
        
        # Format dataframe
        display_df = sessions_df.copy()
        display_df['start_time'] = display_df['start_time'].dt.strftime('%Y-%m-%d %H:%M')
        if 'end_time' in display_df.columns:
            display_df['end_time'] = pd.to_datetime(display_df['end_time']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Calculate duration
        if 'end_time' in sessions_df.columns and 'start_time' in sessions_df.columns:
            display_df['duration'] = (
                (pd.to_datetime(sessions_df['end_time']) - sessions_df['start_time'])
                .dt.total_seconds() / 60
            ).round(2)
            display_df['duration'] = display_df['duration'].apply(lambda x: f"{x:.1f} min" if pd.notna(x) else "In progress")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "session_id": "Session ID",
                "start_time": "Start Time",
                "end_time": "End Time",
                "duration": "Duration",
                "jobs_found": st.column_config.NumberColumn("Jobs Found", format="%d"),
                "jobs_new": st.column_config.NumberColumn("New Jobs", format="%d"),
                "search_query": "Search Query",
                "status": st.column_config.TextColumn("Status"),
                "error_log": st.column_config.TextColumn("Error Log")
            }
        )
        
        # Session details expander
        st.markdown("---")
        st.markdown("### 🔍 Session Details")
        
        session_options = {
            f"Session {row['session_id']} - {row['start_time'].strftime('%Y-%m-%d %H:%M')}": row['session_id']
            for _, row in sessions_df.iterrows()
        }
        
        selected_session_key = st.selectbox(
            "Select a session to view details",
            options=list(session_options.keys())
        )
        
        if selected_session_key:
            session_id = session_options[selected_session_key]
            session_data = sessions_df[sessions_df['session_id'] == session_id].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Session Information")
                st.markdown(f"**Session ID:** {session_data['session_id']}")
                st.markdown(f"**Status:** {create_status_badge(session_data['status'])}", unsafe_allow_html=True)
                st.markdown(f"**Start Time:** {session_data['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                if pd.notna(session_data['end_time']):
                    st.markdown(f"**End Time:** {pd.to_datetime(session_data['end_time']).strftime('%Y-%m-%d %H:%M:%S')}")
                    duration = (pd.to_datetime(session_data['end_time']) - session_data['start_time']).total_seconds() / 60
                    st.markdown(f"**Duration:** {duration:.2f} minutes")
                st.markdown(f"**Search Query:** {session_data['search_query'] or 'N/A'}")
            
            with col2:
                st.markdown("#### 📈 Results")
                st.metric("Jobs Found", session_data['jobs_found'] or 0)
                st.metric("New Jobs", session_data['jobs_new'] or 0)
                
                duplicate_rate = 0
                if session_data['jobs_found'] and session_data['jobs_found'] > 0:
                    duplicate_rate = ((session_data['jobs_found'] - (session_data['jobs_new'] or 0)) / session_data['jobs_found'] * 100)
                st.metric("Duplicate Rate", f"{duplicate_rate:.1f}%")
            
            # Error log
            if pd.notna(session_data['error_log']) and session_data['error_log']:
                with st.expander("⚠️ Error Log"):
                    st.code(session_data['error_log'], language='text')
        
        st.markdown("---")
        
        # Performance charts
        st.markdown("## 📈 Performance Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Jobs found per session over time
            chart_df = sessions_df[sessions_df['end_time'].notna()].copy()
            chart_df['date'] = chart_df['start_time'].dt.date
            
            fig = px.line(
                chart_df,
                x='start_time',
                y='jobs_found',
                title='Jobs Found Per Session',
                labels={'start_time': 'Session Time', 'jobs_found': 'Jobs Found'},
                markers=True
            )
            fig.update_traces(line_color=COLORS['primary'], marker=dict(size=10))
            fig.update_layout(height=CHART_HEIGHT)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Session duration over time
            duration_df = chart_df.copy()
            if not duration_df.empty:
                duration_df['duration'] = (
                    pd.to_datetime(duration_df['end_time']) - duration_df['start_time']
                ).dt.total_seconds() / 60
                
                fig = px.bar(
                    duration_df,
                    x='start_time',
                    y='duration',
                    title='Session Duration',
                    labels={'start_time': 'Session Time', 'duration': 'Duration (minutes)'},
                    color='duration',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=CHART_HEIGHT)
                st.plotly_chart(fig, use_container_width=True)
        
        # Status distribution
        col1, col2 = st.columns(2)
        
        with col1:
            status_counts = sessions_df['status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title='Session Status Distribution',
                hole=0.4,
                color_discrete_sequence=[COLORS['success'], COLORS['danger'], COLORS['warning']]
            )
            fig.update_layout(height=CHART_HEIGHT)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # New vs duplicate jobs
            new_vs_duplicate = pd.DataFrame({
                'Type': ['New Jobs', 'Duplicate Jobs'],
                'Count': [
                    sessions_df['jobs_new'].sum(),
                    sessions_df['jobs_found'].sum() - sessions_df['jobs_new'].sum()
                ]
            })
            
            fig = px.bar(
                new_vs_duplicate,
                x='Type',
                y='Count',
                title='New vs Duplicate Jobs',
                color='Type',
                color_discrete_sequence=[COLORS['primary'], COLORS['secondary']]
            )
            fig.update_layout(height=CHART_HEIGHT, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Export session data
        st.markdown("## 📥 Export Session Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export All Sessions", use_container_width=True):
                csv = sessions_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "bot_sessions.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📈 Generate Performance Report", use_container_width=True):
                st.info("📄 Detailed performance report generation coming soon!")
    
    else:
        st.info("📭 No session data available. The bot hasn't run any scraping sessions yet.")

except Exception as e:
    st.error(f"❌ Error loading bot performance data: {str(e)}")
    with st.expander("🔍 Error Details"):
        st.code(str(e))

# Auto-refresh logic
if auto_refresh:
    import time
    time.sleep(5)
    st.rerun()
