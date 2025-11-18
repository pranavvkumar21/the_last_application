"""
Database helper functions for querying and data processing
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import streamlit as st
from database import DatabaseManager

@st.cache_resource
def get_db_manager():
    """Get cached database manager instance"""
    from config import DB_PATH
    db = DatabaseManager(str(DB_PATH.parent))
    return db


@st.cache_data(ttl=60)
def get_dashboard_stats():
    """Get key statistics for dashboard"""
    db = get_db_manager()
    with db.get_connection() as conn:
        # Total jobs
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        
        # Total applications
        total_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        
        # Applications by status
        apps_submitted = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE status = 'submitted'"
        ).fetchone()[0]
        
        apps_failed = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE status = 'failed'"
        ).fetchone()[0]
        
        apps_pending = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE status = 'pending'"
        ).fetchone()[0]
        
        # Success rate
        success_rate = (apps_submitted / total_apps * 100) if total_apps > 0 else 0
        
        # Jobs not applied
        jobs_not_applied = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE is_applied = false"
        ).fetchone()[0]
        
        # Today's applications
        today_apps = conn.execute("""
            SELECT COUNT(*) FROM applications 
            WHERE DATE(applied_date) = CURRENT_DATE
        """).fetchone()[0]
        
        # This week's applications
        week_apps = conn.execute("""
            SELECT COUNT(*) FROM applications 
            WHERE applied_date >= CURRENT_DATE - INTERVAL '7 days'
        """).fetchone()[0]
        
        # Average application time (mock data - add timestamp tracking)
        avg_time = 3.5  # minutes
        
        # Last updated
        last_updated = conn.execute(
            "SELECT MAX(scraped_at) FROM jobs"
        ).fetchone()[0]
        
    return {
        "total_jobs": total_jobs,
        "total_applications": total_apps,
        "apps_submitted": apps_submitted,
        "apps_failed": apps_failed,
        "apps_pending": apps_pending,
        "success_rate": success_rate,
        "jobs_not_applied": jobs_not_applied,
        "today_apps": today_apps,
        "week_apps": week_apps,
        "avg_time": avg_time,
        "last_updated": last_updated
    }


@st.cache_data(ttl=60)
def get_all_applications(
    status_filter: Optional[List[str]] = None,
    company_filter: Optional[List[str]] = None,
    date_range: Optional[tuple] = None,
    search_term: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0
):
    """Get all applications with filters"""
    db = get_db_manager()
    
    query = """
        SELECT 
            a.application_id,
            a.job_id,
            j.title,
            j.company,
            j.location,
            a.status,
            a.applied_date,
            a.application_method,
            a.confirmation_number,
            j.job_link,
            j.hirer_name
        FROM applications a
        LEFT JOIN jobs j ON a.job_id = j.job_id
        WHERE 1=1
    """
    
    params = []
    
    if status_filter:
        placeholders = ','.join(['?' for _ in status_filter])
        query += f" AND a.status IN ({placeholders})"
        params.extend(status_filter)
    
    if company_filter:
        placeholders = ','.join(['?' for _ in company_filter])
        query += f" AND j.company IN ({placeholders})"
        params.extend(company_filter)
    
    if date_range:
        query += " AND a.applied_date BETWEEN ? AND ?"
        params.extend(date_range)
    
    if search_term:
        query += " AND (j.title ILIKE ? OR j.company ILIKE ? OR j.location ILIKE ?)"
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    query += " ORDER BY a.applied_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    with db.get_connection() as conn:
        result = conn.execute(query, params).fetchall()
        columns = ['application_id', 'job_id', 'title', 'company', 'location', 
                  'status', 'applied_date', 'application_method', 'confirmation_number',
                  'job_link', 'hirer_name']
        df = pd.DataFrame(result, columns=columns)
    
    return df


@st.cache_data(ttl=60)
def get_applications_over_time(days: int = 30):
    """Get application count over time"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute(f"""
            SELECT 
                DATE(applied_date) as date,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM applications
            WHERE applied_date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY DATE(applied_date)
            ORDER BY date
        """).fetchall()
        
        df = pd.DataFrame(result, columns=['date', 'count', 'submitted', 'failed'])
    
    return df


@st.cache_data(ttl=60)
def get_top_companies(limit: int = 10):
    """Get top companies by job count"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute(f"""
            SELECT 
                company,
                COUNT(*) as job_count,
                SUM(CASE WHEN is_applied = true THEN 1 ELSE 0 END) as applied_count,
                ROUND(SUM(CASE WHEN is_applied = true THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as application_rate
            FROM jobs
            WHERE company IS NOT NULL
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT ?
        """, [limit]).fetchall()
        
        df = pd.DataFrame(result, columns=['company', 'job_count', 'applied_count', 'application_rate'])
    
    return df


@st.cache_data(ttl=60)
def get_application_status_distribution():
    """Get distribution of application statuses"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM applications
            GROUP BY status
        """).fetchall()
        
        df = pd.DataFrame(result, columns=['status', 'count'])
    
    return df


@st.cache_data(ttl=60)
def get_job_locations(limit: int = 15):
    """Get job distribution by location"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute(f"""
            SELECT 
                location,
                COUNT(*) as count
            FROM jobs
            WHERE location IS NOT NULL
            GROUP BY location
            ORDER BY count DESC
            LIMIT ?
        """, [limit]).fetchall()
        
        df = pd.DataFrame(result, columns=['location', 'count'])
    
    return df


@st.cache_data(ttl=60)
def get_scraping_sessions():
    """Get scraping session history"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute("""
            SELECT 
                session_id,
                start_time,
                end_time,
                jobs_found,
                jobs_new,
                search_query,
                status,
                error_log
            FROM scraping_sessions
            ORDER BY start_time DESC
            LIMIT 50
        """).fetchall()
        
        columns = ['session_id', 'start_time', 'end_time', 'jobs_found', 
                  'jobs_new', 'search_query', 'status', 'error_log']
        df = pd.DataFrame(result, columns=columns)
    
    return df


@st.cache_data(ttl=60)
def get_question_analytics():
    """Get analytics on form questions"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute("""
            SELECT 
                fq.question_text,
                fq.question_type,
                COUNT(DISTINCT fr.application_id) as times_asked,
                MODE() WITHIN GROUP (ORDER BY fr.response_value) as most_common_answer
            FROM form_questions fq
            LEFT JOIN form_responses fr ON fq.question_id = fr.question_id
            GROUP BY fq.question_text, fq.question_type
            ORDER BY times_asked DESC
            LIMIT 50
        """).fetchall()
        
        df = pd.DataFrame(result, columns=['question', 'type', 'times_asked', 'most_common_answer'])
    
    return df


@st.cache_data(ttl=60)
def get_application_details(application_id: int):
    """Get detailed information about a specific application"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        # Get application info
        app_info = conn.execute("""
            SELECT 
                a.*,
                j.title,
                j.company,
                j.location,
                j.description,
                j.job_link,
                j.hirer_name,
                j.hirer_profile_link
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.job_id
            WHERE a.application_id = ?
        """, [application_id]).fetchone()
        
        # Get Q&A
        qa = conn.execute("""
            SELECT 
                fq.question_text,
                fr.response_value,
                fr.response_data,
                fr.answered_at
            FROM form_responses fr
            LEFT JOIN form_questions fq ON fr.question_id = fq.question_id
            WHERE fr.application_id = ?
            ORDER BY fr.answered_at
        """, [application_id]).fetchall()
    
    return {
        'application': app_info,
        'qa': qa
    }


def retry_failed_application(application_id: int):
    """Retry a failed application"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        conn.execute("""
            UPDATE applications
            SET status = 'pending', notes = COALESCE(notes || ' | Retry requested', 'Retry requested')
            WHERE application_id = ?
        """, [application_id])
    
    st.cache_data.clear()


def export_data_to_csv(data: pd.DataFrame, filename: str):
    """Export dataframe to CSV"""
    csv = data.to_csv(index=False)
    return csv


@st.cache_data(ttl=60)
def get_success_rate_by_company():
    """Get success rate by company"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute("""
            SELECT 
                j.company,
                COUNT(a.application_id) as total_applications,
                SUM(CASE WHEN a.status = 'submitted' THEN 1 ELSE 0 END) as successful,
                ROUND(SUM(CASE WHEN a.status = 'submitted' THEN 1.0 ELSE 0 END) / COUNT(a.application_id) * 100, 2) as success_rate
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.job_id
            WHERE j.company IS NOT NULL
            GROUP BY j.company
            HAVING COUNT(a.application_id) >= 3
            ORDER BY success_rate DESC
            LIMIT 20
        """).fetchall()
        
        df = pd.DataFrame(result, columns=['company', 'total_applications', 'successful', 'success_rate'])
    
    return df


@st.cache_data(ttl=300)
def get_unique_companies():
    """Get list of unique companies"""
    db = get_db_manager()
    
    with db.get_connection() as conn:
        result = conn.execute("""
            SELECT DISTINCT company 
            FROM jobs 
            WHERE company IS NOT NULL 
            ORDER BY company
        """).fetchall()
    
    return [r[0] for r in result]
