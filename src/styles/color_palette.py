"""
Spark-Inspired Color Palette for DeFi Yield Guard Bot Dashboard

Color scheme matching the Spark Protocol bento grid aesthetic with
gradient meshes, dark backgrounds, and bold typography.
"""

class FintechColorPalette:
    """Spark-inspired fintech color palette with dark theme and gradients."""

    # Primary Brand Colors - Spark Gradients
    GRADIENT_PURPLE = "#6B5FED"     
    GRADIENT_BLUE = "#4F7BF5"       
    GRADIENT_TEAL = "#3DBAA5"       
    GRADIENT_ORANGE = "#E89B5F"     
    GRADIENT_GOLD = "#D4A574"       

    # New attributes your app uses
    PRIMARY_BLUE = "#4F7BF5"
    PRIMARY_BLUE_DARK = "#3B5DBF"
    ACCENT_CORAL = "#FF6F61"
    GLOW_BLUE = "0 0 15px rgba(79, 123, 245, 0.5)"

    # Accent Colors
    ACCENT_PURPLE = "#8B7BED"       
    ACCENT_TEAL = "#5DD4C1"         
    ACCENT_ORANGE = "#F5B97F"       
    ACCENT_GREEN = "#51CF66"        
    ACCENT_RED = "#FF6B6B"          

    # Background Colors
    BG_PRIMARY = "#0F1419"          
    BG_SECONDARY = "#1A1F26"        
    BG_TERTIARY = "#242930"         
    BG_ELEVATED = "#2D333A"         

    # Text Colors
    TEXT_PRIMARY = "#FFFFFF"        
    TEXT_SECONDARY = "#B8BCC4"      
    TEXT_TERTIARY = "#7B8088"       
    TEXT_DISABLED = "#4A4D52"       

    # Border & Divider Colors
    BORDER_PRIMARY = "#2A2F36"      
    BORDER_ACCENT = "#3A4048"       
    DIVIDER = "#242930"             

    # Chart Colors
    CHART_PRIMARY = "#6B5FED"       
    CHART_SECONDARY = "#3DBAA5"     
    CHART_TERTIARY = "#E89B5F"      
    CHART_QUATERNARY = "#4F7BF5"    
    CHART_QUINARY = "#D4A574"       

    # Gradient Mesh Definitions
    GRADIENT_MESH_1 = "radial-gradient(circle at 20% 20%, rgba(107, 95, 237, 0.3) 0%, transparent 50%)"
    GRADIENT_MESH_2 = "radial-gradient(circle at 80% 80%, rgba(61, 186, 165, 0.3) 0%, transparent 50%)"
    GRADIENT_MESH_3 = "radial-gradient(circle at 50% 50%, rgba(232, 155, 95, 0.2) 0%, transparent 60%)"

    # Card Gradients
    GRADIENT_CARD_PURPLE = "linear-gradient(135deg, rgba(107, 95, 237, 0.15) 0%, rgba(79, 123, 245, 0.1) 100%)"
    GRADIENT_CARD_TEAL = "linear-gradient(135deg, rgba(61, 186, 165, 0.15) 0%, rgba(93, 212, 193, 0.1) 100%)"
    GRADIENT_CARD_ORANGE = "linear-gradient(135deg, rgba(232, 155, 95, 0.15) 0%, rgba(212, 165, 116, 0.1) 100%)"
    GRADIENT_CARD_DARK = "linear-gradient(135deg, #1A1F26 0%, #242930 100%)"

    # Semantic Colors
    SUCCESS = "#51CF66"
    WARNING = "#F5B97F"
    ERROR = "#FF6B6B"
    INFO = "#4F7BF5"

    # Shadow Colors
    SHADOW_SM = "rgba(0, 0, 0, 0.3)"
    SHADOW_MD = "rgba(0, 0, 0, 0.4)"
    SHADOW_LG = "rgba(0, 0, 0, 0.6)"
    GLOW_PURPLE = "rgba(107, 95, 237, 0.4)"
    GLOW_TEAL = "rgba(61, 186, 165, 0.4)"
    GLOW_ORANGE = "rgba(232, 155, 95, 0.4)"

    @classmethod
    def get_css_variables(cls) -> str:
        """Generate CSS variables string for Streamlit."""
        return f"""
        :root {{
            --primary-blue: {cls.PRIMARY_BLUE};
            --primary-blue-dark: {cls.PRIMARY_BLUE_DARK};
            --accent-coral: {cls.ACCENT_CORAL};
            --accent-green: {cls.ACCENT_GREEN};
            --accent-purple: {cls.ACCENT_PURPLE};
            --accent-orange: {cls.ACCENT_ORANGE};
            --bg-primary: {cls.BG_PRIMARY};
            --bg-secondary: {cls.BG_SECONDARY};
            --bg-tertiary: {cls.BG_TERTIARY};
            --bg-elevated: {cls.BG_ELEVATED};
            --text-primary: {cls.TEXT_PRIMARY};
            --text-secondary: {cls.TEXT_SECONDARY};
            --text-tertiary: {cls.TEXT_TERTIARY};
            --text-disabled: {cls.TEXT_DISABLED};
            --border-primary: {cls.BORDER_PRIMARY};
            --border-accent: {cls.BORDER_ACCENT};
            --divider: {cls.DIVIDER};
            --success: {cls.SUCCESS};
            --warning: {cls.WARNING};
            --error: {cls.ERROR};
            --info: {cls.INFO};
        }}
        """

    @classmethod
    def get_plotly_template(cls) -> dict:
        return {
            'layout': {
                'paper_bgcolor': cls.BG_SECONDARY,
                'plot_bgcolor': cls.BG_PRIMARY,
                'font': {
                    'color': cls.TEXT_SECONDARY,
                    'family': 'Inter, sans-serif'
                },
                'colorway': [
                    cls.CHART_PRIMARY,
                    cls.CHART_SECONDARY,
                    cls.CHART_TERTIARY,
                    cls.CHART_QUATERNARY,
                    cls.CHART_QUINARY
                ],
                'xaxis': {
                    'gridcolor': cls.BORDER_PRIMARY,
                    'linecolor': cls.BORDER_ACCENT,
                    'zerolinecolor': cls.BORDER_ACCENT,
                },
                'yaxis': {
                    'gridcolor': cls.BORDER_PRIMARY,
                    'linecolor': cls.BORDER_ACCENT,
                    'zerolinecolor': cls.BORDER_ACCENT,
                }
            }
        }