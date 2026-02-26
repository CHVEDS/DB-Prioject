"""Style configuration for banking analysis platform."""

# Color scheme for corporate design
COLOR_SCHEME = {
    'primary_blue': '#0052A3',      # Main blue
    'light_blue': '#0078D7',        # Light blue
    'pale_blue': '#E6F2FF',         # Pale blue (background)
    'white': '#FFFFFF',             # White
    'dark_blue': '#003366',         # Dark blue (text)
    'accent_blue': '#0099FF',       # Accent blue
    'success_green': '#28A745',     # Success
    'warning_orange': '#FFA500',    # Warning
    'danger_red': '#DC3545'         # Error/risk
}

# CSS styling for Streamlit
CSS_STYLES = """
<style>
    /* Main background */
    .main {
        background-color: #FFFFFF;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #003366;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #0052A3;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #003366;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #E6F2FF 0%, #FFFFFF 100%);
        border-left: 4px solid #0052A3;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E6F2FF;
    }
    
    /* Statuses */
    .status-excellent { color: #28A745; font-weight: bold; }
    .status-good { color: #5CB85C; font-weight: bold; }
    .status-warning { color: #FFA500; font-weight: bold; }
    .status-critical { color: #DC3545; font-weight: bold; }
    
    /* Tables */
    .dataframe {
        border: 1px solid #E6F2FF;
        border-radius: 8px;
    }
    th {
        background-color: #0052A3 !important;
        color: white !important;
    }
</style>
"""

# Application title
APP_TITLE = "🏦 Аналитический центр банковской устойчивости"
APP_SUBTITLE = "Автоматизированный анализ годовых отчётов кредитных организаций"