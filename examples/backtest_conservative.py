#!/usr/bin/env python3
"""
Conservative Strategy Backtesting
Tests the conservative tier strategy with real historical data from multiple protocols

Strategy Specifications (from conservative tier):
- Risk Level: Low
- Asset Preferences: Stablecoins (USDC, DAI)
- Protocols: Aave V3, Compound V3, Morpho
- Max Drawdown: 10%
- Stop Loss: 5%
- No leverage (lending only, no borrowing)
- Diversification across protocols to reduce smart contract risk
"""

import sys
from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime

from src.market_data.historical_fetcher import HistoricalDataFetcher, HistoricalYield
from src.market_data.risk_parameter_fetcher import get_risk_parameters_for_simulation
from src.simulator.treasury_simulator import TreasurySimulator, PortfolioSnapshot
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


def fetch_protocol_data(
    fetcher: HistoricalDataFetcher,
    protocol: str,
    asset: str,
    days_back: int = 90
) -> Optional[List[HistoricalYield]]:
    """
    Fetch historical data for a protocol/asset pair

    Args:
        fetcher: HistoricalDataFetcher instance
        protocol: Protocol name (e.g., 'aave-v3', 'compound-v3', 'morpho-aave-v3')
        asset: Asset symbol (e.g., 'USDC', 'DAI')
        days_back: Number of days of history

    Returns:
        List of historical yield data
    """
    print(f"  Fetching {protocol} {asset} data...")

    historical = fetcher.get_historical_data_for_backtest(
        protocol=protocol,
        asset_symbol=asset,
        chain='Ethereum',
        days_back=days_back
    )

    if historical:
        apys = [float(h.apy * 100) for h in historical]
        print(f"  ✓ Retrieved {len(historical)} data points")
        print(f"    Date range: {historical[0].timestamp.date()} to {historical[-1].timestamp.date()}")
        print(f"    APY range: {min(apys):.2f}% - {max(apys):.2f}%")
        print(f"    Average APY: {sum(apys)/len(apys):.2f}%")
        return historical
    else:
        print(f"  ✗ No data available for {protocol} {asset}")
        return None


