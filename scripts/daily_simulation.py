#!/usr/bin/env python3
"""
Daily Simulation Script
Automated script for running treasury simulations and saving results to database

This script:
1. Initializes the database
2. Fetches current market data from DeFi protocols
3. Creates/loads treasury portfolios for each risk tier
4. Runs simulations
5. Saves results to database
6. Generates performance reports

Designed to be run daily via cron or manual execution.
"""

import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db import DatabaseManager, SimulationRun, PortfolioSnapshot
from src.market_data.historical_fetcher import HistoricalDataFetcher
from src.market_data.risk_parameter_fetcher import get_risk_parameters_for_simulation
from src.simulator.treasury_simulator import TreasurySimulator
from src.analytics.performance_metrics import PerformanceMetrics


def print_header(text: str, char: str = "="):
    """Print formatted header"""
    print(f"\n{char * 70}")
    print(f"{text:^70}")
    print(f"{char * 70}\n")


def print_section(text: str):
    """Print formatted section"""
    print(f"\n{'-' * 70}")
    print(text)
    print(f"{'-' * 70}\n")


def fetch_current_market_data(protocols: list, asset: str = 'USDC') -> dict:
    """
    Fetch current market data for specified protocols

    Args:
        protocols: List of protocol names (e.g., ['aave-v3', 'compound-v3'])
        asset: Asset symbol (default: 'USDC')

    Returns:
        Dictionary with market data for each protocol
    """
    print_section(f"Fetching Current Market Data for {asset}")

    fetcher = HistoricalDataFetcher()
    market_data = {}

    for protocol in protocols:
        print(f"  Fetching {protocol} {asset} data...")

        # Get last 7 days to get current rates
        historical = fetcher.get_historical_data_for_backtest(
            protocol=protocol,
            asset_symbol=asset,
            chain='Ethereum',
            days_back=7
        )

        if historical and len(historical) > 0:
            # Use most recent data point
            latest = historical[-1]
            market_data[protocol] = {
                'supply_apy': latest.apy,
                'timestamp': latest.timestamp
            }
            print(f"  ✓ {protocol}: {latest.apy*100:.2f}% APY (as of {latest.timestamp.date()})")
        else:
            print(f"  ✗ No data available for {protocol}")

    return market_data


def run_conservative_simulation(
    db: DatabaseManager,
    initial_capital: Decimal = Decimal('1000000'),
    days: int = 1
) -> dict:
    """
    Run conservative strategy simulation

    Conservative Strategy:
    - Stablecoins only (USDC)
    - No leverage (lending only)
    - Diversified across Aave V3, Compound V3, Morpho
    - Equal weight allocation

    Args:
        db: Database manager
        initial_capital: Starting capital
        days: Number of days to simulate

    Returns:
        Dictionary with simulation results
    """
    print_header("CONSERVATIVE STRATEGY SIMULATION")

    strategy_name = "Conservative"
    protocols = ['aave-v3', 'compound-v3', 'morpho-v1']

    # Fetch current market data
    market_data = fetch_current_market_data(protocols)

    if not market_data:
        print("❌ No market data available. Cannot run simulation.")
        return {}

    # Create treasury
    treasury = TreasurySimulator(
        initial_capital=initial_capital,
        name=strategy_name,
        min_health_factor=Decimal('2.0')
    )

    # Equal allocation across protocols
    # Account for gas fees: $15 per deposit transaction
    gas_fee_per_deposit = Decimal('15.00')
    total_gas_fees = gas_fee_per_deposit * len(market_data)
    capital_after_gas = initial_capital - total_gas_fees
    allocation_per_protocol = capital_after_gas / len(market_data)

    print_section("Opening Positions")
    print(f"Diversifying ${initial_capital:,.0f} across {len(market_data)} protocol(s)")
    print(f"Total gas fees: ${total_gas_fees:,.0f} ({len(market_data)} × ${gas_fee_per_deposit})")
    print(f"Capital after gas: ${capital_after_gas:,.0f}")
    print(f"Allocation per protocol: ${allocation_per_protocol:,.0f}\n")

    for protocol, data in market_data.items():
        # Fetch current risk parameters
        risk_params = get_risk_parameters_for_simulation(
            protocol=protocol,
            asset_symbol='USDC',
            start_date=datetime.now(),
            days=1,
            network='mainnet'
        )
        _, liq_threshold = risk_params[0]

        treasury.deposit(
            protocol=protocol,
            asset_symbol='USDC',
            amount=allocation_per_protocol,
            supply_apy=data['supply_apy'],
            borrow_apy=Decimal('0'),  # No borrowing
            ltv=Decimal('0'),  # No leverage
            liquidation_threshold=liq_threshold
        )

        print(f"  ✓ {protocol}: ${allocation_per_protocol:,.0f} at {data['supply_apy']*100:.2f}% APY")

    # Run simulation
    print_section(f"Running {days}-Day Simulation")

    def market_data_generator(day_index: int) -> dict:
        """Generate static market data (using current rates)"""
        result = {}
        for protocol, data in market_data.items():
            result[protocol] = {
                'USDC': {
                    'supply_apy': data['supply_apy'],
                    'borrow_apy': Decimal('0')
                }
            }
        return result

    snapshots = treasury.run_simulation(
        days=days,
        market_data_generator=market_data_generator
    )

    print(f"✓ Simulation complete: {len(snapshots)} days")

    # Calculate metrics
    print_section("Performance Metrics")

    metrics_calc = PerformanceMetrics(risk_free_rate=Decimal('0.04'))
    portfolio_values = [initial_capital] + [s.net_value for s in snapshots]

    metrics = metrics_calc.calculate_all_metrics(
        portfolio_values=portfolio_values,
        days=days
    )

    print(f"  Initial Value:     ${metrics['initial_value']:,.2f}")
    print(f"  Final Value:       ${metrics['final_value']:,.2f}")
    print(f"  Total Return:      {metrics['total_return_pct']:.4f}%")
    print(f"  Daily Return:      {metrics['total_return_pct']/days:.4f}%")
    print(f"  Max Drawdown:      {metrics['max_drawdown_pct']:.4f}%")

    # Save to database
    print_section("Saving to Database")

    simulation_run = SimulationRun(
        strategy_name=strategy_name,
        initial_capital=float(initial_capital),
        simulation_days=days,
        protocols_used=','.join(market_data.keys()),
        total_return=float(metrics['total_return']),
        annualized_return=float(metrics['annualized_return']),
        max_drawdown=float(metrics['max_drawdown']),
        sharpe_ratio=float(metrics['sharpe_ratio']),
        final_value=float(metrics['final_value']),
        created_at=datetime.now()
    )

    simulation_id = db.save_simulation_run(simulation_run)
    print(f"✓ Simulation run saved (ID: {simulation_id})")

    # Save snapshots
    for i, snapshot in enumerate(snapshots):
        portfolio_snapshot = PortfolioSnapshot(
            simulation_id=simulation_id,
            day=i + 1,
            net_value=float(snapshot.net_value),
            total_collateral=float(snapshot.total_collateral),
            total_debt=float(snapshot.total_debt),
            overall_health_factor=float(snapshot.overall_health_factor) if snapshot.overall_health_factor != Decimal('Infinity') else None,
            cumulative_yield=float(snapshot.cumulative_yield),
            timestamp=snapshot.timestamp
        )
        db.save_portfolio_snapshot(portfolio_snapshot)

    print(f"✓ {len(snapshots)} portfolio snapshots saved")

    return {
        'strategy': strategy_name,
        'simulation_id': simulation_id,
        'metrics': metrics,
        'snapshots': snapshots
    }


