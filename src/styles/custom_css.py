"""
Custom CSS styles for DeFi Yield Guard Bot Dashboard

Modern fintech-inspired styling with dark theme, glassmorphism effects,
and professional UI components.
"""

from .color_palette import FintechColorPalette as colors


def get_custom_css() -> str:
    """Generate complete custom CSS for the dashboard."""
    return f"""
    <!-- Ionicons -->
    <script type="module" src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js"></script>
    <script nomodule src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.js"></script>

    <style>
    /* Import Google Fonts - Spark Style */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* CSS Variables */
    {colors.get_css_variables()}

    /* Global Styles */
    * {{
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}

    /* Main Container - Spark Style with Gradient Mesh */
    .main {{
        background-color: {colors.BG_PRIMARY};
        background-image:
            {colors.GRADIENT_MESH_1},
            {colors.GRADIENT_MESH_2},
            {colors.GRADIENT_MESH_3};
        background-attachment: fixed;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {colors.BG_SECONDARY} 0%, {colors.BG_PRIMARY} 100%);
        border-right: 1px solid {colors.BORDER_PRIMARY};
    }}

    [data-testid="stSidebar"] .css-1d391kg {{
        padding-top: 2rem;
    }}

    /* Headers - Spark Style Bold Typography */
    h1, h2, h3, h4, h5, h6 {{
        color: {colors.TEXT_PRIMARY} !important;
        font-weight: 700;
        letter-spacing: -0.03em;
        text-transform: uppercase;
    }}

    h1 {{
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, {colors.GRADIENT_PURPLE} 0%, {colors.GRADIENT_TEAL} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.04em;
    }}

    h2 {{
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        color: {colors.TEXT_PRIMARY} !important;
        letter-spacing: -0.03em;
    }}

    h3 {{
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: {colors.TEXT_PRIMARY} !important;
        letter-spacing: -0.02em;
        text-transform: uppercase;
    }}

    /* Paragraphs and Text */
    p, .css-10trblm, .css-16idsys {{
        color: {colors.TEXT_SECONDARY} !important;
        font-size: 1rem;
        line-height: 1.6;
    }}

    /* Metric Cards */
    [data-testid="stMetric"] {{
        background: linear-gradient(135deg, {colors.BG_SECONDARY} 0%, {colors.BG_TERTIARY} 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid {colors.BORDER_PRIMARY};
        box-shadow: 0 8px 32px {colors.SHADOW_MD};
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    }}

    [data-testid="stMetric"]:hover {{
        transform: translateY(-4px);
        border-color: {colors.BORDER_ACCENT};
        box-shadow: 0 12px 48px {colors.SHADOW_LG}, 0 0 24px {colors.GLOW_BLUE};
    }}

    [data-testid="stMetric"] label {{
        color: {colors.TEXT_TERTIARY} !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {colors.TEXT_PRIMARY} !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace;
    }}

    [data-testid="stMetric"] [data-testid="stMetricDelta"] {{
        font-size: 1rem !important;
        font-weight: 600 !important;
    }}

    /* Positive Delta */
    [data-testid="stMetric"] [data-testid="stMetricDelta"] svg[fill="rgb(9, 171, 59)"],
    [data-testid="stMetric"] [data-testid="stMetricDelta"][style*="rgb(9, 171, 59)"] {{
        color: {colors.ACCENT_GREEN} !important;
    }}

    /* Negative Delta */
    [data-testid="stMetric"] [data-testid="stMetricDelta"] svg[fill="rgb(255, 43, 43)"],
    [data-testid="stMetric"] [data-testid="stMetricDelta"][style*="rgb(255, 43, 43)"] {{
        color: {colors.ACCENT_CORAL} !important;
    }}

    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {colors.PRIMARY_BLUE} 0%, {colors.PRIMARY_BLUE_DARK} 100%);
        color: {colors.TEXT_PRIMARY};
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.02em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(0, 212, 255, 0.3);
        position: relative;
        overflow: hidden;
    }}

    .stButton > button:before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 212, 255, 0.5);
    }}

    .stButton > button:hover:before {{
        left: 100%;
    }}

    .stButton > button:active {{
        transform: translateY(0);
    }}

    /* Primary Button */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {colors.PRIMARY_BLUE} 0%, {colors.ACCENT_PURPLE} 100%);
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
    }}

    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.6);
    }}

    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {{
        background-color: {colors.BG_TERTIARY} !important;
        border: 1px solid {colors.BORDER_PRIMARY} !important;
        border-radius: 12px !important;
        color: {colors.TEXT_PRIMARY} !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease;
    }}

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {colors.PRIMARY_BLUE} !important;
        box-shadow: 0 0 0 3px {colors.GLOW_BLUE} !important;
        outline: none !important;
    }}

    /* Selectbox Styling - Fixed for proper visibility */
    .stSelectbox > div > div {{
        background-color: {colors.BG_TERTIARY} !important;
        border: 1px solid {colors.BORDER_PRIMARY} !important;
        border-radius: 12px !important;
        color: {colors.TEXT_PRIMARY} !important;
    }}

    .stSelectbox > div > div > div {{
        background-color: {colors.BG_TERTIARY} !important;
        color: {colors.TEXT_PRIMARY} !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        min-height: 3rem !important;
    }}

    .stSelectbox [data-baseweb="select"] {{
        background-color: {colors.BG_TERTIARY} !important;
    }}

    .stSelectbox [data-baseweb="select"] > div {{
        background-color: {colors.BG_TERTIARY} !important;
        border-color: {colors.BORDER_PRIMARY} !important;
        color: {colors.TEXT_PRIMARY} !important;
        min-height: 3rem !important;
    }}

    .stSelectbox [data-baseweb="select"]:hover > div {{
        border-color: {colors.PRIMARY_BLUE} !important;
    }}

    .stSelectbox [data-baseweb="select"]:focus-within > div {{
        border-color: {colors.PRIMARY_BLUE} !important;
        box-shadow: 0 0 0 3px {colors.GLOW_BLUE} !important;
    }}

    /* Dropdown menu styling */
    [data-baseweb="popover"] {{
        background-color: {colors.BG_TERTIARY} !important;
        border: 1px solid {colors.BORDER_ACCENT} !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px {colors.SHADOW_LG} !important;
    }}

    [data-baseweb="menu"] {{
        background-color: {colors.BG_TERTIARY} !important;
        border-radius: 12px !important;
    }}

    [role="option"] {{
        background-color: {colors.BG_TERTIARY} !important;
        color: {colors.TEXT_PRIMARY} !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        min-height: 3rem !important;
    }}

    [role="option"]:hover {{
        background-color: {colors.BG_ELEVATED} !important;
        color: {colors.PRIMARY_BLUE} !important;
    }}

    [aria-selected="true"] {{
        background-color: {colors.BG_ELEVATED} !important;
        color: {colors.PRIMARY_BLUE} !important;
        font-weight: 600 !important;
    }}

    /* Labels */
    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stSlider > label {{
        color: {colors.TEXT_SECONDARY} !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
    }}

    /* Sliders */
    .stSlider > div > div > div > div {{
        background-color: {colors.PRIMARY_BLUE} !important;
    }}

    .stSlider > div > div > div {{
        background-color: {colors.BG_TERTIARY} !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
        background-color: transparent;
        border-bottom: 2px solid {colors.BORDER_PRIMARY};
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        border-radius: 0;
        color: {colors.TEXT_TERTIARY};
        font-weight: 600;
        font-size: 1rem;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background-color: transparent;
        color: {colors.TEXT_SECONDARY};
        border-bottom: 3px solid {colors.TEXT_TERTIARY};
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: transparent;
        color: {colors.PRIMARY_BLUE};
        border-bottom: 3px solid {colors.PRIMARY_BLUE};
        font-weight: 700;
    }}

    /* DataFrames / Tables */
    .stDataFrame {{
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid {colors.BORDER_PRIMARY};
        box-shadow: 0 4px 16px {colors.SHADOW_SM};
    }}

    /* DataFrame Container */
    [data-testid="stDataFrame"] {{
        background-color: {colors.BG_SECONDARY};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* DataFrame Headers */
    [data-testid="stDataFrame"] thead tr th,
    .stDataFrame thead tr th,
    div[data-testid="stDataFrame"] table thead th {{
        background: linear-gradient(135deg, {colors.BG_TERTIARY} 0%, {colors.BG_SECONDARY} 100%) !important;
        color: {colors.TEXT_PRIMARY} !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        padding: 1rem !important;
        border-bottom: 2px solid {colors.BORDER_ACCENT} !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }}

    /* DataFrame Body Rows */
    [data-testid="stDataFrame"] tbody tr,
    .stDataFrame tbody tr,
    div[data-testid="stDataFrame"] table tbody tr {{
        background-color: {colors.BG_SECONDARY} !important;
        transition: all 0.2s ease;
    }}

    [data-testid="stDataFrame"] tbody tr:hover,
    .stDataFrame tbody tr:hover,
    div[data-testid="stDataFrame"] table tbody tr:hover {{
        background-color: {colors.BG_TERTIARY} !important;
    }}

    /* DataFrame Cells */
    [data-testid="stDataFrame"] tbody tr td,
    .stDataFrame tbody tr td,
    div[data-testid="stDataFrame"] table tbody td {{
        color: {colors.TEXT_SECONDARY} !important;
        padding: 0.875rem 1rem !important;
        border-bottom: 1px solid {colors.BORDER_PRIMARY} !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.875rem !important;
    }}

    /* Make numeric columns stand out */
    [data-testid="stDataFrame"] tbody tr td:nth-child(2),
    [data-testid="stDataFrame"] tbody tr td:nth-child(3),
    [data-testid="stDataFrame"] tbody tr td:nth-child(4),
    [data-testid="stDataFrame"] tbody tr td:nth-child(5),
    [data-testid="stDataFrame"] tbody tr td:nth-child(6) {{
        font-weight: 600 !important;
        color: {colors.TEXT_PRIMARY} !important;
    }}

    /* Progress Bar */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {colors.PRIMARY_BLUE} 0%, {colors.ACCENT_PURPLE} 100%);
        border-radius: 8px;
    }}

    .stProgress > div > div > div {{
        background-color: {colors.BG_TERTIARY};
        border-radius: 8px;
        height: 12px;
    }}

    /* Info/Success/Warning/Error Messages */
    .stAlert {{
        background-color: {colors.BG_SECONDARY};
        border-radius: 12px;
        border-left: 4px solid;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 16px {colors.SHADOW_SM};
    }}

    [data-testid="stAlert"] {{
        background-color: {colors.BG_SECONDARY};
    }}

    .stSuccess {{
        border-left-color: {colors.SUCCESS} !important;
        background: linear-gradient(90deg, rgba(81, 207, 102, 0.1) 0%, {colors.BG_SECONDARY} 100%) !important;
    }}

    .stInfo {{
        border-left-color: {colors.INFO} !important;
        background: linear-gradient(90deg, rgba(0, 212, 255, 0.1) 0%, {colors.BG_SECONDARY} 100%) !important;
    }}

    .stWarning {{
        border-left-color: {colors.WARNING} !important;
        background: linear-gradient(90deg, rgba(255, 146, 43, 0.1) 0%, {colors.BG_SECONDARY} 100%) !important;
    }}

    .stError {{
        border-left-color: {colors.ERROR} !important;
        background: linear-gradient(90deg, rgba(255, 107, 107, 0.1) 0%, {colors.BG_SECONDARY} 100%) !important;
    }}

    /* Divider */
    hr {{
        border: none;
        border-top: 1px solid {colors.DIVIDER};
        margin: 2rem 0;
        opacity: 0.6;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {colors.BG_SECONDARY};
        border-radius: 12px;
        border: 1px solid {colors.BORDER_PRIMARY};
        color: {colors.TEXT_PRIMARY} !important;
        font-weight: 600;
        padding: 1rem;
        transition: all 0.3s ease;
    }}

    .streamlit-expanderHeader:hover {{
        background-color: {colors.BG_TERTIARY};
        border-color: {colors.BORDER_ACCENT};
    }}

    /* Scrollbar Styling */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}

    ::-webkit-scrollbar-track {{
        background: {colors.BG_PRIMARY};
    }}

    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, {colors.BORDER_ACCENT} 0%, {colors.PRIMARY_BLUE} 100%);
        border-radius: 5px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(135deg, {colors.PRIMARY_BLUE} 0%, {colors.ACCENT_PURPLE} 100%);
    }}

    /* Custom Classes for Special Components */
    .metric-card {{
        background: linear-gradient(135deg, {colors.BG_SECONDARY} 0%, {colors.BG_TERTIARY} 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid {colors.BORDER_PRIMARY};
        box-shadow: 0 8px 32px {colors.SHADOW_MD};
        transition: all 0.3s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 48px {colors.SHADOW_LG}, 0 0 32px {colors.GLOW_BLUE};
        border-color: {colors.PRIMARY_BLUE};
    }}

    .glass-card {{
        background: rgba(21, 26, 48, 0.6);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid {colors.BORDER_PRIMARY};
        padding: 2rem;
        box-shadow: 0 8px 32px {colors.SHADOW_MD};
    }}

    .gradient-text {{
        background: linear-gradient(135deg, {colors.PRIMARY_BLUE} 0%, {colors.ACCENT_PURPLE} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }}

    .stat-positive {{
        color: {colors.ACCENT_GREEN} !important;
        font-weight: 600;
    }}

    .stat-negative {{
        color: {colors.ACCENT_CORAL} !important;
        font-weight: 600;
    }}

    /* Bento Grid Layout - Spark Style */
    .bento-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }}

    .bento-item {{
        background: {colors.BG_SECONDARY};
        border-radius: 12px;
        border: 1px solid {colors.BORDER_PRIMARY};
        padding: 2.5rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}

    .bento-item:before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: {colors.GRADIENT_CARD_PURPLE};
        opacity: 0;
        transition: opacity 0.4s ease;
    }}

    .bento-item:hover:before {{
        opacity: 1;
    }}

    .bento-item:hover {{
        transform: translateY(-2px);
        border-color: {colors.GRADIENT_PURPLE};
        box-shadow: 0 20px 60px {colors.SHADOW_LG}, 0 0 40px {colors.GLOW_PURPLE};
    }}

    .bento-large {{
        grid-column: span 2;
        grid-row: span 2;
    }}

    .bento-wide {{
        grid-column: span 2;
    }}

    .bento-tall {{
        grid-row: span 2;
    }}

    /* Footer */
    footer {{
        color: {colors.TEXT_TERTIARY};
        text-align: center;
        padding: 2rem 0;
        border-top: 1px solid {colors.DIVIDER};
        margin-top: 4rem;
    }}

    /* Hide Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Animation Keyframes */
    @keyframes gradient-shift {{
        0% {{
            background-position: 0% 50%;
        }}
        50% {{
            background-position: 100% 50%;
        }}
        100% {{
            background-position: 0% 50%;
        }}
    }}

    .animated-gradient {{
        background-size: 200% 200%;
        animation: gradient-shift 8s ease infinite;
    }}
    </style>
    """
