"""
Company Intelligence Page - Detailed company insights and analytics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.styles import apply_custom_css, create_custom_card
from utils.db_helper import get_db_manager, get_unique_companies
from config import COLORS, CHART_HEIGHT

# Page config
st.set_page_config(page_title="Company Intelligence", page_icon="🏢", layout="wide")
apply_custom_css()

# Header
st.title("🏢 Company Intelligence")
st.markdown("### Insights and analytics about companies you're applying to")
st.markdown("---")

try:
    db = get_db_manager()
    
    # Company overview metrics
    with db.get_connection() as conn:
        company_stats = conn.execute("""
            SELECT 
                COUNT(DISTINCT company) as total_companies,
                COUNT(DISTINCT CASE WHEN is_applied = true THEN company END) as companies_applied,
                AVG(CASE WHEN is_applied = true THEN 1.0 ELSE 0 END) * 100 as avg_application_rate
            FROM jobs
            WHERE company IS NOT NULL
        """).fetchone()
        
        if company_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Companies", company_stats[0] or 0)
            
            with col2:
                st.metric("Companies Applied To", company_stats[1] or 0)
            
            with col3:
                st.metric("Avg Application Rate", f"{company_stats[2] or 0:.1f}%")
            
            with col4:
                companies_pending = company_stats[0] - company_stats[1] if company_stats[0] and company_stats[1] else 0
                st.metric("Companies Pending", companies_pending)
    
    st.markdown("---")
    
    # Company directory and search
    st.markdown("## 🔍 Company Directory")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_company = st.text_input("🔎 Search Company", placeholder="Enter company name...")
    
    with col2:
        sort_by = st.selectbox("Sort By", ["Most Jobs", "Name A-Z", "Application Rate", "Recent Activity"])
    
    with col3:
        min_jobs = st.number_input("Min Jobs", min_value=0, value=1, step=1)
    
    # Load company data
    with db.get_connection() as conn:
        query = """
            SELECT 
                j.company,
                COUNT(DISTINCT j.job_id) as total_jobs,
                COUNT(DISTINCT CASE WHEN j.is_applied = true THEN j.job_id END) as jobs_applied,
                COUNT(DISTINCT a.application_id) as total_applications,
                SUM(CASE WHEN a.status = 'submitted' THEN 1 ELSE 0 END) as successful_applications,
                MIN(j.scraped_at) as first_seen,
                MAX(j.scraped_at) as last_seen,
                ROUND(SUM(CASE WHEN a.status = 'submitted' THEN 1.0 ELSE 0 END) / 
                      NULLIF(COUNT(a.application_id), 0) * 100, 2) as success_rate
            FROM jobs j
            LEFT JOIN applications a ON j.job_id = a.job_id
            WHERE j.company IS NOT NULL
        """
        
        params = []
        
        if search_company:
            query += " AND j.company ILIKE ?"
            params.append(f"%{search_company}%")
        
        query += " GROUP BY j.company"
        query += f" HAVING COUNT(DISTINCT j.job_id) >= ?"
        params.append(min_jobs)
        
        # Sorting
        if sort_by == "Most Jobs":
            query += " ORDER BY total_jobs DESC"
        elif sort_by == "Name A-Z":
            query += " ORDER BY j.company ASC"
        elif sort_by == "Application Rate":
            query += " ORDER BY success_rate DESC NULLS LAST"
        elif sort_by == "Recent Activity":
            query += " ORDER BY last_seen DESC"
        
        result = conn.execute(query, params).fetchall()
        
        columns = ['company', 'total_jobs', 'jobs_applied', 'total_applications', 
                  'successful_applications', 'first_seen', 'last_seen', 'success_rate']
        companies_df = pd.DataFrame(result, columns=columns)
    
    if not companies_df.empty:
        st.markdown(f"### 📋 Found {len(companies_df)} companies")
        
        # Display companies as cards
        st.markdown("---")
        
        # Company cards in grid
        cols_per_row = 3
        for i in range(0, len(companies_df), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(companies_df):
                    company = companies_df.iloc[i + j]
                    
                    with col:
                        # Company card
                        st.markdown(f"""
                        <div class="custom-card">
                            <h3 style="color: {COLORS['primary']}; margin-bottom: 1rem;">
                                🏢 {company['company']}
                            </h3>
                            <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">
                                <strong>{company['total_jobs']}</strong> Jobs Posted
                            </p>
                            <p style="color: #64748b; margin-bottom: 0.3rem;">
                                ✅ Applied: <strong>{company['jobs_applied']}</strong>
                            </p>
                            <p style="color: #64748b; margin-bottom: 0.3rem;">
                                📊 Success Rate: <strong>{company['success_rate'] or 0:.1f}%</strong>
                            </p>
                            <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem;">
                                Last seen: {pd.to_datetime(company['last_seen']).strftime('%Y-%m-%d')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"📊 View Details", key=f"view_{company['company']}", use_container_width=True):
                            st.session_state.selected_company = company['company']
        
        st.markdown("---")
        
        # Detailed company view
        if 'selected_company' in st.session_state and st.session_state.selected_company:
            st.markdown(f"## 🔍 Deep Dive: {st.session_state.selected_company}")
            
            company_name = st.session_state.selected_company
            company_data = companies_df[companies_df['company'] == company_name].iloc[0]
            
            # Company overview
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Jobs", company_data['total_jobs'])
            
            with col2:
                st.metric("Applications", company_data['total_applications'])
            
            with col3:
                st.metric("Successful", company_data['successful_applications'])
            
            with col4:
                st.metric("Success Rate", f"{company_data['success_rate'] or 0:.1f}%")
            
            with col5:
                days_active = (pd.to_datetime(company_data['last_seen']) - pd.to_datetime(company_data['first_seen'])).days
                st.metric("Days Active", days_active)
            
            st.markdown("---")
            
            # Jobs timeline
            with db.get_connection() as conn:
                timeline_result = conn.execute("""
                    SELECT 
                        DATE(scraped_at) as date,
                        COUNT(*) as jobs_posted
                    FROM jobs
                    WHERE company = ?
                    GROUP BY DATE(scraped_at)
                    ORDER BY date
                """, [company_name]).fetchall()
                
                if timeline_result:
                    timeline_df = pd.DataFrame(timeline_result, columns=['date', 'jobs_posted'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📅 Job Posting Timeline")
                        fig = px.area(
                            timeline_df,
                            x='date',
                            y='jobs_posted',
                            title=f'Jobs Posted by {company_name} Over Time',
                            labels={'date': 'Date', 'jobs_posted': 'Jobs Posted'},
                            color_discrete_sequence=[COLORS['primary']]
                        )
                        fig.update_layout(height=CHART_HEIGHT)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Application success timeline
                        app_timeline_result = conn.execute("""
                            SELECT 
                                DATE(a.applied_date) as date,
                                COUNT(*) as total,
                                SUM(CASE WHEN a.status = 'submitted' THEN 1 ELSE 0 END) as successful
                            FROM applications a
                            JOIN jobs j ON a.job_id = j.job_id
                            WHERE j.company = ?
                            GROUP BY DATE(a.applied_date)
                            ORDER BY date
                        """, [company_name]).fetchall()
                        
                        if app_timeline_result:
                            app_timeline_df = pd.DataFrame(app_timeline_result, columns=['date', 'total', 'successful'])
                            
                            st.markdown("### 📊 Application Success Rate")
                            fig = go.Figure()
                            
                            fig.add_trace(go.Bar(
                                x=app_timeline_df['date'],
                                y=app_timeline_df['total'],
                                name='Total Applications',
                                marker_color=COLORS['info']
                            ))
                            
                            fig.add_trace(go.Bar(
                                x=app_timeline_df['date'],
                                y=app_timeline_df['successful'],
                                name='Successful',
                                marker_color=COLORS['success']
                            ))
                            
                            fig.update_layout(
                                barmode='overlay',
                                height=CHART_HEIGHT,
                                xaxis_title='Date',
                                yaxis_title='Applications'
                            )
                            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Jobs from this company
            st.markdown("### 📋 All Jobs from this Company")
            
            with db.get_connection() as conn:
                jobs_result = conn.execute("""
                    SELECT 
                        j.job_id,
                        j.title,
                        j.location,
                        j.scraped_at,
                        j.is_applied,
                        j.job_link,
                        a.status as application_status,
                        a.applied_date
                    FROM jobs j
                    LEFT JOIN applications a ON j.job_id = a.job_id
                    WHERE j.company = ?
                    ORDER BY j.scraped_at DESC
                """, [company_name]).fetchall()
                
                jobs_df = pd.DataFrame(
                    jobs_result,
                    columns=['job_id', 'title', 'location', 'scraped_at', 'is_applied', 'job_link', 'application_status', 'applied_date']
                )
                
                # Format dates
                jobs_df['scraped_at'] = pd.to_datetime(jobs_df['scraped_at']).dt.strftime('%Y-%m-%d')
                jobs_df['applied_date'] = pd.to_datetime(jobs_df['applied_date']).dt.strftime('%Y-%m-%d')
                
                st.dataframe(
                    jobs_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "job_id": "Job ID",
                        "title": "Job Title",
                        "location": "Location",
                        "scraped_at": "Posted Date",
                        "is_applied": st.column_config.CheckboxColumn("Applied"),
                        "job_link": st.column_config.LinkColumn("Link"),
                        "application_status": "Status",
                        "applied_date": "Applied Date"
                    }
                )
            
            # Clear selection button
            if st.button("← Back to Company List"):
                del st.session_state.selected_company
                st.rerun()
        
        else:
            # Show top companies charts
            st.markdown("## 📊 Company Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top companies by job count
                top_10 = companies_df.nlargest(10, 'total_jobs')
                fig = px.bar(
                    top_10,
                    y='company',
                    x='total_jobs',
                    orientation='h',
                    title='Top 10 Companies by Job Count',
                    labels={'company': 'Company', 'total_jobs': 'Total Jobs'},
                    color='total_jobs',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=CHART_HEIGHT, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Companies by success rate (min 3 applications)
                qualified_companies = companies_df[companies_df['total_applications'] >= 3].nlargest(10, 'success_rate')
                
                if not qualified_companies.empty:
                    fig = px.bar(
                        qualified_companies,
                        y='company',
                        x='success_rate',
                        orientation='h',
                        title='Top Companies by Success Rate',
                        labels={'company': 'Company', 'success_rate': 'Success Rate (%)'},
                        color='success_rate',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_layout(height=CHART_HEIGHT, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not enough application data to show success rates (minimum 3 applications per company)")
        
        st.markdown("---")
        
        # Export company data
        st.markdown("## 📥 Export Company Data")
        
        if st.button("📊 Export All Company Data", use_container_width=False):
            csv = companies_df.to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                csv,
                "company_intelligence.csv",
                "text/csv"
            )
    
    else:
        st.info("📭 No company data available matching your criteria.")

except Exception as e:
    st.error(f"❌ Error loading company intelligence: {str(e)}")
    with st.expander("🔍 Error Details"):
        st.code(str(e))