def generate_summary_report(db: DatabaseManager, limit: int = 5):
    """
    Generate summary report of recent simulations

    Args:
        db: Database manager
        limit: Number of recent simulations to show
    """
    print_header("RECENT SIMULATIONS SUMMARY")

    recent = db.get_recent_simulations(limit=limit)

    if not recent:
        print("No simulations found in database.")
        return

    print(f"Showing last {len(recent)} simulation(s):\n")

    for sim in recent:
        print(f"Strategy: {sim.strategy_name}")
        print(f"  Date: {sim.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Capital: ${sim.initial_capital:,.0f}")
        print(f"  Days: {sim.simulation_days}")
        print(f"  Return: {sim.total_return*100:.4f}%")
        print(f"  Annualized: {sim.annualized_return*100:.2f}%")
        print(f"  Max Drawdown: {sim.max_drawdown*100:.4f}%")
        print(f"  Sharpe Ratio: {sim.sharpe_ratio:.2f}")
        print(f"  Final Value: ${sim.final_value:,.2f}")
        print()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Run daily treasury simulation')
    parser.add_argument('--capital', type=float, default=1000000,
                      help='Initial capital (default: 1000000)')
    parser.add_argument('--days', type=int, default=1,
                      help='Number of days to simulate (default: 1)')
    parser.add_argument('--db-path', type=str, default='data/simulations.db',
                      help='Database path (default: data/simulations.db)')
    parser.add_argument('--summary-only', action='store_true',
                      help='Only show summary of recent simulations')

    args = parser.parse_args()

    print_header("DAILY SIMULATION SCRIPT", "=")
    print(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {args.db_path}")

    # Initialize database
    print_section("Initializing Database")
    db = DatabaseManager(args.db_path)
    db.init_db()
    print(f"✓ Database initialized at {args.db_path}")

    # If summary only, just show report and exit
    if args.summary_only:
        generate_summary_report(db, limit=10)
        return

    try:
        # Run conservative simulation
        result = run_conservative_simulation(
            db=db,
            initial_capital=Decimal(str(args.capital)),
            days=args.days
        )

        if result:
            print_header("SIMULATION COMPLETE", "=")
            print(f"✓ Conservative strategy simulation completed successfully")
            print(f"  Simulation ID: {result['simulation_id']}")
            print(f"  Final Value: ${result['metrics']['final_value']:,.2f}")
            print(f"  Return: {result['metrics']['total_return_pct']:.4f}%")

        # Show summary
        generate_summary_report(db, limit=5)

    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print_header("SCRIPT COMPLETE", "=")


if __name__ == "__main__":
    main()
