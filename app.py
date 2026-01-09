"""
Streamlit Dashboard for DeFi Yield Optimization Bot
Simple version that works with the existing database schema.
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import Config

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
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🗄️ Simulations", "ℹ️ About"])

    with tab1:
        render_dashboard_tab()

    with tab2:
        render_simulations_tab()

    with tab3:
        render_about_tab()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">Built with Streamlit | DeFi Yield Guard Bot v1.0</div>',
        unsafe_allow_html=True
    )


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
                avg_return = df['total_return'].mean()
                st.metric("Avg Total Return", f"{avg_return:.2f}%")

            with col3:
                avg_sharpe = df['sharpe_ratio'].mean()
                st.metric("Avg Sharpe Ratio", f"{avg_sharpe:.2f}")

            with col4:
                avg_drawdown = df['max_drawdown'].mean()
                st.metric("Avg Max Drawdown", f"{avg_drawdown:.2f}%")

            # Recent simulations table
            st.markdown("### 📋 Recent Simulations")

            display_df = df[[
                'id', 'strategy_name', 'initial_capital', 'final_value',
                'total_return', 'sharpe_ratio', 'created_at'
            ]].copy()

            display_df['initial_capital'] = display_df['initial_capital'].apply(lambda x: f"${x:,.0f}")
            display_df['final_value'] = display_df['final_value'].apply(lambda x: f"${x:,.2f}")
            display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x:.2f}%")
            display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.2f}")

            display_df.columns = [
                'ID', 'Strategy', 'Initial Capital', 'Final Value',
                'Total Return', 'Sharpe Ratio', 'Created At'
            ]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Performance chart
            st.markdown("### 📊 Returns Distribution")

            import plotly.express as px
            fig = px.histogram(
                df,
                x='total_return',
                nbins=20,
                labels={'total_return': 'Total Return (%)', 'count': 'Frequency'},
                title="Distribution of Simulation Returns"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No simulation data available yet. Run a simulation to see results!")

            st.markdown("""
            ### 🚀 Getting Started

            To run a simulation:

            1. Make sure you have configured your `.env` file with API keys
            2. Run the simulation from the command line:
               ```bash
               python -m src.services.simulation_service
               ```
            3. Results will be saved to the database and appear here

            For more information, see the **About** tab.
            """)

    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
    finally:
        conn.close()


def render_simulations_tab():
    """Render the simulations tab."""
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
            display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x:.2f}%")
            display_df['annualized_return'] = display_df['annualized_return'].apply(lambda x: f"{x:.2f}%")
            display_df['max_drawdown'] = display_df['max_drawdown'].apply(lambda x: f"{x:.2f}%")
            display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.2f}")

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Detailed view for selected simulation
            st.markdown("---")
            st.markdown("### 🔍 Simulation Details")

            sim_ids = df['id'].tolist()
            selected_id = st.selectbox("Select Simulation ID", sim_ids)

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
                    st.write(f"- **Total Return:** {sim_row['total_return']:.2f}%")
                    st.write(f"- **Annualized Return:** {sim_row['annualized_return']:.2f}%")
                    st.write(f"- **Max Drawdown:** {sim_row['max_drawdown']:.2f}%")
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
                    import plotly.graph_objects as go

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=snapshots_df['day'],
                        y=snapshots_df['net_value'],
                        mode='lines+markers',
                        name='Net Value',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=6)
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
                        fig2 = go.Figure()
                        fig2.add_trace(go.Scatter(
                            x=snapshots_df['day'],
                            y=snapshots_df['overall_health_factor'],
                            mode='lines+markers',
                            name='Health Factor',
                            line=dict(color='#2ca02c', width=2),
                            marker=dict(size=6)
                        ))

                        fig2.update_layout(
                            title="Health Factor Over Time",
                            xaxis_title="Day",
                            yaxis_title="Health Factor",
                            hovermode='x unified',
                            height=400
                        )

                        st.plotly_chart(fig2, use_container_width=True)

                    # Snapshots table
                    st.markdown("#### Snapshot Data")
                    display_snapshots = snapshots_df.copy()
                    display_snapshots['net_value'] = display_snapshots['net_value'].apply(lambda x: f"${x:,.2f}")
                    display_snapshots['total_collateral'] = display_snapshots['total_collateral'].apply(lambda x: f"${x:,.2f}")
                    display_snapshots['total_debt'] = display_snapshots['total_debt'].apply(lambda x: f"${x:,.2f}")
                    display_snapshots['cumulative_yield'] = display_snapshots['cumulative_yield'].apply(lambda x: f"${x:,.2f}")

                    if 'overall_health_factor' in display_snapshots.columns:
                        display_snapshots['overall_health_factor'] = display_snapshots['overall_health_factor'].apply(
                            lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                        )

                    st.dataframe(display_snapshots, use_container_width=True, hide_index=True)

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
    including Aave and Morpho.

    ### Features

    - **Multi-Protocol Support**: Compare and optimize across Aave, Morpho, and other DeFi protocols
    - **Risk Management**: Automated health factor monitoring and rebalancing
    - **Historical Analysis**: Backtest strategies using historical market data
    - **Performance Metrics**: Track returns, Sharpe ratios, drawdowns, and more
    - **SQLite Database**: Persistent storage of simulation results
    - **Interactive Dashboard**: Visualize and analyze simulation results

    ### Running Simulations

    To run simulations, use the command line tools in the `src/services` directory:

    ```bash
    # Run a simulation
    python -m src.services.simulation_service

    # Analyze results
    python -m src.analytics.performance_metrics
    ```

    ### Database Schema

    **simulation_runs table:**
    - id, strategy_name, initial_capital, simulation_days
    - protocols_used, total_return, annualized_return
    - max_drawdown, sharpe_ratio, final_value, created_at

    **portfolio_snapshots table:**
    - id, simulation_id, day, net_value
    - total_collateral, total_debt, overall_health_factor
    - cumulative_yield, timestamp

    ### Configuration

    Configure the bot using environment variables in `.env`:
    - `DATABASE_URL`: Database connection string
    - `AAVE_API_KEY`, `COMPOUND_API_KEY`: Protocol API keys
    - `ETHEREUM_RPC_URL`, `POLYGON_RPC_URL`: Blockchain RPC endpoints

    ### Learn More

    - [GitHub Repository](https://github.com/Enricrypto/yield-guard-bot)
    - [Documentation](README.md)
    """)


if __name__ == "__main__":
    main()