def backtest_conservative_strategy(
    initial_capital: Decimal = Decimal('1000000'),
    days_back: int = 90
) -> Dict:
    """
    Backtest the conservative strategy with real historical data

    Conservative Strategy:
    - Diversify across Aave V3, Compound V3, and Morpho
    - Use only stablecoins (USDC)
    - No leverage (lending only)
    - Equal weight allocation (33.3% each protocol)
    - Focus on capital preservation and consistent returns

    Args:
        initial_capital: Starting capital
        days_back: Number of days to backtest

    Returns:
        Dictionary with backtest results
    """
    print_header("CONSERVATIVE STRATEGY BACKTEST")

    print("Strategy Configuration:")
    print(f"  Risk Level: Low (Conservative)")
    print(f"  Initial Capital: ${initial_capital:,.0f}")
    print(f"  Asset: USDC (Stablecoin)")
    print(f"  Protocols: Aave V3, Compound V3, Morpho")
    print(f"  Allocation: 33.3% per protocol (diversification)")
    print(f"  Leverage: None (lending only)")
    print(f"  Max Drawdown Constraint: 10%")
    print(f"  Period: Last {days_back} days")

    # Initialize fetcher
    fetcher = HistoricalDataFetcher()

    print_section("STEP 1: Fetching Historical Data")

    # Fetch data for all three protocols
    protocols_data = {}

    # Aave V3
    aave_data = fetch_protocol_data(fetcher, 'aave-v3', 'USDC', days_back)
    if aave_data:
        protocols_data['aave-v3'] = aave_data

    # Compound V3
    compound_data = fetch_protocol_data(fetcher, 'compound-v3', 'USDC', days_back)
    if compound_data:
        protocols_data['compound-v3'] = compound_data

    # Morpho (now called morpho-v1 in DefiLlama)
    morpho_data = fetch_protocol_data(fetcher, 'morpho-v1', 'USDC', days_back)
    if morpho_data:
        protocols_data['morpho-v1'] = morpho_data

    if not protocols_data:
        print("\n❌ No data available for any protocol. Cannot run backtest.")
        return {}

    print(f"\n✓ Successfully fetched data for {len(protocols_data)} protocol(s)")

    # Fetch historical risk parameters for Aave V3 (other protocols use defaults)
    print("\nFetching historical risk parameters...")

    # Calculate simulation start date from the first data point
    start_date = datetime.now()  # Default to now
    for data in protocols_data.values():
        if data:
            start_date = data[0].timestamp
            break

    # Get risk parameters for each protocol
    risk_parameters_by_protocol = {}
    for protocol in protocols_data.keys():
        risk_params = get_risk_parameters_for_simulation(
            protocol=protocol,
            asset_symbol='USDC',
            start_date=start_date,
            days=days_back,
            network='mainnet'
        )
        risk_parameters_by_protocol[protocol] = risk_params

        # Show if parameters change during simulation
        unique_params = set(risk_params.values())
        if len(unique_params) > 1:
            print(f"  {protocol}: Risk parameters change {len(unique_params) - 1} time(s)")
        else:
            ltv, liq_threshold = list(unique_params)[0]
            print(f"  {protocol}: Static parameters (LTV={ltv*100:.1f}%, Threshold={liq_threshold*100:.1f}%)")

    print_section("STEP 2: Portfolio Construction")

    # Calculate allocation per protocol
    num_protocols = len(protocols_data)
    allocation_per_protocol = initial_capital / num_protocols

    print(f"Diversifying across {num_protocols} protocol(s):")
    for protocol in protocols_data.keys():
        pct = (allocation_per_protocol / initial_capital) * 100
        print(f"  {protocol}: ${allocation_per_protocol:,.0f} ({pct:.1f}%)")

    print_section("STEP 3: Running Simulation")

    # Initialize treasury
    treasury = TreasurySimulator(
        initial_capital=initial_capital,
        name="Conservative Strategy",
        min_health_factor=Decimal('2.0')  # Conservative: higher safety margin
    )

    # Open positions in each protocol
    print("Opening positions...")
    for protocol, data in protocols_data.items():
        # Use first data point's APY as initial rate
        initial_apy = data[0].apy

        # Get initial risk parameters for day 0
        initial_ltv, initial_liq_threshold = risk_parameters_by_protocol[protocol][0]

        position = treasury.deposit(
            protocol=protocol,
            asset_symbol='USDC',
            amount=allocation_per_protocol,
            supply_apy=initial_apy,
            borrow_apy=Decimal('0'),  # No borrowing in conservative strategy
            ltv=Decimal('0'),  # No leverage in conservative strategy
            liquidation_threshold=initial_liq_threshold  # Use historical parameter
        )

        print(f"  ✓ {protocol}: ${allocation_per_protocol:,.0f} at {initial_apy*100:.2f}% APY (Liq Threshold: {initial_liq_threshold*100:.1f}%)")

    # Prepare market data for simulation
    # We need to align all protocols to the same timeline
    min_length = min(len(data) for data in protocols_data.values())

    print(f"\nSimulating {min_length} days...")

    # Create market data generator with dynamic risk parameters
    def market_data_generator(day_index: int) -> Dict:
        """Generate market data for a specific day including dynamic risk parameters"""
        market_data = {}

        for protocol, data in protocols_data.items():
            if day_index < len(data):
                # Get risk parameters for this day
                ltv, liq_threshold = risk_parameters_by_protocol[protocol][day_index]

                market_data[protocol] = {
                    'USDC': {
                        'supply_apy': data[day_index].apy,
                        'borrow_apy': Decimal('0'),  # No borrowing in conservative
                        'ltv': ltv,  # Historical LTV (not used since no leverage)
                        'liquidation_threshold': liq_threshold  # Historical threshold
                    }
                }

        return market_data

    # Run simulation
    snapshots = treasury.run_simulation(
        days=min_length,
        market_data_generator=market_data_generator
    )

    print(f"✓ Simulation complete: {len(snapshots)} days")

    print_section("STEP 4: Performance Analysis")

    # Calculate metrics
    metrics_calc = PerformanceMetrics(risk_free_rate=Decimal('0.04'))
    portfolio_values = [s.net_value for s in snapshots]

    # Add initial value
    portfolio_values.insert(0, initial_capital)

    metrics = metrics_calc.calculate_all_metrics(
        portfolio_values=portfolio_values,
        days=min_length
    )

    # Display results
    print_header("BACKTEST RESULTS", "=")

    print("RETURNS".center(70))
    print("-" * 70)
    print(f"  Initial Capital:        $ {metrics['initial_value']:>12,.2f}")
    print(f"  Final Value:            $ {metrics['final_value']:>12,.2f}")
    print(f"  Profit/Loss:            $ {metrics['final_value'] - metrics['initial_value']:>12,.2f}")
    print(f"  Total Return:                     {metrics['total_return_pct']:>8.2f}%")
    print(f"  Annualized Return:                {metrics['annualized_return_pct']:>8.2f}%")

    print("\n" + "RISK METRICS".center(70))
    print("-" * 70)
    print(f"  Max Drawdown:                     {metrics['max_drawdown_pct']:>8.2f}%")
    print(f"  Volatility (Annual):              {metrics['volatility_pct']:>8.2f}%")

    # Check if max drawdown constraint is met
    max_dd_constraint = 10.0  # Conservative tier: 10% max
    if metrics['max_drawdown_pct'] <= max_dd_constraint:
        print(f"  ✓ Max drawdown within {max_dd_constraint}% constraint")
    else:
        print(f"  ⚠ Max drawdown EXCEEDS {max_dd_constraint}% constraint!")

    print("\n" + "RISK-ADJUSTED RETURNS".center(70))
    print("-" * 70)
    print(f"  Sharpe Ratio:                     {metrics['sharpe_ratio']:>8.2f}")
    print(f"  Sortino Ratio:                    {metrics['sortino_ratio']:>8.2f}")
    print(f"  Calmar Ratio:                     {metrics['calmar_ratio']:>8.2f}")

    print("\n" + "BENCHMARK COMPARISON".center(70))
    print("-" * 70)
    rf_return = metrics['risk_free_rate_pct'] * (min_length / 365)
    print(f"  Risk-Free Return ({min_length} days):     {rf_return:>8.2f}%")
    print(f"  Excess Return:                    {metrics['total_return_pct'] - rf_return:>8.2f}%")

    if metrics['annualized_return_pct'] > metrics['risk_free_rate_pct']:
        print(f"  ✓ Strategy OUTPERFORMS risk-free rate")
    else:
        print(f"  ⚠ Strategy UNDERPERFORMS risk-free rate")

    print("\n" + "DIVERSIFICATION".center(70))
    print("-" * 70)
    print(f"  Number of Protocols:              {len(protocols_data)}")
    print(f"  Allocation per Protocol:          {100/len(protocols_data):.1f}%")
    print(f"  Smart Contract Risk:              DIVERSIFIED")

    print("\n" + "=" * 70)

    # Return results
    return {
        'strategy': 'Conservative',
        'metrics': metrics,
        'snapshots': snapshots,
        'protocols': list(protocols_data.keys()),
        'num_protocols': len(protocols_data),
        'meets_max_drawdown': metrics['max_drawdown_pct'] <= max_dd_constraint,
        'outperforms_risk_free': metrics['annualized_return_pct'] > metrics['risk_free_rate_pct']
    }


