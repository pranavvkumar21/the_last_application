"""
Overview Dashboard Page - Main metrics and visualizations
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils.styles import apply_custom_css, create_metric_card
from utils.db_helper import (
    get_dashboard_stats, 
    get_applications_over_time,
    get_application_status_distribution,
    get_top_companies
)
from utils.chart_helper import (
    create_status_pie_chart,
    create_timeline_chart,
    create_gauge_chart,
    create_funnel_chart
)
from config import COLORS

# Page config
st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")
apply_custom_css()

# Header
st.title("📊 Overview Dashboard")
st.markdown("### Your job application bot at a glance")
st.markdown("---")

# Load data
try:
    stats = get_dashboard_stats()
    
    # Hero Metrics Section
    st.markdown("## 📈 Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(
            create_metric_card(
                "Total Applications",
                stats['total_applications'],
                delta=stats['today_apps'],
                delta_color="normal"
            ),
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            create_metric_card(
                "Success Rate",
                f"{stats['success_rate']:.1f}%",
                delta=None
            ),
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            create_metric_card(
                "Jobs Available",
                stats['jobs_not_applied'],
                delta=None
            ),
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            create_metric_card(
                "This Week",
                stats['week_apps'],
                delta=None
            ),
            unsafe_allow_html=True
        )
    
    with col5:
        st.markdown(
            create_metric_card(
                "Avg. Time",
                f"{stats['avg_time']:.1f} min",
                delta=None
            ),
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🎯 Application Status")
        status_df = get_application_status_distribution()
        if not status_df.empty:
            fig = create_status_pie_chart(status_df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No application data available yet.")
    
    with col2:
        st.markdown("## 📊 Success Gauge")
        if stats['total_applications'] > 0:
            fig = create_gauge_chart(
                stats['success_rate'],
                "Overall Success Rate",
                max_value=100
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Start applying to jobs to see your success rate!")
    
    st.markdown("---")
    
    # Timeline Chart
    st.markdown("## 📅 Application Timeline")
    
    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2)
    with col2:
        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Area"])
    
    timeline_df = get_applications_over_time(days=days_back)
    
    if not timeline_df.empty:
        if chart_type == "Line":
            fig = create_timeline_chart(timeline_df)
        elif chart_type == "Bar":
            fig = px.bar(
                timeline_df,
                x='date',
                y='count',
                title='Applications Over Time',
                color_discrete_sequence=[COLORS['primary']]
            )
        else:  # Area
            fig = px.area(
                timeline_df,
                x='date',
                y='count',
                title='Applications Over Time',
                color_discrete_sequence=[COLORS['primary']]
            )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available yet.")
    
    st.markdown("---")
    
    # Top Companies and Funnel
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🏢 Top Companies")
        companies_df = get_top_companies(limit=8)
        if not companies_df.empty:
            fig = px.bar(
                companies_df,
                y='company',
                x='job_count',
                orientation='h',
                text='job_count',
                color='application_rate',
                color_continuous_scale='Viridis',
                labels={'job_count': 'Jobs', 'application_rate': 'Applied %'}
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                height=400,
                yaxis={'categoryorder':'total ascending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No company data available yet.")
    
    with col2:
        st.markdown("## 🔄 Application Funnel")
        funnel_data = {
            'Jobs Scraped': stats['total_jobs'],
            'Jobs Attempted': stats['total_applications'],
            'Successfully Applied': stats['apps_submitted'],
            'Confirmed': stats['apps_submitted']  # Adjust if you track confirmations
        }
        fig = create_funnel_chart(funnel_data)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("## ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Retry Failed Apps", use_container_width=True):
            st.info("Retry functionality will trigger the bot to reprocess failed applications.")
    
    with col2:
        if st.button("📥 Export Data", use_container_width=True):
            st.info("Export functionality coming soon!")
    
    with col3:
        if st.button("⚠️ View Errors", use_container_width=True):
            st.switch_page("pages/8_Error_Logs.py")
    
    with col4:
        if st.button("📝 View Applications", use_container_width=True):
            st.switch_page("pages/2_Applications.py")
    
    # Last updated
    st.markdown("---")
    st.caption(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
except Exception as e:
    st.error(f"❌ Error loading dashboard data: {str(e)}")
    st.info("Make sure your database is properly initialized and contains data.")
