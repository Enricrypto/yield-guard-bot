"""
Enhanced Streamlit Dashboard for DeFi Yield Optimization Bot

Modern fintech-themed interface with bento grid layout, dark theme,
and professional UI components inspired by Taipy Studio.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from decimal import Decimal
from typing import Literal, cast
import sqlite3
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import Config
from simulator.treasury_simulator import TreasurySimulator
from market_data.synthetic_generator import SyntheticDataGenerator
from analytics.performance_metrics import PerformanceMetrics
from database.db import DatabaseManager, SimulationRun, PortfolioSnapshot
from styles.custom_css import get_custom_css
from styles.color_palette import FintechColorPalette as colors

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="DeFi Yield Guard Bot",
    page_icon="⬢",  # Hexagon shape - closest to a shield without emoji
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(get_custom_css(), unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Session & DB helpers
# ---------------------------------------------------------------------
def initialize_session_state():
    if "config" not in st.session_state:
        st.session_state.config = Config()
    if "last_simulation_id" not in st.session_state:
        st.session_state.last_simulation_id = None
    if "show_landing" not in st.session_state:
        st.session_state.show_landing = True


def get_db_connection():
    config = st.session_state.config
    db_path = Path(config.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(config.database_path)
    db = DatabaseManager(config.database_path)
    db.init_db()
    return conn

# ---------------------------------------------------------------------
# Simulation Tab
# ---------------------------------------------------------------------
def render_simulation_tab():
    st.markdown(
        f"""
        <h2 style="color:{colors.GRADIENT_PURPLE};">
            <span class="iconify" data-icon="mdi:play-circle" style="vertical-align:middle;"></span>
            Run Simulation
        </h2>
        <p style="color:{colors.TEXT_SECONDARY};">Configure and execute a yield optimization simulation</p>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            f"""
            <div class="bento-item" style="padding:1.5rem;">
                <h3 style="color:{colors.GRADIENT_BLUE};">
                    <span class="iconify" data-icon="mdi:cog" style="vertical-align:middle;"></span>
                    Simulation Parameters
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Input fields
        col_a, col_b = st.columns(2)
        with col_a:
            initial_capital = st.number_input(
                "Initial Capital (USDC)",
                min_value=1000.0,
                value=100000.0,
                step=1000.0,
                help="Starting capital for the simulation"
            )
            simulation_days = st.number_input(
                "Simulation Duration (days)",
                min_value=1,
                value=365,
                step=1,
                help="Number of days to simulate"
            )

        with col_b:
            risk_tolerance = st.selectbox(
                "Risk Tolerance",
                ["Conservative", "Moderate", "Aggressive"],
                index=1,
                help="Risk appetite for yield optimization"
            )
            rebalance_frequency = st.selectbox(
                "Rebalance Frequency",
                ["Daily", "Weekly", "Monthly"],
                index=1,
                help="How often to rebalance the portfolio"
            )

        st.markdown(
            f"""
            <div class="bento-item" style="margin-top:2rem;padding:1.5rem;">
                <h3 style="color:{colors.GRADIENT_TEAL};">
                    <span class="iconify" data-icon="mdi:bank" style="vertical-align:middle;"></span>
                    Protocol Selection
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            use_aave = st.checkbox("Aave", value=True)
        with col_p2:
            use_compound = st.checkbox("Compound", value=True)
        with col_p3:
            use_morpho = st.checkbox("Morpho", value=False)

        st.markdown("<br>", unsafe_allow_html=True)

        # Single functional button
        run_clicked = st.button(
            "RUN SIMULATION",
            key="run_sim_btn",
            use_container_width=True,
            type="primary"
        )

        if run_clicked:
            st.success("🚀 Simulation started! Processing yield optimization...")
            # Placeholder for actual simulation logic

    with col2:
        st.markdown(
            f"""
            <div class="bento-item" style="padding:1.5rem;">
                <h3 style="color:{colors.GRADIENT_ORANGE};">
                    <span class="iconify" data-icon="mdi:information" style="vertical-align:middle;"></span>
                    Quick Guide
                </h3>
                <div style="color:{colors.TEXT_SECONDARY};font-size:0.9rem;line-height:1.6;margin-top:1rem;">
                    <div style="margin-bottom:1rem;"><strong style="color:{colors.GRADIENT_PURPLE};">1. Set Parameters</strong><br>Choose your initial capital and simulation duration.</div>
                    <div style="margin-bottom:1rem;"><strong style="color:{colors.GRADIENT_TEAL};">2. Select Risk</strong><br>Pick a risk tolerance that matches your strategy.</div>
                    <div style="margin-bottom:1rem;"><strong style="color:{colors.GRADIENT_ORANGE};">3. Choose Protocols</strong><br>Enable DeFi protocols to include in optimization.</div>
                    <div><strong style="color:{colors.GRADIENT_BLUE};">4. Run</strong><br>Execute the simulation and analyze results.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ---------------------------------------------------------------------
# Dashboard Tab
# ---------------------------------------------------------------------
def render_dashboard_tab():
    st.markdown(
        f"""
        <h2 style="color:{colors.GRADIENT_TEAL};">
            <span class="iconify" data-icon="mdi:view-dashboard" style="vertical-align:middle;"></span>
            Portfolio Dashboard
        </h2>
        <p style="color:{colors.TEXT_SECONDARY};">Real-time metrics and performance analytics</p>
        """,
        unsafe_allow_html=True
    )

    # Fetch latest simulation data
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get latest simulation
        cur.execute("""
            SELECT
                initial_capital,
                final_value,
                total_return,
                sharpe_ratio,
                max_drawdown,
                total_gas_fees,
                num_rebalances,
                created_at
            FROM simulation_runs
            ORDER BY created_at DESC
            LIMIT 1
        """)
        latest = cur.fetchone()

        if latest:
            initial_cap = latest[0]
            final_val = latest[1]
            total_ret = latest[2] * 100
            sharpe = latest[3]
            drawdown = latest[4] * 100
            gas_fees = latest[5]
            rebalances = latest[6]
            pnl = final_val - initial_cap
            pnl_pct = (pnl / initial_cap) * 100
        else:
            # Default values if no simulation exists
            initial_cap = 100000
            final_val = 100000
            total_ret = 0
            sharpe = 0
            drawdown = 0
            gas_fees = 0
            rebalances = 0
            pnl = 0
            pnl_pct = 0

        conn.close()
    except Exception:
        initial_cap = 100000
        final_val = 100000
        total_ret = 0
        sharpe = 0
        drawdown = 0
        gas_fees = 0
        rebalances = 0
        pnl = 0
        pnl_pct = 0

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card_html = f"""
        <div class="bento-item" style="padding:1.5rem;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <span class="iconify" data-icon="mdi:wallet" style="vertical-align:middle;"></span>
                Portfolio Value
            </div>
            <div style="font-size:2rem;color:{colors.GRADIENT_PURPLE};font-family:JetBrains Mono,monospace;">
                ${final_val:,.2f}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;margin-top:0.5rem;">
                Initial: ${initial_cap:,.2f}
            </div>
        </div>
        """
        st.markdown(metric_card_html, unsafe_allow_html=True)

    with col2:
        pnl_color = colors.GRADIENT_TEAL if pnl >= 0 else colors.ACCENT_RED
        pnl_icon = "mdi:trending-up" if pnl >= 0 else "mdi:trending-down"
        metric_card_html = f"""
        <div class="bento-item" style="padding:1.5rem;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <span class="iconify" data-icon="{pnl_icon}" style="vertical-align:middle;"></span>
                P&L
            </div>
            <div style="font-size:2rem;color:{pnl_color};font-family:JetBrains Mono,monospace;">
                {'+' if pnl >= 0 else ''}{pnl_pct:.2f}%
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;margin-top:0.5rem;">
                ${pnl:+,.2f}
            </div>
        </div>
        """
        st.markdown(metric_card_html, unsafe_allow_html=True)

    with col3:
        metric_card_html = f"""
        <div class="bento-item" style="padding:1.5rem;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <span class="iconify" data-icon="mdi:chart-line-variant" style="vertical-align:middle;"></span>
                Sharpe Ratio
            </div>
            <div style="font-size:2rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;">
                {sharpe:.2f}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;margin-top:0.5rem;">
                Risk-adjusted return
            </div>
        </div>
        """
        st.markdown(metric_card_html, unsafe_allow_html=True)

    with col4:
        metric_card_html = f"""
        <div class="bento-item" style="padding:1.5rem;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <span class="iconify" data-icon="mdi:alert-circle" style="vertical-align:middle;"></span>
                Max Drawdown
            </div>
            <div style="font-size:2rem;color:{colors.GRADIENT_ORANGE};font-family:JetBrains Mono,monospace;">
                {drawdown:.2f}%
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;margin-top:0.5rem;">
                Peak to trough
            </div>
        </div>
        """
        st.markdown(metric_card_html, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Charts Row
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown(
            f"""
            <div class="bento-item" style="padding:1.5rem;margin-bottom:1rem;">
                <h3 style="color:{colors.GRADIENT_BLUE};">
                    <span class="iconify" data-icon="mdi:chart-areaspline" style="vertical-align:middle;"></span>
                    Portfolio Performance
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Sample chart data (replace with actual data)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        values = [initial_cap * (1 + i/1000) for i in range(100)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines',
            line=dict(color=colors.GRADIENT_PURPLE, width=3),
            fill='tozeroy',
            fillcolor=f'rgba(107, 95, 237, 0.1)',
            name='Portfolio Value'
        ))

        fig.update_layout(
            **colors.get_plotly_template()['layout'],
            height=280,
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=False,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(
            f"""
            <div class="bento-item">
                <h3 style="color:{colors.GRADIENT_ORANGE};">
                    <span class="iconify" data-icon="mdi:finance" style="vertical-align:middle;"></span>
                    Activity Stats
                </h3>
                <div style="margin-top:1.5rem;">
                    <div style="margin-bottom:1.5rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">Rebalances</div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_PURPLE};font-family:JetBrains Mono,monospace;margin-top:0.25rem;">
                            {rebalances}
                        </div>
                    </div>
                    <div style="margin-bottom:1.5rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">Gas Fees</div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;margin-top:0.25rem;">
                            ${gas_fees:.2f}
                        </div>
                    </div>
                    <div>
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">Efficiency</div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_ORANGE};font-family:JetBrains Mono,monospace;margin-top:0.25rem;">
                            {((pnl - gas_fees) / initial_cap * 100) if initial_cap > 0 else 0:.2f}%
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ---------------------------------------------------------------------
# History Tab
# ---------------------------------------------------------------------
def render_history_tab():
    st.markdown(
        f"""
        <h2 style="color:{colors.GRADIENT_BLUE};">
            <span class="iconify" data-icon="mdi:history" style="vertical-align:middle;"></span>
            Simulation History
        </h2>
        <p style="color:{colors.TEXT_SECONDARY};">Review past simulation runs and performance</p>
        """,
        unsafe_allow_html=True
    )

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                initial_capital,
                final_value,
                total_return,
                sharpe_ratio,
                max_drawdown,
                num_rebalances,
                created_at
            FROM simulation_runs
            ORDER BY created_at DESC
            LIMIT 50
        """)

        rows = cur.fetchall()
        conn.close()

        if rows:
            # Create DataFrame
            df = pd.DataFrame(rows, columns=[
                'ID', 'Initial Capital', 'Final Value', 'Total Return',
                'Sharpe Ratio', 'Max Drawdown', 'Rebalances', 'Date'
            ])

            # Format columns
            df['Initial Capital'] = df['Initial Capital'].apply(lambda x: f"${x:,.2f}")
            df['Final Value'] = df['Final Value'].apply(lambda x: f"${x:,.2f}")
            df['Total Return'] = df['Total Return'].apply(lambda x: f"{x*100:+.2f}%")
            df['Sharpe Ratio'] = df['Sharpe Ratio'].apply(lambda x: f"{x:.2f}")
            df['Max Drawdown'] = df['Max Drawdown'].apply(lambda x: f"{x*100:.2f}%")
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')

            st.markdown(
                f"""
                <div class="bento-item">
                    <h3 style="color:{colors.GRADIENT_PURPLE};">
                        <span class="iconify" data-icon="mdi:table" style="vertical-align:middle;"></span>
                        Recent Simulations ({len(rows)} runs)
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                hide_index=True
            )

            # Summary stats
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    f"""
                    <div class="bento-item" style="padding:1.5rem;margin-top:1rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">
                            <span class="iconify" data-icon="mdi:trophy" style="vertical-align:middle;"></span>
                            Best Return
                        </div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">
                            {max([r[3] for r in rows])*100:+.2f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    f"""
                    <div class="bento-item" style="padding:1.5rem;margin-top:1rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">
                            <span class="iconify" data-icon="mdi:chart-bar" style="vertical-align:middle;"></span>
                            Avg Sharpe
                        </div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_PURPLE};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">
                            {sum([r[4] for r in rows])/len(rows):.2f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col3:
                st.markdown(
                    f"""
                    <div class="bento-item" style="padding:1.5rem;margin-top:1rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">
                            <span class="iconify" data-icon="mdi:sigma" style="vertical-align:middle;"></span>
                            Total Runs
                        </div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_ORANGE};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">
                            {len(rows)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:
            st.markdown(
                f"""
                <div class="bento-item" style="text-align:center;padding:3rem;">
                    <span class="iconify" data-icon="mdi:information-outline" style="font-size:3rem;color:{colors.TEXT_TERTIARY};"></span>
                    <h3 style="color:{colors.TEXT_SECONDARY};margin-top:1rem;">No Simulation History</h3>
                    <p style="color:{colors.TEXT_TERTIARY};">Run your first simulation to see results here</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"Error loading history: {str(e)}")


# ---------------------------------------------------------------------
# About Tab
# ---------------------------------------------------------------------
def render_about_tab():
    st.markdown(
        f"""
        <h2 style="color:{colors.GRADIENT_PURPLE};">
            <span class="iconify" data-icon="mdi:information" style="vertical-align:middle;"></span>
            About DeFi Yield Guard Bot
        </h2>
        <p style="color:{colors.TEXT_SECONDARY};">Intelligent yield optimization with automated risk management</p>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            f"""
            <div class="bento-item">
                <h3 style="color:{colors.GRADIENT_BLUE};"><span class="iconify" data-icon="mdi:robot" style="vertical-align:middle;"></span> What is Yield Guard?</h3>
                <div style="color:{colors.TEXT_SECONDARY};font-size:1rem;line-height:1.8;margin-top:1rem;">
                    <div style="margin-bottom:1rem;">DeFi Yield Guard Bot is an intelligent treasury management system that automatically optimizes yield across multiple DeFi protocols while managing risk exposure.</div>
                    <div style="margin-bottom:0.5rem;"><strong style="color:{colors.GRADIENT_PURPLE};">Key Features:</strong></div>
                    <div style="margin-left:1.5rem;">
                        <div style="margin-bottom:0.5rem;"><span class="iconify" data-icon="mdi:check-circle" style="color:{colors.GRADIENT_TEAL};"></span> Multi-protocol yield optimization (Aave, Compound, Morpho)</div>
                        <div style="margin-bottom:0.5rem;"><span class="iconify" data-icon="mdi:check-circle" style="color:{colors.GRADIENT_TEAL};"></span> Automated risk management and rebalancing</div>
                        <div style="margin-bottom:0.5rem;"><span class="iconify" data-icon="mdi:check-circle" style="color:{colors.GRADIENT_TEAL};"></span> Real-time portfolio monitoring and analytics</div>
                        <div style="margin-bottom:0.5rem;"><span class="iconify" data-icon="mdi:check-circle" style="color:{colors.GRADIENT_TEAL};"></span> Historical backtesting and simulation</div>
                        <div><span class="iconify" data-icon="mdi:check-circle" style="color:{colors.GRADIENT_TEAL};"></span> Gas-efficient transaction batching</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        protocols_html = f"""
        <div class="bento-item" style="margin-top:1rem;">
            <h3 style="color:{colors.GRADIENT_TEAL};">
                <span class="iconify" data-icon="mdi:bank-outline" style="vertical-align:middle;"></span>
                Supported Protocols
            </h3>
            <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:1rem;margin-top:1.5rem;">
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};text-align:center;">
                    <span class="iconify" data-icon="cryptocurrency:aave" style="font-size:2.5rem;color:{colors.GRADIENT_PURPLE};"></span>
                    <div style="color:{colors.TEXT_PRIMARY};font-weight:600;margin-top:0.5rem;">Aave V3</div>
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;">Lending Protocol</div>
                </div>
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};text-align:center;">
                    <span class="iconify" data-icon="cryptocurrency:comp" style="font-size:2.5rem;color:{colors.GRADIENT_TEAL};"></span>
                    <div style="color:{colors.TEXT_PRIMARY};font-weight:600;margin-top:0.5rem;">Compound</div>
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;">Money Market</div>
                </div>
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};text-align:center;">
                    <span class="iconify" data-icon="mdi:atom" style="font-size:2.5rem;color:{colors.GRADIENT_ORANGE};"></span>
                    <div style="color:{colors.TEXT_PRIMARY};font-weight:600;margin-top:0.5rem;">Morpho</div>
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;">Optimizer</div>
                </div>
            </div>
        </div>
        """
        st.markdown(protocols_html, unsafe_allow_html=True)

    with col2:
        st.markdown(
            f"""
            <div class="bento-item">
                <h3 style="color:{colors.GRADIENT_ORANGE};"><span class="iconify" data-icon="mdi:palette" style="vertical-align:middle;"></span> Design System</h3>
                <div style="margin-top:1.5rem;">
                    <div style="margin-bottom:1.5rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">Typography</div>
                        <div style="color:{colors.TEXT_SECONDARY};font-size:0.9rem;margin-top:0.5rem;">Space Grotesk (Headings)<br>JetBrains Mono (Metrics)</div>
                    </div>
                    <div style="margin-bottom:1.5rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">Color Palette</div>
                        <div style="display:flex;gap:0.5rem;margin-top:0.5rem;">
                            <div style="width:40px;height:40px;background:{colors.GRADIENT_PURPLE};border-radius:8px;"></div>
                            <div style="width:40px;height:40px;background:{colors.GRADIENT_TEAL};border-radius:8px;"></div>
                            <div style="width:40px;height:40px;background:{colors.GRADIENT_ORANGE};border-radius:8px;"></div>
                            <div style="width:40px;height:40px;background:{colors.GRADIENT_BLUE};border-radius:8px;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">Inspiration</div>
                        <div style="color:{colors.TEXT_SECONDARY};font-size:0.9rem;margin-top:0.5rem;">Spark Protocol aesthetic with<br>dark theme & bento grid layout</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="bento-item" style="margin-top:1rem;">
                <h3 style="color:{colors.GRADIENT_BLUE};"><span class="iconify" data-icon="mdi:code-tags" style="vertical-align:middle;"></span> Tech Stack</h3>
                <div style="margin-top:1.5rem;color:{colors.TEXT_SECONDARY};font-size:0.9rem;line-height:1.8;">
                    <div><span class="iconify" data-icon="mdi:language-python" style="color:{colors.GRADIENT_PURPLE};vertical-align:middle;"></span> Python 3.11+</div>
                    <div><span class="iconify" data-icon="mdi:chart-line" style="color:{colors.GRADIENT_TEAL};vertical-align:middle;"></span> Streamlit</div>
                    <div><span class="iconify" data-icon="mdi:database" style="color:{colors.GRADIENT_ORANGE};vertical-align:middle;"></span> SQLite</div>
                    <div><span class="iconify" data-icon="mdi:chart-box" style="color:{colors.GRADIENT_BLUE};vertical-align:middle;"></span> Plotly</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div class="bento-item" style="margin-top:1rem;text-align:center;padding:2rem;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;">Built with <span class="iconify" data-icon="mdi:heart" style="color:{colors.ACCENT_RED};vertical-align:middle;"></span> for DeFi</div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;margin-top:0.5rem;">Version 2.0 | Spark Protocol Aesthetic</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------
# Landing Page
# ---------------------------------------------------------------------
def render_landing_page():
    st.markdown(
        f"""
        <script src="https://code.iconify.design/3/3.1.0/iconify.min.js"></script>
        <div style="text-align:center;padding:3rem 0;">
            <h1 style="font-size:3.5rem;">
                <span class="iconify" data-icon="mdi:shield-check"></span>
                DeFi Yield Guard Bot
            </h1>
            <p style="font-size:1.25rem;color:{colors.TEXT_SECONDARY};max-width:800px;margin:auto;">
                Intelligent yield optimization with automated risk management across DeFi protocols
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='bento-grid'>", unsafe_allow_html=True)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM simulation_runs")
        total_sims = cur.fetchone()[0]

        cur.execute(
            """
            SELECT
                AVG(total_return),
                AVG(sharpe_ratio),
                AVG(max_drawdown),
                SUM(final_value - initial_capital)
            FROM simulation_runs
            """
        )
        stats = cur.fetchone()
        conn.close()

        avg_return = (stats[0] or 0) * 100
        avg_sharpe = stats[1] or 0
        avg_drawdown = (stats[2] or 0) * 100
        total_profit = stats[3] or 0

    except Exception:
        total_sims = avg_return = avg_sharpe = avg_drawdown = total_profit = 0

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Quick Start card with metrics
        quickstart_html = f"""
        <div class="bento-item bento-wide" style="height:350px;">
            <h3 style="color:{colors.GRADIENT_PURPLE};">
                <span class="iconify" data-icon="mdi:lightning-bolt" style="vertical-align:middle;"></span>
                Quick Start
            </h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:2rem;">
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};">
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Total Simulations</div>
                    <div style="font-size:2rem;color:{colors.GRADIENT_PURPLE};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">{total_sims}</div>
                </div>
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};">
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Avg Sharpe</div>
                    <div style="font-size:2rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">{avg_sharpe:.2f}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(quickstart_html, unsafe_allow_html=True)

    with col2:
        returns_html = f"""
        <div class="bento-item" style="height:350px;display:flex;flex-direction:column;justify-content:center;">
            <h3 style="color:{colors.GRADIENT_TEAL};">
                <span class="iconify" data-icon="mdi:trending-up" style="vertical-align:middle;"></span>
                Returns
            </h3>
            <div style="font-size:3rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;margin:1rem 0;">
                {avg_return:+.2f}%
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.9rem;">Average Total Return</div>
        </div>
        """
        st.markdown(returns_html, unsafe_allow_html=True)

    with col3:
        risk_html = f"""
        <div class="bento-item" style="height:350px;display:flex;flex-direction:column;justify-content:center;">
            <h3 style="color:{colors.GRADIENT_ORANGE};">
                <span class="iconify" data-icon="mdi:alert-circle-outline" style="vertical-align:middle;"></span>
                Risk
            </h3>
            <div style="font-size:3rem;color:{colors.GRADIENT_ORANGE};font-family:JetBrains Mono,monospace;margin:1rem 0;">
                {avg_drawdown:.1f}%
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.9rem;">Average Drawdown</div>
        </div>
        """
        st.markdown(risk_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------
def main():
    initialize_session_state()

    if st.session_state.show_landing:
        with st.sidebar:
            st.markdown(
                f"<h2 style='color:{colors.GRADIENT_BLUE};'>Navigation</h2>",
                unsafe_allow_html=True,
            )
            if st.button("Skip to Dashboard →"):
                st.session_state.show_landing = False
                st.rerun()

        render_landing_page()
    else:
        render_dashboard()


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
def render_dashboard():
    with st.sidebar:
        st.markdown(
            f"""
            <script src="https://code.iconify.design/3/3.1.0/iconify.min.js"></script>
            <h2 style="color:{colors.GRADIENT_PURPLE};">
                <span class="iconify" data-icon="mdi:shield-check"></span>
                Yield Guard
            </h2>
            """,
            unsafe_allow_html=True,
        )

        if st.button("← Back to Home"):
            st.session_state.show_landing = True
            st.rerun()

    st.markdown(
        f"""
        <h1>DeFi Yield Guard Bot</h1>
        <p style="color:{colors.TEXT_SECONDARY};">
            Intelligent yield optimization with automated risk management
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Create tabs - Streamlit doesn't support HTML in tab labels, so using text only
    st.markdown('<script src="https://code.iconify.design/3/3.1.0/iconify.min.js"></script>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "RUN SIMULATION",
        "DASHBOARD",
        "HISTORY",
        "ABOUT"
    ])

    with tab1:
        render_simulation_tab()
    with tab2:
        render_dashboard_tab()
    with tab3:
        render_history_tab()
    with tab4:
        render_about_tab()


# ---------------------------------------------------------------------
# Charts & thresholds FIXES (examples)
# ---------------------------------------------------------------------
def portfolio_chart(x, y):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(color=colors.GRADIENT_BLUE, width=3),
            fill="tozeroy",
            fillcolor="rgba(0, 212, 255, 0.1)",
        )
    )
    fig.update_layout(template=colors.get_plotly_template())
    return fig


# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
