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
from market_data.historical_fetcher import HistoricalDataFetcher
from analytics.performance_metrics import PerformanceMetrics
from database.db import DatabaseManager, SimulationRun, PortfolioSnapshot
from styles.custom_css import get_custom_css
from styles.color_palette import FintechColorPalette as colors

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="DeFi Yield Guard Bot",
    page_icon="🛡️",  # Shield icon for page tab
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


def format_number_eu(value: float, decimals: int = 2) -> str:
    """Format number with European notation (. for thousands, , for decimals)"""
    # Format with specified decimals
    formatted = f"{value:,.{decimals}f}"
    # Swap commas and periods for European notation
    formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    return formatted


def format_currency_eu(value: float) -> str:
    """Format currency with European notation (max 2 decimals)"""
    return f"${format_number_eu(value, 2)}"


def format_percentage_eu(value: float) -> str:
    """Format percentage with European notation (max 2 decimals)"""
    return f"{format_number_eu(value, 2)}%"

# ---------------------------------------------------------------------
# Simulation Tab
# ---------------------------------------------------------------------
def render_simulation_tab():
    st.markdown(
        f"""
        <h2 style="color:{colors.GRADIENT_PURPLE};">
            <ion-icon name="play-circle" style="vertical-align:middle;"></ion-icon>
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
                    <ion-icon name="cog" style="vertical-align:middle;"></ion-icon>
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
                    <ion-icon name="bank" style="vertical-align:middle;"></ion-icon>
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
            with st.spinner("Running simulation... This may take a moment"):
                try:
                    # Build protocol list
                    protocols = []
                    if use_aave:
                        protocols.append("Aave")
                    if use_compound:
                        protocols.append("Compound")
                    if use_morpho:
                        protocols.append("Morpho")

                    if not protocols:
                        st.markdown('<p style="color:#ff4b4b;"><ion-icon name="warning" style="vertical-align:middle;"></ion-icon> Please select at least one protocol</p>', unsafe_allow_html=True)
                        st.stop()

                    # Map risk tolerance to strategy name
                    strategy_map = {
                        "Conservative": "Conservative",
                        "Moderate": "Balanced",
                        "Aggressive": "High Yield"
                    }
                    strategy_name = strategy_map[risk_tolerance]

                    # Initialize simulator
                    simulator = TreasurySimulator(
                        initial_capital=Decimal(str(initial_capital)),
                        name=f"{strategy_name} Strategy"
                    )

                    # Create initial positions based on selected protocols
                    # Distribute capital across protocols with proper precision handling
                    total_capital = Decimal(str(initial_capital))
                    num_protocols = len(protocols)

                    # Estimate transaction costs to reserve capital
                    # Gas fee per deposit is ~$15, protocol fees vary by protocol (0-0.09%)
                    estimated_gas_per_deposit = Decimal('15.00')
                    total_estimated_gas = estimated_gas_per_deposit * num_protocols

                    # Reserve additional buffer for protocol fees and slippage (~0.1% of capital)
                    estimated_protocol_fees = total_capital * Decimal('0.001')

                    # Total costs to reserve
                    total_reserved_costs = total_estimated_gas + estimated_protocol_fees

                    # Capital available for actual deposits (after reserving for costs)
                    deployable_capital = total_capital - total_reserved_costs

                    # Calculate per-protocol amount from deployable capital
                    capital_per_protocol = (deployable_capital / num_protocols).quantize(Decimal('0.01'))

                    # For the last protocol, use remaining capital to avoid rounding errors
                    remaining_capital = deployable_capital

                    # Define APY ranges based on risk tolerance
                    # Using realistic DeFi lending rates (updated for better returns)
                    apy_ranges = {
                        "Conservative": {"supply": Decimal('0.055'), "borrow": Decimal('0.065')},  # 5.5% supply, 6.5% borrow
                        "Moderate": {"supply": Decimal('0.085'), "borrow": Decimal('0.095')},     # 8.5% supply, 9.5% borrow
                        "Aggressive": {"supply": Decimal('0.125'), "borrow": Decimal('0.145')}    # 12.5% supply, 14.5% borrow
                    }
                    apys = apy_ranges[risk_tolerance]

                    # Create positions in selected protocols
                    for i, protocol in enumerate(protocols):
                        protocol_name = protocol.lower()

                        # For last protocol, use all remaining capital
                        if i == num_protocols - 1:
                            amount = remaining_capital
                        else:
                            amount = capital_per_protocol
                            remaining_capital -= amount

                        simulator.deposit(
                            protocol=protocol_name,
                            asset_symbol="USDC",
                            amount=amount,
                            supply_apy=apys["supply"],
                            borrow_apy=apys["borrow"],
                            ltv=Decimal('0.75'),
                            liquidation_threshold=Decimal('0.80')
                        )

                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Determine volatility level based on risk tier
                    volatility_levels = {
                        'Conservative': 'low',     # ±0.2-0.5% APY variation
                        'Moderate': 'medium',      # ±0.5-1.5% APY variation
                        'Aggressive': 'high'       # ±1-3% APY variation
                    }
                    volatility_level = volatility_levels.get(strategy_name, 'low')

                    # Run simulation with progress updates and market volatility
                    snapshots = []
                    for day in range(simulation_days):
                        # Update progress
                        progress = (day + 1) / simulation_days
                        progress_bar.progress(progress)
                        status_text.text(f"Simulating day {day + 1}/{simulation_days}...")

                        # Generate market volatility for this day
                        market_data = {}
                        for position in simulator.positions:
                            if position.protocol not in market_data:
                                market_data[position.protocol] = {}

                            # Generate APY fluctuations
                            new_rates = simulator._generate_market_volatility(
                                position.supply_apy,
                                position.borrow_apy,
                                volatility_level
                            )

                            market_data[position.protocol][position.asset_symbol] = {
                                'supply_apy': new_rates['supply_apy'],
                                'borrow_apy': new_rates['borrow_apy']
                            }

                        # Simulate one day with market data
                        snapshot = simulator.step(days=Decimal('1'), market_data=market_data)
                        snapshots.append(snapshot)

                    # Calculate performance metrics
                    metrics = PerformanceMetrics()

                    final_value = snapshots[-1].net_value if snapshots else simulator.initial_capital
                    total_return = metrics.calculate_total_return(
                        simulator.initial_capital,
                        final_value
                    )
                    annualized_return = metrics.calculate_annualized_return(
                        simulator.initial_capital,
                        final_value,
                        simulation_days
                    )

                    # Calculate max drawdown
                    portfolio_values = [s.net_value for s in snapshots]
                    max_dd_data = metrics.calculate_max_drawdown(portfolio_values)
                    max_drawdown = max_dd_data['max_drawdown']

                    # Calculate Sharpe ratio
                    daily_returns = []
                    for i in range(1, len(portfolio_values)):
                        prev_val = portfolio_values[i-1]
                        curr_val = portfolio_values[i]
                        if prev_val > 0:
                            daily_ret = (curr_val - prev_val) / prev_val
                            daily_returns.append(daily_ret)

                    # Only calculate Sharpe if we have enough data (at least 7 days)
                    if len(daily_returns) >= 7:
                        sharpe = metrics.calculate_sharpe_ratio(daily_returns, annualize=True)
                        # Ensure reasonable Sharpe ratio values
                        if sharpe == Decimal('Infinity') or sharpe == Decimal('-Infinity'):
                            sharpe = Decimal('0')
                        elif abs(float(sharpe)) > 10:  # Cap extremely high values
                            sharpe = Decimal('0')
                    else:
                        # Not enough data for meaningful Sharpe ratio
                        sharpe = Decimal('0')

                    # Save to database
                    db = DatabaseManager(st.session_state.config.database_path)
                    db.init_db()

                    sim_run = SimulationRun(
                        strategy_name=strategy_name,
                        initial_capital=float(initial_capital),
                        simulation_days=simulation_days,
                        protocols_used=", ".join(protocols),
                        total_return=float(total_return),
                        annualized_return=float(annualized_return),
                        max_drawdown=float(max_drawdown),
                        sharpe_ratio=float(sharpe),
                        final_value=float(final_value),
                        total_gas_fees=float(simulator.total_gas_fees),
                        num_rebalances=simulator.num_transactions,  # Track total transactions for now
                        created_at=datetime.now()
                    )

                    simulation_id = db.save_simulation_run(sim_run)

                    # Save daily snapshots
                    for day, snapshot in enumerate(snapshots):
                        ps = PortfolioSnapshot(
                            simulation_id=simulation_id,
                            day=day,
                            net_value=float(snapshot.net_value),
                            total_collateral=float(snapshot.total_collateral),
                            total_debt=float(snapshot.total_debt),
                            overall_health_factor=float(snapshot.overall_health_factor) if snapshot.overall_health_factor != Decimal('Infinity') else None,
                            cumulative_yield=float(snapshot.cumulative_yield),
                            timestamp=snapshot.timestamp
                        )
                        db.save_portfolio_snapshot(ps)

                    # Store simulation ID in session state
                    st.session_state.last_simulation_id = simulation_id

                    progress_bar.progress(1.0)
                    status_text.empty()

                    # Determine risk color
                    risk_colors = {
                        'Conservative': colors.GRADIENT_TEAL,
                        'Moderate': colors.GRADIENT_ORANGE,
                        'Aggressive': colors.ACCENT_RED
                    }
                    risk_color = risk_colors.get(strategy_name, colors.GRADIENT_PURPLE)

                    st.markdown(f'<p style="color:#00c851;"><ion-icon name="checkmark-circle" style="vertical-align:middle;"></ion-icon> Simulation complete! <span style="color:{risk_color}; font-weight:700;">[{strategy_name} Risk]</span> | Final value: {format_currency_eu(float(final_value))} | Return: {format_percentage_eu(float(total_return)*100)}</p>', unsafe_allow_html=True)

                    # Display transaction costs summary
                    st.markdown(
                        f"""
                        <div style="background:{colors.BG_SECONDARY}; padding:1rem; border-radius:8px; margin:1rem 0;">
                            <p style="color:{colors.TEXT_TERTIARY}; font-size:0.75rem; text-transform:uppercase; margin:0 0 0.5rem 0;">Transaction Costs</p>
                            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:1rem; font-family:JetBrains Mono,monospace; font-size:0.85rem;">
                                <div>
                                    <span style="color:{colors.TEXT_TERTIARY};">Gas Fees:</span>
                                    <span style="color:{colors.ACCENT_RED}; margin-left:0.5rem;">{format_currency_eu(float(simulator.total_gas_fees))}</span>
                                </div>
                                <div>
                                    <span style="color:{colors.TEXT_TERTIARY};">Protocol Fees:</span>
                                    <span style="color:{colors.ACCENT_ORANGE}; margin-left:0.5rem;">{format_currency_eu(float(simulator.total_protocol_fees))}</span>
                                </div>
                                <div>
                                    <span style="color:{colors.TEXT_TERTIARY};">Slippage:</span>
                                    <span style="color:{colors.ACCENT_ORANGE}; margin-left:0.5rem;">{format_currency_eu(float(simulator.total_slippage))}</span>
                                </div>
                                <div>
                                    <span style="color:{colors.TEXT_TERTIARY};">Total Costs:</span>
                                    <span style="color:{colors.ACCENT_RED}; margin-left:0.5rem; font-weight:700;">{format_currency_eu(float(simulator.total_gas_fees + simulator.total_protocol_fees + simulator.total_slippage))}</span>
                                </div>
                            </div>
                            <p style="color:{colors.TEXT_TERTIARY}; font-size:0.7rem; margin:0.5rem 0 0 0; font-style:italic;">
                                {simulator.num_transactions} transactions executed
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Display per-protocol performance breakdown
                    if simulator.positions:
                        st.markdown("---")
                        st.markdown(
                            f"""
                            <h3 style="color:{colors.TEXT_PRIMARY};">
                                <ion-icon name="stats-chart" style="vertical-align:middle;"></ion-icon>
                                Protocol Performance Breakdown
                            </h3>
                            """,
                            unsafe_allow_html=True
                        )

                        # Create columns for each protocol
                        num_protocols = len(simulator.positions)
                        cols = st.columns(num_protocols)

                        for idx, position in enumerate(simulator.positions):
                            with cols[idx]:
                                # Calculate position-specific metrics
                                position_value = position.collateral_amount - position.debt_amount
                                initial_position_value = (total_capital / num_protocols).quantize(Decimal('0.01'))
                                position_return = ((position_value - initial_position_value) / initial_position_value) * 100
                                position_apy = position.supply_apy * 100

                                # Determine color based on performance
                                perf_color = colors.SUCCESS if position_return > 0 else colors.ERROR if position_return < 0 else colors.TEXT_SECONDARY

                                st.markdown(
                                    f"""
                                    <div style="background:{colors.BG_SECONDARY}; padding:1.5rem; border-radius:12px; border-left:4px solid {colors.GRADIENT_PURPLE};">
                                        <p style="color:{colors.TEXT_TERTIARY}; font-size:0.75rem; text-transform:uppercase; margin:0; font-family:Space Grotesk,sans-serif; letter-spacing:0.05em;">
                                            {position.protocol.upper()}
                                        </p>
                                        <h2 style="color:{colors.TEXT_PRIMARY}; margin:0.5rem 0; font-family:JetBrains Mono,monospace;">{format_currency_eu(float(position_value))}</h2>
                                        <p style="color:{perf_color}; margin:0; font-size:0.9rem; font-family:JetBrains Mono,monospace;">
                                            {'+' if position_return > 0 else ''}{format_percentage_eu(float(position_return))} return
                                        </p>
                                        <hr style="border:none; border-top:1px solid {colors.BG_PRIMARY}; margin:0.75rem 0;">
                                        <p style="color:{colors.TEXT_TERTIARY}; font-size:0.8rem; margin:0; font-family:JetBrains Mono,monospace;">
                                            APY: {format_percentage_eu(float(position_apy))}
                                        </p>
                                        <p style="color:{colors.TEXT_TERTIARY}; font-size:0.8rem; margin:0; font-family:JetBrains Mono,monospace;">
                                            Collateral: {format_currency_eu(float(position.collateral_amount))}
                                        </p>
                                        <p style="color:{colors.TEXT_TERTIARY}; font-size:0.8rem; margin:0; font-family:JetBrains Mono,monospace;">
                                            Debt: {format_currency_eu(float(position.debt_amount))}
                                        </p>
                                        <p style="color:{colors.TEXT_TERTIARY}; font-size:0.8rem; margin:0; font-family:JetBrains Mono,monospace;">
                                            Health: {format_number_eu(float(position.health_factor), 2)}
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                    st.markdown('<p style="color:#33b5e5;"><ion-icon name="analytics" style="vertical-align:middle;"></ion-icon> View full results in the DASHBOARD tab</p>', unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f'<p style="color:#ff4b4b;"><ion-icon name="close-circle" style="vertical-align:middle;"></ion-icon> Simulation failed: {str(e)}</p>', unsafe_allow_html=True)
                    import traceback
                    st.code(traceback.format_exc())

    with col2:
        st.markdown(
            f"""
            <div class="bento-item" style="padding:1.5rem;">
                <h3 style="color:{colors.GRADIENT_ORANGE};">
                    <ion-icon name="information" style="vertical-align:middle;"></ion-icon>
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
            <ion-icon name="view-dashboard" style="vertical-align:middle;"></ion-icon>
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
            # Validate and sanitize Sharpe ratio
            if sharpe is None or abs(sharpe) > 10 or sharpe != sharpe:  # None, too large, or NaN
                sharpe = 0.0
            sharpe = round(float(sharpe), 2)
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
        <div class="bento-item" style="padding:1.5rem; height:200px; display:flex; flex-direction:column; box-sizing:border-box;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <ion-icon name="wallet" style="vertical-align:middle;"></ion-icon>
                Portfolio Value
            </div>
            <div style="font-size:2rem;color:{colors.GRADIENT_PURPLE};font-family:JetBrains Mono,monospace;line-height:1.2;">
                {format_currency_eu(final_val)}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;margin-top:0.5rem;">
                Initial: {format_currency_eu(initial_cap)}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.65rem;margin-top:auto;padding-top:0.5rem;opacity:0.8;font-style:italic;line-height:1.3;">
                Total value including positions, collateral & debt
            </div>
        </div>
        """
        st.markdown(metric_card_html, unsafe_allow_html=True)

    with col2:
        pnl_color = colors.GRADIENT_TEAL if pnl >= 0 else colors.ACCENT_RED
        pnl_icon = "trending-up" if pnl >= 0 else "trending-down"
        metric_card_html = f"""
        <div class="bento-item" style="padding:1.5rem; height:200px; display:flex; flex-direction:column; box-sizing:border-box;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <ion-icon name="{pnl_icon}" style="vertical-align:middle;"></ion-icon>
                P&L
            </div>
            <div style="font-size:2rem;color:{pnl_color};font-family:JetBrains Mono,monospace;line-height:1.2;">
                {'+' if pnl >= 0 else ''}{format_percentage_eu(pnl_pct)}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;margin-top:0.5rem;">
                {'+' if pnl >= 0 else ''}{format_currency_eu(abs(pnl))}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.65rem;margin-top:auto;padding-top:0.5rem;opacity:0.8;font-style:italic;line-height:1.3;">
                (Final - Initial) / Initial Capital
            </div>
        </div>
        """
        st.markdown(metric_card_html, unsafe_allow_html=True)

    with col3:
        # Clamp Sharpe to reasonable values
        sharpe_clamped = min(max(float(sharpe), -10), 10)
        metric_card_html = f"""
        <div class="bento-item" style="padding:1.5rem; height:200px; display:flex; flex-direction:column; box-sizing:border-box;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <ion-icon name="analytics" style="vertical-align:middle;"></ion-icon>
                Sharpe Ratio
            </div>
            <div style="font-size:2rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;line-height:1.2;">
                {format_number_eu(sharpe_clamped, 2)}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;margin-top:0.5rem;">
                Risk-adjusted return
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.65rem;margin-top:auto;padding-top:0.5rem;opacity:0.8;font-style:italic;line-height:1.3;">
                >1,0 Good, >1,5 Very Good, >2,0 Excellent
            </div>
        </div>
        """
        st.markdown(metric_card_html, unsafe_allow_html=True)

    with col4:
        metric_card_html = f"""
        <div class="bento-item" style="padding:1.5rem; height:200px; display:flex; flex-direction:column; box-sizing:border-box;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">
                <ion-icon name="alert-circle" style="vertical-align:middle;"></ion-icon>
                Max Drawdown
            </div>
            <div style="font-size:2rem;color:{colors.GRADIENT_ORANGE};font-family:JetBrains Mono,monospace;line-height:1.2;">
                {format_percentage_eu(drawdown)}
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;margin-top:0.5rem;">
                Peak to trough
            </div>
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.65rem;margin-top:auto;padding-top:0.5rem;opacity:0.8;font-style:italic;line-height:1.3;">
                Largest drop from high to low. Lower is better
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
                    <ion-icon name="trending-up" style="vertical-align:middle;"></ion-icon>
                    Portfolio Performance
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Fetch snapshot data from database for the latest simulation
        try:
            # Open new database connection for chart data
            chart_conn = get_db_connection()
            chart_cur = chart_conn.cursor()

            snapshot_query = """
                SELECT
                    day,
                    net_value,
                    total_collateral,
                    total_debt,
                    overall_health_factor,
                    cumulative_yield,
                    timestamp
                FROM portfolio_snapshots
                WHERE simulation_id = (SELECT id FROM simulation_runs ORDER BY created_at DESC LIMIT 1)
                ORDER BY day ASC
            """
            chart_cur.execute(snapshot_query)
            snapshot_rows = chart_cur.fetchall()
            chart_conn.close()

            if snapshot_rows and len(snapshot_rows) > 1:
                # Extract data from snapshots
                days = [row[0] for row in snapshot_rows]
                net_values = [row[1] for row in snapshot_rows]
                collaterals = [row[2] for row in snapshot_rows]
                debts = [row[3] for row in snapshot_rows]
                health_factors = [row[4] if row[4] is not None and row[4] != float('inf') else None for row in snapshot_rows]

                # Create figure with secondary y-axis
                fig = go.Figure()

                # Add portfolio value trace (main)
                fig.add_trace(go.Scatter(
                    x=days,
                    y=net_values,
                    mode='lines',
                    name='Net Value',
                    line=dict(color=colors.GRADIENT_PURPLE, width=3),
                    fill='tozeroy',
                    fillcolor='rgba(107, 95, 237, 0.15)',
                    hovertemplate='<b>Day %{x}</b><br>Net Value: $%{y:,.2f}<extra></extra>',
                    yaxis='y1'
                ))

                # Add collateral trace
                fig.add_trace(go.Scatter(
                    x=days,
                    y=collaterals,
                    mode='lines',
                    name='Collateral',
                    line=dict(color=colors.GRADIENT_TEAL, width=2, dash='dot'),
                    hovertemplate='<b>Day %{x}</b><br>Collateral: $%{y:,.2f}<extra></extra>',
                    yaxis='y1'
                ))

                # Add debt trace
                fig.add_trace(go.Scatter(
                    x=days,
                    y=debts,
                    mode='lines',
                    name='Debt',
                    line=dict(color=colors.ACCENT_RED, width=2, dash='dash'),
                    hovertemplate='<b>Day %{x}</b><br>Debt: $%{y:,.2f}<extra></extra>',
                    yaxis='y1'
                ))

                # Add health factor trace on secondary axis (only if we have debt)
                if any(d > 0 for d in debts):
                    # Filter out None values for health factor
                    hf_days = [d for d, hf in zip(days, health_factors) if hf is not None]
                    hf_values = [hf for hf in health_factors if hf is not None]

                    if hf_values:
                        fig.add_trace(go.Scatter(
                            x=hf_days,
                            y=hf_values,
                            mode='lines',
                            name='Health Factor',
                            line=dict(color=colors.ACCENT_ORANGE, width=2),
                            hovertemplate='<b>Day %{x}</b><br>Health Factor: %{y:.2f}<extra></extra>',
                            yaxis='y2'
                        ))

                        # Add critical health factor line at 1.0
                        fig.add_hline(
                            y=1.0,
                            line=dict(color=colors.ACCENT_RED, width=1, dash='dot'),
                            annotation_text="Liquidation Risk",
                            annotation_position="right",
                            yref='y2'
                        )

                # Get base template and update with custom settings
                layout_config = colors.get_plotly_template()['layout'].copy()

                # Update xaxis settings
                layout_config['xaxis'].update({
                    'title': "Day",
                    'showgrid': True
                })

                # Update yaxis settings
                layout_config['yaxis'].update({
                    'title': "USD Value",
                    'side': 'left',
                    'showgrid': True,
                    'tickformat': '$,.0f'
                })

                # Add secondary yaxis for health factor
                layout_config['yaxis2'] = {
                    'title': "Health Factor",
                    'side': 'right',
                    'overlaying': 'y',
                    'showgrid': False,
                    'tickformat': '.2f',
                    'gridcolor': colors.BORDER_PRIMARY,
                    'linecolor': colors.BORDER_ACCENT,
                    'range': [0, max(hf_values) * 1.1] if any(d > 0 for d in debts) and hf_values else None
                }

                # Apply layout
                fig.update_layout(
                    **layout_config,
                    height=340,
                    margin=dict(l=10, r=10, t=20, b=70),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.35,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback to simple placeholder if no snapshot data
                st.markdown(
                    f"""
                    <div class="bento-item" style="padding:2rem;text-align:center;">
                        <p style="color:{colors.TEXT_TERTIARY};font-size:0.9rem;">
                            <ion-icon name="information-circle" style="vertical-align:middle;font-size:1.5rem;"></ion-icon><br>
                            No snapshot data available. Run a simulation to see performance charts.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        except Exception as e:
            st.error(f"Error loading chart data: {str(e)}")
            # Simple fallback chart
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            values = [initial_cap * (1 + i/1000) for i in range(30)]

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
                    <ion-icon name="finance" style="vertical-align:middle;"></ion-icon>
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
            <ion-icon name="history" style="vertical-align:middle;"></ion-icon>
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

            # Format columns with European notation
            df['Initial Capital'] = df['Initial Capital'].apply(lambda x: format_currency_eu(x))
            df['Final Value'] = df['Final Value'].apply(lambda x: format_currency_eu(x))
            df['Total Return'] = df['Total Return'].apply(lambda x: f"{'+' if x >= 0 else ''}{format_percentage_eu(x*100)}")
            df['Sharpe Ratio'] = df['Sharpe Ratio'].apply(lambda x: format_number_eu(min(max(x, -10), 10), 2))  # Clamp to reasonable range
            df['Max Drawdown'] = df['Max Drawdown'].apply(lambda x: format_percentage_eu(x*100))
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')

            # Build HTML table with full control
            table_rows = ""
            for _, row in df.iterrows():
                table_rows += f"""<tr>
                    <td>{row['ID']}</td>
                    <td>{row['Initial Capital']}</td>
                    <td>{row['Final Value']}</td>
                    <td>{row['Total Return']}</td>
                    <td>{row['Sharpe Ratio']}</td>
                    <td>{row['Max Drawdown']}</td>
                    <td>{row['Rebalances']}</td>
                    <td>{row['Date']}</td>
                </tr>"""

            st.markdown(
                f"""
                <div class="bento-item">
                    <h3 style="color:{colors.GRADIENT_PURPLE};">
                        <ion-icon name="table" style="vertical-align:middle;"></ion-icon>
                        Recent Simulations ({len(rows)} runs)
                    </h3>
                </div>
                <div class="bento-item" style="padding:0; overflow:auto; max-height:500px;">
                    <table style="width:100%; border-collapse:collapse;">
                        <thead style="position:sticky; top:0; z-index:10;">
                            <tr>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">ID</th>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">Initial Capital</th>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">Final Value</th>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">Total Return</th>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">Sharpe Ratio</th>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">Max Drawdown</th>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">Rebalances</th>
                                <th style="background:{colors.BG_TERTIARY}; color:{colors.TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:1rem; text-align:left; border-bottom:2px solid {colors.BORDER_ACCENT};">Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
                <style>
                    .bento-item table tbody tr {{
                        background:{colors.BG_SECONDARY};
                        transition: all 0.2s ease;
                    }}
                    .bento-item table tbody tr:hover {{
                        background:{colors.BG_TERTIARY};
                    }}
                    .bento-item table tbody td {{
                        color:{colors.TEXT_PRIMARY};
                        font-family:'JetBrains Mono',monospace;
                        font-size:0.875rem;
                        font-weight:600;
                        padding:0.875rem 1rem;
                        border-bottom:1px solid {colors.BORDER_PRIMARY};
                    }}
                </style>
                """,
                unsafe_allow_html=True
            )

            # Summary stats
            col1, col2, col3 = st.columns(3)

            with col1:
                best_return = max([r[3] for r in rows])*100
                st.markdown(
                    f"""
                    <div class="bento-item" style="padding:1.5rem;margin-top:1rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">
                            <ion-icon name="trophy" style="vertical-align:middle;"></ion-icon>
                            Best Return
                        </div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">
                            {'+' if best_return >= 0 else ''}{format_percentage_eu(best_return)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                avg_sharpe = (sum([r[4] for r in rows])/len(rows)) if rows else 0
                # Clamp to reasonable range
                avg_sharpe = min(max(avg_sharpe, -10), 10)
                st.markdown(
                    f"""
                    <div class="bento-item" style="padding:1.5rem;margin-top:1rem;">
                        <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;">
                            <ion-icon name="chart-bar" style="vertical-align:middle;"></ion-icon>
                            Avg Sharpe
                        </div>
                        <div style="font-size:1.5rem;color:{colors.GRADIENT_PURPLE};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">
                            {format_number_eu(avg_sharpe, 2)}
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
                            <ion-icon name="sigma" style="vertical-align:middle;"></ion-icon>
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
                    <ion-icon name="information-outline" style="font-size:3rem;color:{colors.TEXT_TERTIARY};"></ion-icon>
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
def render_historical_backtest_tab():
    """Render Historical Backtest tab with real market data"""
    st.markdown(
        f"""
        <h2 style="color:{colors.GRADIENT_PURPLE};">
            <ion-icon name="analytics" style="vertical-align:middle;"></ion-icon>
            Historical Backtest
        </h2>
        <p style="color:{colors.TEXT_SECONDARY};">Backtest strategies using REAL historical DeFi market data</p>
        """,
        unsafe_allow_html=True
    )

    # Configuration Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"<h3 style='color:{colors.TEXT_PRIMARY};'>Backtest Configuration</h3>", unsafe_allow_html=True)

        # Protocol Selection
        protocol = st.selectbox(
            "Select Protocol",
            ["aave-v3", "compound-v3"],
            help="Choose which DeFi protocol to backtest"
        )

        # Asset Selection
        asset = st.selectbox(
            "Select Asset",
            ["USDC", "USDT", "DAI", "WETH", "WBTC"],
            help="Choose which asset to analyze"
        )

        # Chain Selection
        chain = st.selectbox(
            "Select Chain",
            ["Ethereum", "Polygon", "Arbitrum", "Optimism", "Base"],
            help="Choose which blockchain network"
        )

        # Time Period
        time_period = st.selectbox(
            "Time Period",
            ["30 Days", "90 Days", "180 Days", "1 Year"],
            index=3,
            help="How far back to analyze"
        )

        days_map = {
            "30 Days": 30,
            "90 Days": 90,
            "180 Days": 180,
            "1 Year": 365
        }
        days_back = days_map[time_period]

        # Initial Capital
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=100.0,
            max_value=10000000.0,
            value=10000.0,
            step=1000.0,
            help="Starting investment amount"
        )

    with col2:
        st.markdown(f"<h3 style='color:{colors.TEXT_PRIMARY};'>Cache Settings</h3>", unsafe_allow_html=True)

        use_cache = st.checkbox(
            "Use cached data (faster)",
            value=True,
            help="Use locally cached historical data to avoid API calls"
        )

        if use_cache:
            cache_age = st.number_input(
                "Max cache age (hours)",
                min_value=1,
                max_value=168,
                value=24,
                help="Maximum age of cached data before refreshing"
            )
        else:
            cache_age = 0

        st.markdown("---")

        # Info box
        st.markdown(
            f"""
            <div style="background:{colors.BG_SECONDARY}; padding:1rem; border-radius:8px; border-left:4px solid {colors.GRADIENT_BLUE};">
                <p style="color:{colors.TEXT_SECONDARY}; margin:0; font-size:0.9rem;">
                    <ion-icon name="information-circle" style="vertical-align:middle;"></ion-icon>
                    <strong>Real Data Source</strong><br>
                    Uses DefiLlama API to fetch actual historical APY rates, TVL, and protocol data.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Run Backtest Button
    st.markdown("---")

    if st.button("RUN HISTORICAL BACKTEST", key="run_backtest_btn", use_container_width=True, type="primary"):
        with st.spinner(f"Fetching {days_back} days of historical data..."):
            try:
                # Initialize database and fetcher
                db = DatabaseManager(st.session_state.config.database_path)
                db.init_db()
                fetcher = HistoricalDataFetcher()

                # Try to get cached data first
                cached_data = None
                if use_cache:
                    st.info(f"Checking cache for {protocol}/{asset} on {chain}...")
                    cached_data = db.get_historical_data(
                        protocol=protocol,
                        asset_symbol=asset,
                        chain=chain,
                        days_back=days_back,
                        max_age_hours=cache_age
                    )

                if cached_data:
                    st.success(f"Using cached data ({len(cached_data)} days)")
                    historical_dicts = cached_data
                else:
                    # Fetch fresh data
                    st.info(f"Fetching fresh data from DefiLlama API...")
                    historical = fetcher.get_historical_data_for_backtest(
                        protocol=protocol,
                        asset_symbol=asset,
                        chain=chain,
                        days_back=days_back
                    )

                    if not historical:
                        st.error(f"Could not fetch data for {protocol}/{asset} on {chain}")
                        st.stop()

                    st.success(f"Fetched {len(historical)} days of real market data")

                    # Convert to dicts and cache
                    historical_dicts = [h.to_dict() for h in historical]

                    if use_cache:
                        cache_id = db.save_historical_data(
                            protocol=protocol,
                            asset_symbol=asset,
                            chain=chain,
                            days_back=days_back,
                            historical_data=historical_dicts
                        )
                        st.success(f"✓ Cached for future use (ID: {cache_id})")

                # Convert back to objects for processing
                from decimal import Decimal
                from datetime import datetime

                historical = []
                for d in historical_dicts:
                    from dataclasses import dataclass
                    from market_data.historical_fetcher import HistoricalYield

                    historical.append(HistoricalYield(
                        timestamp=datetime.fromisoformat(d['timestamp']) if isinstance(d['timestamp'], str) else d['timestamp'],
                        protocol=d['protocol'],
                        chain=d['chain'],
                        pool_id=d['pool_id'],
                        asset_symbol=d['asset_symbol'],
                        apy=Decimal(str(d['apy'])),
                        tvl_usd=Decimal(str(d['tvl_usd']))
                    ))

                # Show data summary
                st.markdown("---")
                st.markdown(f"<h3 style='color:{colors.TEXT_PRIMARY};'>Data Summary</h3>", unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)

                apys = [float(h.apy * 100) for h in historical]
                tvls = [float(h.tvl_usd) for h in historical]

                with col1:
                    st.metric("Data Points", len(historical))
                with col2:
                    st.metric("Avg APY", f"{sum(apys)/len(apys):.2f}%")
                with col3:
                    st.metric("Min APY", f"{min(apys):.2f}%")
                with col4:
                    st.metric("Max APY", f"{max(apys):.2f}%")

                # Run backtest simulation
                st.markdown("---")
                st.markdown(f"<h3 style='color:{colors.TEXT_PRIMARY};'>Running Backtest Simulation...</h3>", unsafe_allow_html=True)

                progress_bar = st.progress(0)
                status_text = st.empty()

                # Initialize simulator
                deposit_amount = Decimal(str(initial_capital)).quantize(Decimal('0.01'))

                simulator = TreasurySimulator(
                    initial_capital=deposit_amount,
                    name=f"Historical Backtest - {protocol}/{asset}",
                    min_health_factor=Decimal('1.5')
                )

                # Open initial position
                simulator.deposit(
                    protocol=protocol.split('-')[0],  # 'aave' from 'aave-v3'
                    asset_symbol=asset,
                    amount=deposit_amount,
                    supply_apy=historical[0].apy,
                    borrow_apy=historical[0].apy * Decimal('1.2'),
                    ltv=Decimal('0.75'),
                    liquidation_threshold=Decimal('0.80')
                )

                # Run simulation day by day
                snapshots = []
                for day in range(len(historical)):
                    progress = (day + 1) / len(historical)
                    progress_bar.progress(progress)
                    status_text.text(f"Day {day + 1}/{len(historical)}...")

                    # Update APY with real historical data
                    if simulator.positions:
                        simulator.positions[0].supply_apy = historical[day].apy
                        simulator.positions[0].borrow_apy = historical[day].apy * Decimal('1.2')

                    # Step forward
                    snapshot = simulator.step(days=Decimal('1'))
                    snapshots.append(snapshot)

                progress_bar.empty()
                status_text.empty()

                # Calculate performance metrics
                portfolio_values = [s.net_value for s in snapshots]
                final_value = portfolio_values[-1] if portfolio_values else Decimal(str(initial_capital))

                metrics = PerformanceMetrics()

                total_return = metrics.calculate_total_return(
                    Decimal(str(initial_capital)),
                    final_value
                )

                annualized_return = metrics.calculate_annualized_return(
                    Decimal(str(initial_capital)),
                    final_value,
                    len(historical)
                )

                max_dd_data = metrics.calculate_max_drawdown(portfolio_values)
                max_drawdown = max_dd_data['max_drawdown']

                # Calculate Sharpe ratio
                daily_returns = []
                for i in range(1, len(portfolio_values)):
                    prev_val = portfolio_values[i-1]
                    curr_val = portfolio_values[i]
                    if prev_val > 0:
                        daily_return = float((curr_val - prev_val) / prev_val)
                        daily_returns.append(daily_return)

                sharpe = metrics.calculate_sharpe_ratio(daily_returns)

                # Display Results
                st.markdown("---")
                st.markdown(
                    f"""
                    <h2 style="color:{colors.GRADIENT_TEAL};">
                        <ion-icon name="trophy" style="vertical-align:middle;"></ion-icon>
                        Backtest Results
                    </h2>
                    """,
                    unsafe_allow_html=True
                )

                # Performance metrics cards
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(
                        f"""
                        <div style="background:{colors.BG_SECONDARY}; padding:1.5rem; border-radius:12px; border-left:4px solid {colors.SUCCESS};">
                            <p style="color:{colors.TEXT_SECONDARY}; font-size:0.9rem; margin:0;">Total Return</p>
                            <h2 style="color:{colors.SUCCESS}; margin:0.5rem 0;">{total_return:.2f}%</h2>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        f"""
                        <div style="background:{colors.BG_SECONDARY}; padding:1.5rem; border-radius:12px; border-left:4px solid {colors.GRADIENT_BLUE};">
                            <p style="color:{colors.TEXT_SECONDARY}; font-size:0.9rem; margin:0;">Annualized Return</p>
                            <h2 style="color:{colors.GRADIENT_BLUE}; margin:0.5rem 0;">{annualized_return:.2f}%</h2>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col3:
                    dd_color = colors.SUCCESS if max_drawdown > -10 else colors.WARNING if max_drawdown > -20 else colors.ERROR
                    st.markdown(
                        f"""
                        <div style="background:{colors.BG_SECONDARY}; padding:1.5rem; border-radius:12px; border-left:4px solid {dd_color};">
                            <p style="color:{colors.TEXT_SECONDARY}; font-size:0.9rem; margin:0;">Max Drawdown</p>
                            <h2 style="color:{dd_color}; margin:0.5rem 0;">{max_drawdown:.2f}%</h2>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col4:
                    sharpe_color = colors.SUCCESS if sharpe > 1.5 else colors.WARNING if sharpe > 1.0 else colors.ERROR
                    st.markdown(
                        f"""
                        <div style="background:{colors.BG_SECONDARY}; padding:1.5rem; border-radius:12px; border-left:4px solid {sharpe_color};">
                            <p style="color:{colors.TEXT_SECONDARY}; font-size:0.9rem; margin:0;">Sharpe Ratio</p>
                            <h2 style="color:{sharpe_color}; margin:0.5rem 0;">{sharpe:.2f}</h2>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Portfolio value chart
                st.markdown("---")
                st.markdown(f"<h3 style='color:{colors.TEXT_PRIMARY};'>Portfolio Value Over Time</h3>", unsafe_allow_html=True)

                fig = go.Figure()

                days = list(range(len(portfolio_values)))
                values = [float(v) for v in portfolio_values]

                fig.add_trace(go.Scatter(
                    x=days,
                    y=values,
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color=colors.GRADIENT_TEAL, width=2),
                    fill='tozeroy',
                    fillcolor=f'rgba(61, 186, 165, 0.1)'
                ))

                fig.update_layout(
                    plot_bgcolor=colors.BG_PRIMARY,
                    paper_bgcolor=colors.BG_PRIMARY,
                    font=dict(color=colors.TEXT_PRIMARY),
                    xaxis_title="Day",
                    yaxis_title="Portfolio Value ($)",
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # APY over time chart
                st.markdown(f"<h3 style='color:{colors.TEXT_PRIMARY};'>Historical APY Rates</h3>", unsafe_allow_html=True)

                fig2 = go.Figure()

                fig2.add_trace(go.Scatter(
                    x=list(range(len(apys))),
                    y=apys,
                    mode='lines',
                    name='Supply APY',
                    line=dict(color=colors.GRADIENT_PURPLE, width=2)
                ))

                fig2.update_layout(
                    plot_bgcolor=colors.BG_PRIMARY,
                    paper_bgcolor=colors.BG_PRIMARY,
                    font=dict(color=colors.TEXT_PRIMARY),
                    xaxis_title="Day",
                    yaxis_title="APY (%)",
                    hovermode='x unified',
                    height=300
                )

                st.plotly_chart(fig2, use_container_width=True)

                # Summary stats
                st.markdown("---")
                st.markdown(f"<h3 style='color:{colors.TEXT_PRIMARY};'>Summary</h3>", unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(
                        f"""
                        <div style="background:{colors.BG_SECONDARY}; padding:1rem; border-radius:8px;">
                            <h4 style="color:{colors.TEXT_PRIMARY};">Capital</h4>
                            <p style="color:{colors.TEXT_SECONDARY};">Initial: ${initial_capital:,.2f}</p>
                            <p style="color:{colors.TEXT_SECONDARY};">Final: ${float(final_value):,.2f}</p>
                            <p style="color:{colors.SUCCESS};">Profit: ${float(final_value - Decimal(str(initial_capital))):,.2f}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        f"""
                        <div style="background:{colors.BG_SECONDARY}; padding:1rem; border-radius:8px;">
                            <h4 style="color:{colors.TEXT_PRIMARY};">Performance</h4>
                            <p style="color:{colors.TEXT_SECONDARY};">Period: {len(historical)} days</p>
                            <p style="color:{colors.TEXT_SECONDARY};">Protocol: {protocol}</p>
                            <p style="color:{colors.TEXT_SECONDARY};">Asset: {asset} ({chain})</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.success("Historical backtest completed!")

            except Exception as e:
                st.error(f"Error during backtest: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def render_about_tab():
    st.markdown(
        f"""
        <h2 style="color:{colors.GRADIENT_PURPLE};">
            <ion-icon name="information" style="vertical-align:middle;"></ion-icon>
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
                <h3 style="color:{colors.GRADIENT_BLUE};"><ion-icon name="robot" style="vertical-align:middle;"></ion-icon> What is Yield Guard?</h3>
                <div style="color:{colors.TEXT_SECONDARY};font-size:1rem;line-height:1.8;margin-top:1rem;">
                    <div style="margin-bottom:1rem;">DeFi Yield Guard Bot is an intelligent treasury management system that automatically optimizes yield across multiple DeFi protocols while managing risk exposure.</div>
                    <div style="margin-bottom:0.5rem;"><strong style="color:{colors.GRADIENT_PURPLE};">Key Features:</strong></div>
                    <div style="margin-left:1.5rem;">
                        <div style="margin-bottom:0.5rem;"><ion-icon name="check-circle" style="color:{colors.GRADIENT_TEAL};"></ion-icon> Multi-protocol yield optimization (Aave, Compound, Morpho)</div>
                        <div style="margin-bottom:0.5rem;"><ion-icon name="check-circle" style="color:{colors.GRADIENT_TEAL};"></ion-icon> Automated risk management and rebalancing</div>
                        <div style="margin-bottom:0.5rem;"><ion-icon name="check-circle" style="color:{colors.GRADIENT_TEAL};"></ion-icon> Real-time portfolio monitoring and analytics</div>
                        <div style="margin-bottom:0.5rem;"><ion-icon name="check-circle" style="color:{colors.GRADIENT_TEAL};"></ion-icon> Historical backtesting and simulation</div>
                        <div><ion-icon name="check-circle" style="color:{colors.GRADIENT_TEAL};"></ion-icon> Gas-efficient transaction batching</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        protocols_html = f"""
        <div class="bento-item" style="margin-top:1rem;">
            <h3 style="color:{colors.GRADIENT_TEAL};">
                <ion-icon name="bank-outline" style="vertical-align:middle;"></ion-icon>
                Supported Protocols
            </h3>
            <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:1rem;margin-top:1.5rem;">
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};text-align:center;">
                    <ion-icon name="aave" style="font-size:2.5rem;color:{colors.GRADIENT_PURPLE};"></ion-icon>
                    <div style="color:{colors.TEXT_PRIMARY};font-weight:600;margin-top:0.5rem;">Aave V3</div>
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;">Lending Protocol</div>
                </div>
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};text-align:center;">
                    <ion-icon name="comp" style="font-size:2.5rem;color:{colors.GRADIENT_TEAL};"></ion-icon>
                    <div style="color:{colors.TEXT_PRIMARY};font-weight:600;margin-top:0.5rem;">Compound</div>
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;">Money Market</div>
                </div>
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};text-align:center;">
                    <ion-icon name="atom" style="font-size:2.5rem;color:{colors.GRADIENT_ORANGE};"></ion-icon>
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
                <h3 style="color:{colors.GRADIENT_ORANGE};"><ion-icon name="palette" style="vertical-align:middle;"></ion-icon> Design System</h3>
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
                <h3 style="color:{colors.GRADIENT_BLUE};"><ion-icon name="code-tags" style="vertical-align:middle;"></ion-icon> Tech Stack</h3>
                <div style="margin-top:1.5rem;color:{colors.TEXT_SECONDARY};font-size:0.9rem;line-height:1.8;">
                    <div><ion-icon name="language-python" style="color:{colors.GRADIENT_PURPLE};vertical-align:middle;"></ion-icon> Python 3.11+</div>
                    <div><ion-icon name="chart-line" style="color:{colors.GRADIENT_TEAL};vertical-align:middle;"></ion-icon> Streamlit</div>
                    <div><ion-icon name="database" style="color:{colors.GRADIENT_ORANGE};vertical-align:middle;"></ion-icon> SQLite</div>
                    <div><ion-icon name="chart-box" style="color:{colors.GRADIENT_BLUE};vertical-align:middle;"></ion-icon> Plotly</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div class="bento-item" style="margin-top:1rem;text-align:center;padding:2rem;">
            <div style="color:{colors.TEXT_TERTIARY};font-size:0.85rem;">Built with <ion-icon name="heart" style="color:{colors.ACCENT_RED};vertical-align:middle;"></ion-icon> for DeFi</div>
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
                <ion-icon name="shield-check"></ion-icon>
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
        avg_sharpe = round(stats[1] or 0, 2)
        # Sanitize Sharpe ratio to reasonable values
        if abs(avg_sharpe) > 100 or avg_sharpe != avg_sharpe:  # Check for > 100 or NaN
            avg_sharpe = 0
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
                <ion-icon name="lightning-bolt" style="vertical-align:middle;"></ion-icon>
                Quick Start
            </h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:2rem;">
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};">
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Total Simulations</div>
                    <div style="font-size:2rem;color:{colors.GRADIENT_PURPLE};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">{total_sims}</div>
                </div>
                <div style="background:{colors.BG_PRIMARY};padding:1.5rem;border-radius:12px;border:1px solid {colors.BORDER_PRIMARY};">
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Avg Sharpe</div>
                    <div style="font-size:2rem;color:{colors.GRADIENT_TEAL};font-family:JetBrains Mono,monospace;margin-top:0.5rem;">{format_number_eu(avg_sharpe, 2)}</div>
                    <div style="color:{colors.TEXT_TERTIARY};font-size:0.65rem;margin-top:0.5rem;font-style:italic;">
                        {'Low volatility simulations' if avg_sharpe == 0 else 'Risk-adjusted performance'}
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(quickstart_html, unsafe_allow_html=True)

    with col2:
        returns_html = f"""
        <div class="bento-item" style="height:350px;display:flex;flex-direction:column;justify-content:center;">
            <h3 style="color:{colors.GRADIENT_TEAL};">
                <ion-icon name="trending-up" style="vertical-align:middle;"></ion-icon>
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
                <ion-icon name="alert-circle-outline" style="vertical-align:middle;"></ion-icon>
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
                <ion-icon name="shield-check"></ion-icon>
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "RUN SIMULATION",
        "DASHBOARD",
        "HISTORICAL BACKTEST",
        "HISTORY",
        "ABOUT"
    ])

    with tab1:
        render_simulation_tab()
    with tab2:
        render_dashboard_tab()
    with tab3:
        render_historical_backtest_tab()
    with tab4:
        render_history_tab()
    with tab5:
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
