"""
Configuration settings for the Job Application Dashboard
"""
from pathlib import Path

# Database configuration
DB_PATH = DB_PATH = Path(__file__).parent.parent / "database" / "jobs.duckdb"


# Dashboard settings
PAGE_TITLE = "Job Application Bot Dashboard"
PAGE_ICON = "🤖"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# Color scheme - Modern gradient theme
COLORS = {
    "primary": "#6366f1",      # Indigo
    "secondary": "#8b5cf6",    # Purple
    "success": "#10b981",      # Green
    "warning": "#f59e0b",      # Amber
    "danger": "#ef4444",       # Red
    "info": "#3b82f6",         # Blue
    "dark": "#1e293b",         # Slate
    "light": "#5e7388",        # Light slate
    "accent": "#ec4899",       # Pink
}

# Status colors
STATUS_COLORS = {
    "submitted": COLORS["success"],
    "failed": COLORS["danger"],
    "pending": COLORS["warning"],
    "in_progress": COLORS["info"],
    "active": COLORS["primary"],
    "completed": COLORS["success"],
}

# Chart settings
CHART_THEME = "plotly"  # Changed from "plotly_dark" to "plotly"
CHART_HEIGHT = 400

# Pagination
ITEMS_PER_PAGE = 50
PAGE_SIZE_OPTIONS = [25, 50, 100, 250, 500]

# Date format
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_SHORT = "%Y-%m-%d"

# Auto-refresh interval (seconds)
AUTO_REFRESH_INTERVAL = 300  # 5 minutes

# Application status options
APPLICATION_STATUSES = ["submitted", "failed", "pending", "in_progress"]

# Job statuses
JOB_STATUSES = ["active", "inactive", "expired", "filled"]
