"""
Job Application Bot Dashboard - Main Application
"""
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
from config import *
from utils.styles import apply_custom_css
from utils.db_helper import get_db_manager, get_dashboard_stats

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE
)

# Apply custom styling
apply_custom_css()

# Initialize database
@st.cache_resource
def init_database():
    """Initialize database with schema"""
    db = get_db_manager()
    db.initialize_schema()
    db.add_application_tables()
    db.create_indexes()
    return db

db = init_database()

# Sidebar
with st.sidebar:
    st.markdown(f"# {PAGE_ICON} Job Bot")
    st.markdown("### Dashboard")
    st.markdown("---")
    
    # Navigation menu
    selected = option_menu(
        menu_title=None,
        options=["Overview", "Applications", "Job Discovery", "Analytics", 
                "Bot Performance", "Company Intel", "Q&A Repository", "Error Logs"],
        icons=["speedometer2", "file-earmark-check", "search", "graph-up", 
               "gear", "building", "question-circle", "exclamation-triangle"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": COLORS['primary'], "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "padding": "10px",
                "border-radius": "10px"
            },
            "nav-link-selected": {"background-color": COLORS['primary']},
        }
    )
    
    st.markdown("---")
    
    # Quick stats in sidebar
    try:
        stats = get_dashboard_stats()
        st.metric("Total Applications", stats['total_applications'])
        st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
        st.metric("Jobs Available", stats['jobs_not_applied'])
    except:
        st.info("Loading statistics...")
    
    st.markdown("---")
    
    # Settings
    with st.expander("⚙️ Settings"):
        st.checkbox("Auto-refresh", value=False, key="auto_refresh")
        st.slider("Refresh interval (sec)", 30, 600, AUTO_REFRESH_INTERVAL, key="refresh_interval")
        theme = st.selectbox("Theme", ["Light", "Dark"], key="theme")
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Main content area
st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title(f"{PAGE_ICON} Job Application Bot Dashboard")
    st.markdown(f"**Welcome!** Track and manage your automated job applications.")
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Route to selected page
if selected == "Overview":
    st.switch_page("pages/Overview.py")
elif selected == "Applications":
    st.switch_page("pages/Applications.py")
elif selected == "Job Discovery":
    st.switch_page("pages/Job_Discovery.py")
elif selected == "Analytics":
    st.switch_page("pages/Analytics.py")
elif selected == "Bot Performance":
    st.switch_page("pages/Bot_Performance.py")
elif selected == "Company Intel":
    st.switch_page("pages/Company_Intelligence.py")
elif selected == "Q&A Repository":
    st.switch_page("pages/QA_Repository.py")
elif selected == "Error Logs":
    st.switch_page("pages/Error_Logs.py")

st.markdown('</div>', unsafe_allow_html=True)
