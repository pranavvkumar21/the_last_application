"""
Analytics Page - Deep dive into application data and trends
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.styles import apply_custom_css
from utils.db_helper import (
    get_applications_over_time,
    get_top_companies,
    get_success_rate_by_company,
    get_job_locations,
    get_db_manager
)
from utils.chart_helper import (
    create_company_bar_chart,
    create_success_rate_chart,
    create_location_treemap
)
from config import COLORS, CHART_HEIGHT

# Page config
st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")
apply_custom_css()

# Header
st.title("📈 Analytics & Insights")
st.markdown("### Deep dive into your job application data")
st.markdown("---")

# Time period selector
col1, col2, col3 = st.columns([2, 2, 4])
with col1:
    time_period = st.selectbox("📅 Time Period", [7, 14, 30, 60, 90, 180], format_func=lambda x: f"Last {x} days", index=2)
with col2:
    refresh = st.button("🔄 Refresh Data")
    if refresh:
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

try:
    # Applications Over Time
    st.markdown("## 📊 Application Trends")
    
    timeline_df = get_applications_over_time(days=time_period)
    
    if not timeline_df.empty:
        # Create multi-line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timeline_df['date'],
            y=timeline_df['count'],
            name='Total Applications',
            mode='lines+markers',
            line=dict(color=COLORS['primary'], width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor=f'rgba(99, 102, 241, 0.1)'
        ))
        
        fig.add_trace(go.Scatter(
            x=timeline_df['date'],
            y=timeline_df['submitted'],
            name='Successful',
            mode='lines+markers',
            line=dict(color=COLORS['success'], width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=timeline_df['date'],
            y=timeline_df['failed'],
            name='Failed',
            mode='lines+markers',
            line=dict(color=COLORS['danger'], width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f'Application Activity - Last {time_period} Days',
            xaxis_title='Date',
            yaxis_title='Number of Applications',
            height=CHART_HEIGHT,
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_apps = timeline_df['count'].sum()
        avg_daily = timeline_df['count'].mean()
        max_day = timeline_df.loc[timeline_df['count'].idxmax()]
        success_rate = (timeline_df['submitted'].sum() / total_apps * 100) if total_apps > 0 else 0
        
        with col1:
            st.metric("Total Applications", int(total_apps))
        with col2:
            st.metric("Daily Average", f"{avg_daily:.1f}")
        with col3:
            st.metric("Best Day", f"{max_day['count']} apps", delta=f"{max_day['date'].strftime('%b %d')}")
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
    
    else:
        st.info("No application data available for the selected time period.")
    
    st.markdown("---")
    
    # Company Analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🏢 Top Companies")
        companies_df = get_top_companies(limit=15)
        
        if not companies_df.empty:
            fig = create_company_bar_chart(companies_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Top companies table
            with st.expander("📋 View Company Details"):
                st.dataframe(
                    companies_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "company": "Company",
                        "job_count": st.column_config.NumberColumn("Total Jobs", format="%d"),
                        "applied_count": st.column_config.NumberColumn("Applied", format="%d"),
                        "application_rate": st.column_config.NumberColumn("Application Rate", format="%.1f%%")
                    }
                )
        else:
            st.info("No company data available.")
    
    with col2:
        st.markdown("## 🎯 Success Rate by Company")
        success_df = get_success_rate_by_company()
        
        if not success_df.empty:
            fig = create_success_rate_chart(success_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Success rate table
            with st.expander("📋 View Success Rates"):
                st.dataframe(
                    success_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "company": "Company",
                        "total_applications": st.column_config.NumberColumn("Total Apps", format="%d"),
                        "successful": st.column_config.NumberColumn("Successful", format="%d"),
                        "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1f%%")
                    }
                )
        else:
            st.info("No success rate data available.")
    
    st.markdown("---")
    
    # Location Analytics
    st.markdown("## 🌍 Geographic Distribution")
    
    locations_df = get_job_locations(limit=20)
    
    if not locations_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Treemap
            fig = create_location_treemap(locations_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top locations list
            st.markdown("### 📍 Top Locations")
            for idx, row in locations_df.head(10).iterrows():
                percentage = (row['count'] / locations_df['count'].sum() * 100)
                st.markdown(f"**{row['location']}**")
                st.progress(percentage / 100)
                st.caption(f"{row['count']} jobs ({percentage:.1f}%)")
    else:
        st.info("No location data available.")
    
    st.markdown("---")
    
    # Application Method Analysis
    st.markdown("## 📝 Application Methods")
    
    db = get_db_manager()
    with db.get_connection() as conn:
        method_result = conn.execute("""
            SELECT 
                application_method,
                COUNT(*) as count,
                ROUND(AVG(CASE WHEN status = 'submitted' THEN 100 ELSE 0 END), 2) as success_rate
            FROM applications
            WHERE application_method IS NOT NULL
            GROUP BY application_method
        """).fetchall()
        
        if method_result:
            method_df = pd.DataFrame(method_result, columns=['method', 'count', 'success_rate'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart
                fig = px.bar(
                    method_df,
                    x='method',
                    y='count',
                    title='Applications by Method',
                    color='success_rate',
                    color_continuous_scale='RdYlGn',
                    text='count'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pie chart
                fig = px.pie(
                    method_df,
                    values='count',
                    names='method',
                    title='Application Method Distribution',
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No application method data available.")
    
    st.markdown("---")
    
    # Weekly Pattern Analysis
    st.markdown("## 📅 Application Patterns")
    
    with db.get_connection() as conn:
        pattern_result = conn.execute(f"""
            SELECT 
                DAYNAME(applied_date) as day_of_week,
                HOUR(applied_date) as hour,
                COUNT(*) as count
            FROM applications
            WHERE applied_date >= CURRENT_DATE - INTERVAL '{time_period} days'
            GROUP BY day_of_week, hour
            ORDER BY 
                CASE day_of_week
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                END,
                hour
        """).fetchall()
        
        if pattern_result:
            pattern_df = pd.DataFrame(pattern_result, columns=['day_of_week', 'hour', 'count'])
            
            # Create pivot table for heatmap
            pivot_df = pattern_df.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
            
            # Reorder days
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot_df = pivot_df.reindex([day for day in day_order if day in pivot_df.index])
            
            fig = px.imshow(
                pivot_df,
                labels=dict(x="Hour of Day", y="Day of Week", color="Applications"),
                x=[f"{h}:00" for h in pivot_df.columns],
                y=pivot_df.index,
                color_continuous_scale='Blues',
                title='Application Activity Heatmap'
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            st.markdown("### 💡 Insights")
            most_active_day = pattern_df.groupby('day_of_week')['count'].sum().idxmax()
            most_active_hour = pattern_df.groupby('hour')['count'].sum().idxmax()
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📆 Most active day: **{most_active_day}**")
            with col2:
                st.info(f"🕐 Most active hour: **{most_active_hour}:00**")
        else:
            st.info("Not enough data to show application patterns.")
    
    st.markdown("---")
    
    # Export Section
    st.markdown("## 📥 Export Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Timeline Data", use_container_width=True):
            csv = timeline_df.to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                csv,
                "timeline_data.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("🏢 Export Company Data", use_container_width=True):
            csv = companies_df.to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                csv,
                "company_data.csv",
                "text/csv"
            )
    
    with col3:
        if st.button("📈 Generate Report", use_container_width=True):
            st.info("📄 Full analytics report generation coming soon!")
    apply_custom_css()

except Exception as e:
    st.error(f"❌ Error loading analytics: {str(e)}")
    with st.expander("🔍 Error Details"):
        st.code(str(e))
