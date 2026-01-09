"""
Streamlit Dashboard for DeFi Yield Optimization Bot

Interactive web interface integrated with TreasurySimulator for running
simulations, viewing analytics, and querying historical results.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from decimal import Decimal
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

# Page configuration
st.set_page_config(
    page_title="DeFi Yield Guard Bot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = Config()
    if 'last_simulation_id' not in st.session_state:
        st.session_state.last_simulation_id = None


def get_db_connection():
    """Get database connection."""
    config = st.session_state.config
    return sqlite3.connect(config.database_path)


def main():
    """Main application."""
    initialize_session_state()

    # Header
    st.markdown("# 🛡️ DeFi Yield Guard Bot")
    st.markdown("**Intelligent yield optimization with automated risk management**")
    st.markdown("---")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Run Simulation", "📊 Dashboard", "🗄️ History", "ℹ️ About"])

    with tab1:
        render_simulation_tab()

    with tab2:
        render_dashboard_tab()

    with tab3:
        render_history_tab()

    with tab4:
        render_about_tab()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">Built with Streamlit | DeFi Yield Guard Bot v1.0</div>',
        unsafe_allow_html=True
    )


def render_simulation_tab():
    """Render the simulation tab with live simulation capabilities."""
    st.markdown("## 🚀 Run New Simulation")

    st.markdown("""
    Configure and run a new yield optimization simulation using the TreasurySimulator engine.
    The simulator will backtest your strategy across multiple days using synthetic market data.
    """)

    st.markdown("---")

    # Configuration columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💰 Portfolio Settings")

        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=10000.0,
            max_value=100000000.0,
            value=1000000.0,
            step=10000.0,
            help="Starting capital for the simulation"
        )

        strategy_name = st.text_input(
            "Strategy Name",
            value=f"Simulation {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Name to identify this simulation"
        )

        min_health_factor = st.slider(
            "Minimum Health Factor",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            help="Minimum acceptable health factor for positions"
        )

    with col2:
        st.markdown("### 📊 Simulation Parameters")

        simulation_days = st.number_input(
            "Simulation Days",
            min_value=7,
            max_value=365,
            value=180,
            step=1,
            help="Number of days to simulate"
        )

        market_regime = st.selectbox(
            "Market Regime",
            options=["normal", "bull", "bear", "volatile"],
            index=0,
            help="Market conditions for synthetic data generation"
        )

        random_seed = st.number_input(
            "Random Seed (optional)",
            min_value=0,
            max_value=99999,
            value=42,
            step=1,
            help="Seed for reproducible results"
        )

    st.markdown("---")
    st.markdown("### 🎯 Protocol Allocation")

    col1, col2 = st.columns(2)

    with col1:
        aave_allocation = st.slider(
            "Aave V3 Allocation (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="Percentage of capital to allocate to Aave V3"
        )

    with col2:
        morpho_allocation = 100 - aave_allocation
        st.metric("Morpho Allocation (%)", f"{morpho_allocation}%")

    # Run simulation button
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        run_button = st.button(
            "▶️ Run Simulation",
            type="primary",
            use_container_width=True
        )

    if run_button:
        run_simulation_process(
            initial_capital=initial_capital,
            strategy_name=strategy_name,
            min_health_factor=min_health_factor,
            simulation_days=simulation_days,
            market_regime=market_regime,
            random_seed=random_seed,
            aave_allocation=aave_allocation / 100,
            morpho_allocation=morpho_allocation / 100
        )


def run_simulation_process(
    initial_capital: float,
    strategy_name: str,
    min_health_factor: float,
    simulation_days: int,
    market_regime: str,
    random_seed: int,
    aave_allocation: float,
    morpho_allocation: float
):
    """Execute the simulation using TreasurySimulator."""
    progress_bar = st.progress(0, text="Initializing simulation...")

    try:
        # Step 1: Initialize Treasury Simulator
        progress_bar.progress(10, text="Initializing treasury simulator...")

        treasury = TreasurySimulator(
            initial_capital=Decimal(str(initial_capital)),
            name=strategy_name,
            min_health_factor=Decimal(str(min_health_factor))
        )

        # Step 2: Add positions
        progress_bar.progress(20, text="Setting up initial positions...")

        if aave_allocation > 0:
            treasury.deposit(
                protocol='aave-v3',
                asset_symbol='USDC',
                amount=Decimal(str(initial_capital * aave_allocation)),
                supply_apy=Decimal('0.05'),
                borrow_apy=Decimal('0.07'),
                ltv=Decimal('0.80'),
                liquidation_threshold=Decimal('0.85')
            )

        if morpho_allocation > 0:
            treasury.deposit(
                protocol='morpho',
                asset_symbol='USDC',
                amount=Decimal(str(initial_capital * morpho_allocation)),
                supply_apy=Decimal('0.06'),
                borrow_apy=Decimal('0.075'),
                ltv=Decimal('0.80'),
                liquidation_threshold=Decimal('0.85')
            )

        # Step 3: Generate market data
        progress_bar.progress(30, text="Generating market data...")

        generator = SyntheticDataGenerator(seed=random_seed)
        market_snapshots = generator.generate_timeseries(
            days=simulation_days,
            asset_symbol='USDC',
            market_regime=market_regime
        )

        def market_data_generator(day_index: int):
            """Provide daily market rates."""
            if day_index < len(market_snapshots):
                snapshot = market_snapshots[day_index]
                return {
                    'aave-v3': {
                        'USDC': {
                            'supply_apy': snapshot.aave_supply_apy,
                            'borrow_apy': snapshot.aave_borrow_apy
                        }
                    },
                    'morpho': {
                        'USDC': {
                            'supply_apy': snapshot.morpho_supply_apy,
                            'borrow_apy': snapshot.morpho_borrow_apy
                        }
                    }
                }
            return None

        # Step 4: Run simulation
        progress_bar.progress(40, text="Running simulation...")

        snapshots = treasury.run_simulation(
            days=simulation_days,
            market_data_generator=market_data_generator
        )

        progress_bar.progress(70, text="Calculating performance metrics...")

        # Step 5: Calculate performance metrics
        portfolio_values = [Decimal(str(initial_capital))] + [s.net_value for s in snapshots]

        metrics_calc = PerformanceMetrics(risk_free_rate=Decimal('0.04'))
        metrics = metrics_calc.calculate_all_metrics(
            portfolio_values=portfolio_values,
            days=simulation_days
        )

        # Step 6: Save to database
        progress_bar.progress(85, text="Saving results to database...")

        db = DatabaseManager(st.session_state.config.database_path)
        db.init_db()

        # Determine protocols used
        protocols_used = []
        if aave_allocation > 0:
            protocols_used.append('aave-v3')
        if morpho_allocation > 0:
            protocols_used.append('morpho')

        sim_run = SimulationRun(
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            simulation_days=simulation_days,
            protocols_used=','.join(protocols_used),
            total_return=float(metrics['total_return']),
            annualized_return=float(metrics['annualized_return']),
            max_drawdown=float(metrics['max_drawdown']),
            sharpe_ratio=float(metrics['sharpe_ratio']),
            final_value=float(portfolio_values[-1]),
            created_at=datetime.now()
        )

        sim_id = db.save_simulation_run(sim_run)

        # Save snapshots
        for i, snapshot in enumerate(snapshots):
            hf = snapshot.overall_health_factor
            hf_value = None if hf == Decimal('Infinity') or hf is None else float(hf)

            ps = PortfolioSnapshot(
                simulation_id=sim_id,
                day=i + 1,
                net_value=float(snapshot.net_value),
                total_collateral=float(snapshot.total_collateral),
                total_debt=float(snapshot.total_debt),
                overall_health_factor=hf_value,
                cumulative_yield=float(snapshot.cumulative_yield),
                timestamp=snapshot.timestamp
            )
            db.save_portfolio_snapshot(ps)

        progress_bar.progress(100, text="Complete!")
        st.session_state.last_simulation_id = sim_id

        # Display results
        st.success(f"✅ Simulation completed successfully! (ID: {sim_id})")

        st.markdown("---")
        st.markdown("### 📈 Results Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            final_value = float(portfolio_values[-1])
            profit = final_value - initial_capital
            st.metric("Final Value", f"${final_value:,.0f}", f"${profit:,.0f}")

        with col2:
            total_return_pct = float(metrics['total_return']) * 100
            st.metric("Total Return", f"{total_return_pct:.2f}%")

        with col3:
            max_drawdown_pct = float(metrics['max_drawdown']) * 100
            st.metric("Max Drawdown", f"{max_drawdown_pct:.2f}%")

        with col4:
            sharpe = float(metrics['sharpe_ratio'])
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")

        # Plot portfolio value
        st.markdown("### 💼 Portfolio Value Over Time")

        days_range = list(range(len(portfolio_values)))
        values = [float(v) for v in portfolio_values]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days_range,
            y=values,
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4)
        ))

        fig.update_layout(
            xaxis_title="Day",
            yaxis_title="Value ($)",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 View detailed analytics in the Dashboard and History tabs")

    except Exception as e:
        st.error(f"❌ Simulation failed: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
    finally:
        progress_bar.empty()


def render_dashboard_tab():
    """Render the main dashboard tab."""
    st.markdown("## 📈 Performance Overview")

    conn = get_db_connection()

    try:
        # Get simulation count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM simulation_runs")
        total_sims = cursor.fetchone()[0]

        # Get recent simulations
        cursor.execute("""
            SELECT * FROM simulation_runs
            ORDER BY created_at DESC
            LIMIT 10
        """)

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        if rows:
            df = pd.DataFrame(rows, columns=columns)

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Simulations", total_sims)

            with col2:
                avg_return = df['total_return'].mean() * 100
                st.metric("Avg Total Return", f"{avg_return:.2f}%")

            with col3:
                avg_sharpe = df['sharpe_ratio'].mean()
                st.metric("Avg Sharpe Ratio", f"{avg_sharpe:.2f}")

            with col4:
                avg_drawdown = df['max_drawdown'].mean() * 100
                st.metric("Avg Max Drawdown", f"{avg_drawdown:.2f}%")

            # Recent simulations table
            st.markdown("---")
            st.markdown("### 📋 Recent Simulations")

            display_df = df[[
                'id', 'strategy_name', 'initial_capital', 'final_value',
                'total_return', 'sharpe_ratio', 'created_at'
            ]].copy()

            display_df['initial_capital'] = display_df['initial_capital'].apply(lambda x: f"${x:,.0f}")
            display_df['final_value'] = display_df['final_value'].apply(lambda x: f"${x:,.2f}")
            display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x*100:.2f}%")
            display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.2f}")

            display_df.columns = [
                'ID', 'Strategy', 'Initial Capital', 'Final Value',
                'Total Return', 'Sharpe Ratio', 'Created At'
            ]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Performance chart
            st.markdown("---")
            st.markdown("### 📊 Returns Distribution")

            fig = px.histogram(
                df,
                x=df['total_return'] * 100,
                nbins=20,
                labels={'x': 'Total Return (%)', 'y': 'Frequency'},
                title="Distribution of Simulation Returns"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No simulation data available yet. Run a simulation in the '🚀 Run Simulation' tab!")

    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
    finally:
        conn.close()


def render_history_tab():
    """Render the simulations history tab."""
    st.markdown("## 🗄️ Simulation History")

    conn = get_db_connection()

    try:
        # Filter options
        col1, col2 = st.columns(2)

        with col1:
            sort_options = {
                "Newest First": "created_at DESC",
                "Oldest First": "created_at ASC",
                "Highest Return": "total_return DESC",
                "Lowest Return": "total_return ASC",
                "Highest Sharpe": "sharpe_ratio DESC"
            }
            sort_by = st.selectbox("Sort By", list(sort_options.keys()))

        with col2:
            limit = st.number_input("Show Results", min_value=10, max_value=1000, value=50, step=10)

        # Get simulations
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM simulation_runs
            ORDER BY {sort_options[sort_by]}
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        if rows:
            df = pd.DataFrame(rows, columns=columns)

            st.markdown(f"**Showing {len(df)} simulations**")

            # Detailed table
            display_df = df.copy()
            display_df['initial_capital'] = display_df['initial_capital'].apply(lambda x: f"${x:,.0f}")
            display_df['final_value'] = display_df['final_value'].apply(lambda x: f"${x:,.2f}")
            display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x*100:.2f}%")
            display_df['annualized_return'] = display_df['annualized_return'].apply(lambda x: f"{x*100:.2f}%")
            display_df['max_drawdown'] = display_df['max_drawdown'].apply(lambda x: f"{x*100:.2f}%")
            display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.2f}")

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Detailed view for selected simulation
            st.markdown("---")
            st.markdown("### 🔍 Simulation Details")

            sim_ids = df['id'].tolist()
            selected_id = st.selectbox("Select Simulation ID", sim_ids, index=0 if st.session_state.last_simulation_id is None else (sim_ids.index(st.session_state.last_simulation_id) if st.session_state.last_simulation_id in sim_ids else 0))

            if selected_id:
                # Get simulation details
                sim_row = df[df['id'] == selected_id].iloc[0]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Simulation Info**")
                    st.write(f"- **ID:** {sim_row['id']}")
                    st.write(f"- **Strategy:** {sim_row['strategy_name']}")
                    st.write(f"- **Created:** {sim_row['created_at']}")
                    st.write(f"- **Simulation Days:** {sim_row['simulation_days']}")
                    st.write(f"- **Protocols Used:** {sim_row['protocols_used']}")

                with col2:
                    st.markdown("**Performance Metrics**")
                    st.write(f"- **Initial Capital:** ${sim_row['initial_capital']:,.0f}")
                    st.write(f"- **Final Value:** ${sim_row['final_value']:,.2f}")
                    st.write(f"- **Total Return:** {sim_row['total_return']*100:.2f}%")
                    st.write(f"- **Annualized Return:** {sim_row['annualized_return']*100:.2f}%")
                    st.write(f"- **Max Drawdown:** {sim_row['max_drawdown']*100:.2f}%")
                    st.write(f"- **Sharpe Ratio:** {sim_row['sharpe_ratio']:.2f}")

                # Get snapshots
                cursor.execute("""
                    SELECT * FROM portfolio_snapshots
                    WHERE simulation_id = ?
                    ORDER BY day ASC
                """, (selected_id,))

                snapshot_rows = cursor.fetchall()
                snapshot_columns = [description[0] for description in cursor.description]

                if snapshot_rows:
                    snapshots_df = pd.DataFrame(snapshot_rows, columns=snapshot_columns)

                    st.markdown("---")
                    st.markdown("### 📸 Portfolio Snapshots")

                    # Portfolio value chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=snapshots_df['day'],
                        y=snapshots_df['net_value'],
                        mode='lines+markers',
                        name='Net Value',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=4)
                    ))

                    fig.update_layout(
                        title="Portfolio Value Over Time",
                        xaxis_title="Day",
                        yaxis_title="Value ($)",
                        hovermode='x unified',
                        height=400
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Health factor chart (if available)
                    if 'overall_health_factor' in snapshots_df.columns:
                        # Filter out None values for health factor
                        hf_df = snapshots_df[snapshots_df['overall_health_factor'].notna()].copy()

                        if len(hf_df) > 0:
                            fig2 = go.Figure()
                            fig2.add_trace(go.Scatter(
                                x=hf_df['day'],
                                y=hf_df['overall_health_factor'],
                                mode='lines+markers',
                                name='Health Factor',
                                line=dict(color='#2ca02c', width=2),
                                marker=dict(size=4)
                            ))

                            fig2.add_hline(
                                y=1.5,
                                line_dash="dash",
                                line_color="red",
                                annotation_text="Min Threshold"
                            )

                            fig2.update_layout(
                                title="Health Factor Over Time",
                                xaxis_title="Day",
                                yaxis_title="Health Factor",
                                hovermode='x unified',
                                height=400
                            )

                            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("No simulations found.")

    except Exception as e:
        st.error(f"Error loading simulations: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
    finally:
        conn.close()


def render_about_tab():
    """Render the about tab."""
    st.markdown("## ℹ️ About DeFi Yield Guard Bot")

    st.markdown("""
    ### Overview

    The DeFi Yield Guard Bot is an intelligent yield optimization system with automated risk management
    for DeFi lending protocols. It simulates and optimizes portfolio strategies across multiple protocols
    including Aave and Morpho using the **TreasurySimulator** engine.

    ### Features

    - **Live Simulation Engine**: Run backtests directly from the dashboard using TreasurySimulator
    - **Multi-Protocol Support**: Compare and optimize across Aave V3 and Morpho protocols
    - **Risk Management**: Automated health factor monitoring and position management
    - **Synthetic Market Data**: Generate realistic market conditions for testing strategies
    - **Performance Analytics**: Track returns, Sharpe ratios, drawdowns, and more
    - **SQLite Database**: Persistent storage of all simulation results
    - **Interactive Visualizations**: Portfolio value and health factor charts

    ### How to Use

    1. **Run Simulation Tab**: Configure and execute new simulations with custom parameters
    2. **Dashboard Tab**: View aggregated performance metrics across all simulations
    3. **History Tab**: Browse and analyze individual simulation results in detail

    ### Architecture

    **Core Components:**
    - `TreasurySimulator`: Main simulation engine for portfolio management
    - `SyntheticDataGenerator`: Generates realistic market data for testing
    - `PerformanceMetrics`: Calculates comprehensive performance statistics
    - `DatabaseManager`: Handles SQLite persistence

    **Database Schema:**

    - **simulation_runs**: Stores simulation configurations and results
    - **portfolio_snapshots**: Daily snapshots of portfolio state during simulations

    ### Configuration

    Configure the bot using environment variables in `.env`:
    - `DATABASE_URL`: Database connection string (default: sqlite:///data/simulations.db)
    - `AAVE_API_KEY`, `COMPOUND_API_KEY`: Protocol API keys (optional for live data)
    - `ETHEREUM_RPC_URL`, `POLYGON_RPC_URL`: Blockchain RPC endpoints (optional)

    ### Learn More

    - [GitHub Repository](https://github.com/Enricrypto/yield-guard-bot)
    - [Documentation](README.md)

    ### Version

    **DeFi Yield Guard Bot v1.0**
    Built with Streamlit, TreasurySimulator, and Python 3.14
    """)


if __name__ == "__main__":
    main()
