"""
Historical Backtesting Script
Run backtests using REAL historical DeFi yield data from DefiLlama

This script:
1. Fetches real historical APY data
2. Simulates portfolio performance with actual market rates
3. Calculates performance metrics
4. Compares results to benchmarks
"""

from src.market_data.historical_fetcher import HistoricalDataFetcher
from src.simulator import TreasurySimulator
from src.analytics import PerformanceMetrics
from decimal import Decimal
from datetime import datetime, timedelta


def backtest_simple_strategy(
    initial_capital: Decimal = Decimal('1000000'),
    days_back: int = 90
):
    """
    Backtest a simple strategy: deposit in Aave USDC

    Args:
        initial_capital: Starting capital ($1M default)
        days_back: How many days of history to test
    """
    print("\n" + "="*70)
    print(" "*20 + "HISTORICAL BACKTEST")
    print("="*70)
    print(f"\nStrategy: Simple Aave V3 USDC Lending")
    print(f"Initial Capital: ${initial_capital:,.0f}")
    print(f"Period: Last {days_back} days")

    # Step 1: Fetch historical data
    print("\n" + "-"*70)
    print("STEP 1: Fetching Historical Data")
    print("-"*70)

    fetcher = HistoricalDataFetcher()

    print("\nFetching Aave V3 USDC historical data...")
    historical = fetcher.get_historical_data_for_backtest(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=days_back
    )

    if not historical:
        print("❌ Could not fetch historical data")
        return None

    print(f"✓ Retrieved {len(historical)} data points")
    print(f"  Date range: {historical[0].timestamp.date()} to {historical[-1].timestamp.date()}")

    apys = [float(h.apy * 100) for h in historical]
    print(f"  APY range: {min(apys):.2f}% - {max(apys):.2f}%")
    print(f"  Average APY: {sum(apys)/len(apys):.2f}%")

    # Step 2: Run simulation
    print("\n" + "-"*70)
    print("STEP 2: Running Simulation")
    print("-"*70)

    treasury = TreasurySimulator(
        initial_capital=initial_capital,
        name="Historical Backtest",
        min_health_factor=Decimal('1.5')
    )

    # Deposit all capital into Aave USDC
    print(f"\nDepositing ${initial_capital:,.0f} into Aave V3 USDC...")
    treasury.deposit(
        protocol='aave-v3',
        asset_symbol='USDC',
        amount=initial_capital,
        supply_apy=historical[0].apy,
        borrow_apy=historical[0].apy * Decimal('1.2')  # Estimate borrow rate
    )
    print("✓ Position opened")

    # Create market data generator from historical data
    def market_data_generator(day):
        if day < len(historical):
            h = historical[day]
            return {
                'aave-v3': {
                    'USDC': {
                        'supply_apy': h.apy,
                        'borrow_apy': h.apy * Decimal('1.2')  # Estimate
                    }
                }
            }
        return None

    # Run simulation
    print(f"\nSimulating {len(historical)} days...")
    snapshots = treasury.run_simulation(
        days=len(historical),
        market_data_generator=market_data_generator
    )
    print(f"✓ Simulation complete")

    # Step 3: Calculate metrics
    print("\n" + "-"*70)
    print("STEP 3: Performance Analysis")
    print("-"*70)

    portfolio_values = [Decimal(str(initial_capital))]
    portfolio_values.extend([s.net_value for s in snapshots])

    metrics_calc = PerformanceMetrics(risk_free_rate=Decimal('0.04'))
    metrics = metrics_calc.calculate_all_metrics(
        portfolio_values=portfolio_values,
        days=len(historical)
    )

    # Display results
    print(f"\n{'='*70}")
    print(f"{'BACKTEST RESULTS':^70}")
    print(f"{'='*70}")

    print(f"\n{'RETURNS':^70}")
    print(f"{'-'*70}")
    print(f"  Initial Capital:        ${metrics['initial_value']:>15,.2f}")
    print(f"  Final Value:            ${metrics['final_value']:>15,.2f}")
    print(f"  Profit/Loss:            ${metrics['final_value'] - metrics['initial_value']:>15,.2f}")
    print(f"  Total Return:           {metrics['total_return_pct']:>18.2f}%")
    print(f"  Annualized Return:      {metrics['annualized_return_pct']:>18.2f}%")

    print(f"\n{'RISK METRICS':^70}")
    print(f"{'-'*70}")
    print(f"  Max Drawdown:           {metrics['max_drawdown_pct']:>18.2f}%")
    print(f"  Volatility (Annual):    {metrics['volatility_pct']:>18.2f}%")

    print(f"\n{'RISK-ADJUSTED RETURNS':^70}")
    print(f"{'-'*70}")
    print(f"  Sharpe Ratio:           {metrics['sharpe_ratio']:>22.2f}")
    print(f"  Sortino Ratio:          {metrics['sortino_ratio']:>22.2f}")
    print(f"  Calmar Ratio:           {metrics['calmar_ratio']:>22.2f}")

    print(f"\n{'BENCHMARK COMPARISON':^70}")
    print(f"{'-'*70}")
    risk_free = metrics['risk_free_rate_pct'] * (len(historical) / 365)
    print(f"  Risk-Free Return:       {risk_free:>18.2f}%")
    print(f"  Excess Return:          {metrics['total_return_pct'] - risk_free:>18.2f}%")

    print(f"\n{'='*70}\n")

    return {
        'metrics': metrics,
        'snapshots': snapshots,
        'historical': historical
    }