def compare_single_vs_diversified(
    initial_capital: Decimal = Decimal('1000000'),
    days_back: int = 90
):
    """
    Compare single protocol vs diversified strategy
    """
    print_header("STRATEGY COMPARISON: Single vs Diversified")

    fetcher = HistoricalDataFetcher()

    # Test 1: Single protocol (Aave only)
    print_section("Strategy A: Single Protocol (Aave V3 Only)")

    aave_data = fetch_protocol_data(fetcher, 'aave-v3', 'USDC', days_back)

    if aave_data:
        # Fetch risk parameters for Aave
        start_date = aave_data[0].timestamp
        risk_params_aave = get_risk_parameters_for_simulation(
            protocol='aave-v3',
            asset_symbol='USDC',
            start_date=start_date,
            days=days_back,
            network='mainnet'
        )

        # Get initial risk parameters
        initial_ltv, initial_liq_threshold = risk_params_aave[0]

        treasury_single = TreasurySimulator(initial_capital=initial_capital, name="Single Protocol")
        treasury_single.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=initial_capital,
            supply_apy=aave_data[0].apy,
            borrow_apy=Decimal('0'),
            ltv=Decimal('0'),
            liquidation_threshold=initial_liq_threshold
        )

        def single_market_data(day_index: int) -> Dict:
            if day_index < len(aave_data) and day_index < len(risk_params_aave):
                ltv, liq_threshold = risk_params_aave[day_index]
                return {
                    'aave-v3': {
                        'USDC': {
                            'supply_apy': aave_data[day_index].apy,
                            'borrow_apy': Decimal('0'),
                            'ltv': ltv,
                            'liquidation_threshold': liq_threshold
                        }
                    }
                }
            return {}

        # Use minimum length between data and risk parameters
        sim_days = min(len(aave_data), len(risk_params_aave))
        snapshots_single = treasury_single.run_simulation(
            days=sim_days,
            market_data_generator=single_market_data
        )

        values_single = [initial_capital] + [s.net_value for s in snapshots_single]
        metrics_single = PerformanceMetrics().calculate_all_metrics(values_single, days=sim_days)

        print(f"  Total Return: {metrics_single['total_return_pct']:.2f}%")
        print(f"  Annualized Return: {metrics_single['annualized_return_pct']:.2f}%")
        print(f"  Max Drawdown: {metrics_single['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe Ratio: {metrics_single['sharpe_ratio']:.2f}")

    # Test 2: Diversified (run the full conservative strategy)
    print_section("Strategy B: Diversified (Aave + Compound + Morpho)")
    result_diversified = backtest_conservative_strategy(initial_capital, days_back)

    if result_diversified and aave_data:
        print_section("COMPARISON SUMMARY")

        print("Single Protocol (Aave only):")
        print(f"  Return: {metrics_single['annualized_return_pct']:.2f}%")
        print(f"  Risk (Max DD): {metrics_single['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe: {metrics_single['sharpe_ratio']:.2f}")
        print(f"  Diversification: LOW (1 protocol)")

        print("\nDiversified Strategy:")
        div_metrics = result_diversified['metrics']
        print(f"  Return: {div_metrics['annualized_return_pct']:.2f}%")
        print(f"  Risk (Max DD): {div_metrics['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe: {div_metrics['sharpe_ratio']:.2f}")
        print(f"  Diversification: HIGH ({result_diversified['num_protocols']} protocols)")

        print("\nConclusion:")
        if div_metrics['sharpe_ratio'] > metrics_single['sharpe_ratio']:
            print("  ✓ Diversified strategy has BETTER risk-adjusted returns")
        else:
            print("  Note: Single protocol had better risk-adjusted returns this period")


