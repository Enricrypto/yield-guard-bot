"""Quick test to verify HTML rendering in Streamlit"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.styles.color_palette import FintechColorPalette as colors
from src.styles.custom_css import get_custom_css

st.set_page_config(page_title="Render Test", layout="wide")

# Apply CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Test 1: Simple HTML
st.markdown("## Test 1: Simple HTML")
st.markdown(
    """
    <div style="background: #1A1F26; padding: 2rem; border-radius: 12px; color: white;">
        <h3>This should be styled</h3>
        <p>If you can read this in a dark card, HTML rendering works!</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Test 2: With CSS Classes
st.markdown("## Test 2: With Bento Grid Classes")
st.markdown(
    f"""
    <div class="bento-item" style="padding: 2rem;">
        <h3 style="color: {colors.GRADIENT_PURPLE};">Bento Card Test</h3>
        <p style="color: {colors.TEXT_SECONDARY};">This uses the bento-item class</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Test 3: Iconify
st.markdown("## Test 3: Iconify Icons")
st.markdown(
    """
    <script src="https://code.iconify.design/3/3.1.0/iconify.min.js"></script>
    <div style="font-size: 3rem;">
        <span class="iconify" data-icon="mdi:shield-check"></span>
        <span class="iconify" data-icon="mdi:lightning-bolt"></span>
        <span class="iconify" data-icon="mdi:trending-up"></span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")
st.markdown("If all three tests display correctly, your setup is working!")