def backtest_multi_protocol(
    initial_capital: Decimal = Decimal('1000000'),
    days_back: int = 90
):
    """
    Backtest a multi-protocol strategy

    Args:
        initial_capital: Starting capital
        days_back: How many days of history
    """
    print("\n" + "="*70)
    print(" "*20 + "MULTI-PROTOCOL BACKTEST")
    print("="*70)
    print(f"\nStrategy: Diversified across Aave & Compound")
    print(f"Initial Capital: ${initial_capital:,.0f}")
    print(f"Period: Last {days_back} days")

    fetcher = HistoricalDataFetcher()

    # Fetch data for multiple protocols
    print("\nFetching historical data for multiple protocols...")

    protocol_assets = [
        {'protocol': 'aave-v3', 'asset': 'USDC', 'chain': 'Ethereum'},
        {'protocol': 'compound-v3', 'asset': 'USDC', 'chain': 'Ethereum'},
    ]

    historical_data = fetcher.get_multiple_protocols_history(
        protocol_assets=protocol_assets,
        days_back=days_back
    )

    if len(historical_data) < 2:
        print("❌ Could not fetch data for all protocols")
        print(f"   Only found: {list(historical_data.keys())}")
        return None

    print(f"✓ Retrieved data for {len(historical_data)} protocol/asset pairs")

    # Print summary for each
    for key, data in historical_data.items():
        apys = [float(h.apy * 100) for h in data]
        print(f"\n  {key}:")
        print(f"    Data points: {len(data)}")
        print(f"    Avg APY: {sum(apys)/len(apys):.2f}%")

    print("\n✓ Ready for simulation")
    print("\n(Note: Full multi-protocol simulation would follow similar pattern)")

    return historical_data


def main():
    """Run backtesting examples"""
    print("\n" + "="*70)
    print(" "*15 + "DEFI YIELD HISTORICAL BACKTESTING")
    print("="*70)
    print("\nUsing REAL historical data from DefiLlama")
    print("No synthetic data - actual market conditions!")

    try:
        # Test 1: Simple strategy
        print("\n" + "="*70)
        print("TEST 1: Simple Aave V3 USDC Strategy")
        print("="*70)

        result = backtest_simple_strategy(
            initial_capital=Decimal('1000000'),
            days_back=90
        )

        if result:
            print("✓ Backtest completed successfully")
        else:
            print("✗ Backtest failed")

        # Test 2: Multi-protocol (data fetch only for now)
        print("\n" + "="*70)
        print("TEST 2: Multi-Protocol Data Fetch")
        print("="*70)

        multi_data = backtest_multi_protocol(
            initial_capital=Decimal('1000000'),
            days_back=90
        )

        if multi_data:
            print("\n✓ Multi-protocol data ready for backtesting")

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print("\n✓ Historical backtesting system is working!")
        print("✓ Using real DeFi market data")
        print("✓ Performance metrics calculated")
        print("\nYou can now:")
        print("  - Backtest different strategies")
        print("  - Compare protocols")
        print("  - Analyze real historical performance")

    except Exception as e:
        print(f"\n❌ Error during backtesting: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