def main():
    """Main execution"""
    print_header("CONSERVATIVE STRATEGY HISTORICAL BACKTESTING", "=")

    print("Testing Conservative Tier Strategy")
    print("Using REAL historical data from DefiLlama")
    print("\nStrategy Characteristics:")
    print("  • Risk Level: LOW (Conservative)")
    print("  • Assets: Stablecoins only (USDC)")
    print("  • Protocols: Aave V3, Compound V3, Morpho")
    print("  • Leverage: NONE (lending only)")
    print("  • Diversification: Equal weight across protocols")
    print("  • Max Drawdown: 10% constraint")

    try:
        # Run main conservative strategy backtest
        result = backtest_conservative_strategy(
            initial_capital=Decimal('1000000'),
            days_back=90
        )

        if result:
            print("\n✓ Conservative strategy backtest completed successfully")

            # Run comparison
            print("\n" + "=" * 70)
            compare_single_vs_diversified(
                initial_capital=Decimal('1000000'),
                days_back=90
            )

    except Exception as e:
        print(f"\n❌ Error during backtesting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print_header("BACKTEST COMPLETE", "=")

    print("\nNext Steps:")
    print("  1. Review if strategy meets 10% max drawdown constraint")
    print("  2. Verify strategy outperforms risk-free rate")
    print("  3. Consider adjusting protocol weights based on historical performance")
    print("  4. Test with different time periods (bear markets, bull markets)")


if __name__ == "__main__":
    main()
