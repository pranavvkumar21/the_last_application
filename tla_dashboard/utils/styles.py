"""
Custom CSS styling for the dashboard
"""
import streamlit as st
from config import COLORS

def apply_custom_css():
    """Apply custom CSS styling to the dashboard"""
    st.markdown(f"""
    <style>
        /* Import modern font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global font */
        * {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* THIS IS THE KEY - Target the actual Streamlit app container */
        .stApp {{
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%) !important;
        }}
        
        /* Main content area */
        .main .block-container {{
            background: transparent !important;
            padding-top: 3rem !important;
            max-width: 100% !important;
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {COLORS['dark']} 0%, #0f172a 100%) !important;
        }}
        
        section[data-testid="stSidebar"] > div {{
            background: transparent !important;
        }}
        
        /* Sidebar text color */
        section[data-testid="stSidebar"] * {{
            color: #e2e8f0 !important;
        }}
        
        /* Make all container divs transparent */
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"] {{
            background: transparent !important;
        }}
        
        /* White cards for metrics */
        [data-testid="stMetric"] {{
            background: white !important;
            padding: 1.5rem !important;
            border-radius: 15px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
            border: 1px solid rgba(99, 102, 241, 0.1) !important;
        }}
        
        /* Metric values with gradient */
        [data-testid="stMetricValue"] {{
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            color: #64748b !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        
        [data-testid="stMetricDelta"] {{
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
        }}
        
        /* Text inputs */
        .stTextInput > div > div > input,
        .stTextArea textarea {{
            background: white !important;
            border-radius: 10px !important;
            border: 2px solid #e2e8f0 !important;
            padding: 0.75rem !important;
            transition: all 0.3s ease !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea textarea:focus {{
            border-color: {COLORS['primary']} !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
        }}
        
        /* Select boxes */
        .stSelectbox > div > div {{
            background: white !important;
            border-radius: 10px !important;
            border: 2px solid #e2e8f0 !important;
        }}
        
        /* Plotly charts */
        .stPlotlyChart {{
            background: white !important;
            border-radius: 15px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
            overflow: hidden !important;
            margin-bottom: 1rem !important;
        }}

        /* Inner plot container */
        .js-plotly-plot {{
            background: white !important;
            border-radius: 15px !important;
            overflow: hidden !important;
            width: 100% !important;
        }}

        /* The actual plot/SVG area */
        .plot-container {{
            overflow: hidden !important;
            position: relative !important;
        }}

        /* SVG elements */
        .plotly,
        .svg-container {{
            overflow: hidden !important;
            width: 100% !important;
            max-width: 100% !important;
        }}

        .plotly svg {{
            overflow: hidden !important;
            max-width: 100% !important;
            height: auto !important;
        }}

        /* Main SVG canvas */
        .main-svg {{
            overflow: hidden !important;
        }}

        /* Modebar (chart toolbar) */
        .modebar {{
            position: absolute !important;
            top: 5px !important;
            right: 5px !important;
            z-index: 100 !important;
        }}

        .modebar-btn {{
            background: rgba(255,255,255,0.8) !important;
            border-radius: 5px !important;
        }}

        .modebar-btn:hover {{
            background: rgba(99, 102, 241, 0.1) !important;
        }}

        /* Responsive behavior */
        @media (max-width: 768px) {{
            .js-plotly-plot {{
                max-width: 100vw !important;
            }}
        }}
        
        /* Tables */
        .stDataFrame,
        .dataframe {{
            background: white !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }}
        
        .dataframe thead tr th {{
            background: {COLORS['primary']} !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 1rem !important;
        }}
        
        /* Expanders */
        .streamlit-expanderHeader {{
            background: white !important;
            border-radius: 10px !important;
            border: 2px solid #e2e8f0 !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}
        
        .streamlit-expanderHeader:hover {{
            border-color: {COLORS['primary']} !important;
            background: #f8fafc !important;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px !important;
            background: transparent !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: white !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            border: 2px solid #e2e8f0 !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%) !important;
            color: white !important;
            border-color: transparent !important;
        }}
        
        /* Status badges */
        .status-badge {{
            display: inline-block !important;
            padding: 0.4rem 0.9rem !important;
            border-radius: 20px !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        
        .status-submitted {{
            background: {COLORS['success']} !important;
            color: white !important;
        }}
        
        .status-failed {{
            background: {COLORS['danger']} !important;
            color: white !important;
        }}
        
        .status-pending {{
            background: {COLORS['warning']} !important;
            color: white !important;
        }}
        
        /* Custom cards */
        .custom-card {{
            background: white !important;
            padding: 1.5rem !important;
            border-radius: 15px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
            border: 1px solid rgba(99, 102, 241, 0.1) !important;
            transition: all 0.3s ease !important;
        }}
        
        .custom-card:hover {{
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15) !important;
            border-color: {COLORS['primary']} !important;
        }}
        
        /* Messages */
        .stSuccess {{
            background: rgba(16, 185, 129, 0.1) !important;
            border-left: 4px solid {COLORS['success']} !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }}
        
        .stError {{
            background: rgba(239, 68, 68, 0.1) !important;
            border-left: 4px solid {COLORS['danger']} !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }}
        
        .stInfo {{
            background: rgba(59, 130, 246, 0.1) !important;
            border-left: 4px solid {COLORS['info']} !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }}
        
        .stWarning {{
            background: rgba(245, 158, 11, 0.1) !important;
            border-left: 4px solid {COLORS['warning']} !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f5f9;
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['primary']};
        }}
        
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden !important;}}
        footer {{visibility: hidden !important;}}
        header {{visibility: hidden !important;}}
        
        /* Headers */
        h1, h2, h3 {{
            color: {COLORS['dark']} !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def create_metric_card(label, value, delta=None, delta_color="normal"):
    """Create a custom metric card with styling"""
    delta_html = ""
    if delta is not None:
        delta_class = "metric-delta-positive" if delta_color == "normal" else "metric-delta-negative"
        delta_symbol = "↑" if delta >= 0 else "↓"
        delta_html = f'<div class="{delta_class}">{delta_symbol} {abs(delta)}</div>'
    
    return f"""
    <div class="metric-card animate-fade-in">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """


def create_status_badge(status):
    """Create a colored status badge"""
    status_lower = status.lower().replace(" ", "_")
    return f'<span class="status-badge status-{status_lower}">{status}</span>'


def create_custom_card(content, title=None):
    """Create a custom styled card"""
    title_html = f"<h3>{title}</h3>" if title else ""
    return f"""
    <div class="custom-card animate-fade-in">
        {title_html}
        <div>{content}</div>
    </div>
    """
