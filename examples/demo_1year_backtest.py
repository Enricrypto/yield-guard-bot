#!/usr/bin/env python3
"""
Demo: 1-Year Historical Backtest with Real Data
Fetches and backtests using actual DeFi yield data from the past year
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from market_data.historical_fetcher import HistoricalDataFetcher
from simulator.treasury_simulator import TreasurySimulator
from analytics.performance_metrics import PerformanceMetrics
from decimal import Decimal
from datetime import datetime


def fetch_1year_data():
    """Fetch 1 year of historical data"""
    print("="*70)
    print(" "*20 + "1-YEAR DATA FETCH")
    print("="*70)

    fetcher = HistoricalDataFetcher()

    print("\nFetching 1 year (365 days) of Aave V3 USDC data...")
    print("This may take a moment...\n")

    historical = fetcher.get_historical_data_for_backtest(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=365  # ← 1 FULL YEAR
    )

    if not historical:
        print("❌ Could not fetch data")
        return None

    print(f"✓ SUCCESS! Retrieved {len(historical)} data points")
    print(f"\nData Range:")
    print(f"  Start: {historical[0].timestamp.date()}")
    print(f"  End:   {historical[-1].timestamp.date()}")
    print(f"  Days:  {len(historical)}")

    # Calculate APY statistics
    apys = [float(h.apy * 100) for h in historical]
    avg_apy = sum(apys) / len(apys)

    print(f"\nAPY Statistics (1 year):")
    print(f"  Minimum:  {min(apys):>6.2f}%")
    print(f"  Maximum:  {max(apys):>6.2f}%")
    print(f"  Average:  {avg_apy:>6.2f}%")
    print(f"  Median:   {sorted(apys)[len(apys)//2]:>6.2f}%")

    # Calculate TVL statistics
    tvls = [float(h.tvl_usd) for h in historical]
    avg_tvl = sum(tvls) / len(tvls)

    print(f"\nTVL Statistics:")
    print(f"  Min TVL:  ${min(tvls):>15,.0f}")
    print(f"  Max TVL:  ${max(tvls):>15,.0f}")
    print(f"  Avg TVL:  ${avg_tvl:>15,.0f}")

    return historical


def backtest_1year(initial_capital: float = 10000):
    """Run a 1-year backtest with real data"""
    print("\n" + "="*70)
    print(" "*20 + "1-YEAR BACKTEST")
    print("="*70)

    print(f"\nInitial Capital: ${initial_capital:,.2f}")

    # Fetch historical data
    fetcher = HistoricalDataFetcher()

    print("\nFetching 1 year of historical data...")
    historical = fetcher.get_historical_data_for_backtest(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=365
    )

    if not historical:
        print("❌ Could not fetch data")
        return None

    print(f"✓ Retrieved {len(historical)} days of data")

    # Initialize simulator
    print(f"\nInitializing simulator...")
    simulator = TreasurySimulator(
        initial_capital=Decimal(str(initial_capital)),
        name="1-Year Historical Backtest",
        min_health_factor=Decimal('1.5')
    )

    # Deposit all capital
    print(f"Depositing ${initial_capital:,.2f} into Aave V3 USDC...")
    simulator.deposit(
        protocol='aave',
        asset_symbol='USDC',
        amount=Decimal(str(initial_capital)),
        supply_apy=historical[0].apy,
        borrow_apy=historical[0].apy * Decimal('1.2'),
        ltv=Decimal('0.75'),
        liquidation_threshold=Decimal('0.80')
    )
    print("✓ Position opened")

    # Run simulation day by day with real APY data
    print(f"\nRunning simulation with real market data...")
    print("Progress: ", end='', flush=True)

    snapshots = []
    for day in range(len(historical)):
        # Progress indicator
        if day % 30 == 0:
            print(f"{day}...", end='', flush=True)

        # Get real APY for this day
        h = historical[day]

        # Update position APY (simulating rate changes)
        if simulator.positions:
            simulator.positions[0].supply_apy = h.apy
            simulator.positions[0].borrow_apy = h.apy * Decimal('1.2')

        # Step forward one day
        snapshot = simulator.step(days=Decimal('1'))
        snapshots.append(snapshot)

    print(f"{len(historical)} ✓")

    # Calculate performance metrics
    print("\nCalculating performance metrics...")

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

    # Display results
    print("\n" + "="*70)
    print(" "*25 + "RESULTS")
    print("="*70)

    print(f"\n{'CAPITAL'}")
    print(f"  Initial:              ${initial_capital:>15,.2f}")
    print(f"  Final:                ${float(final_value):>15,.2f}")
    print(f"  Profit:               ${float(final_value - Decimal(str(initial_capital))):>15,.2f}")

    print(f"\n{'RETURNS'}")
    print(f"  Total Return:         {total_return:>18.2f}%")
    print(f"  Annualized Return:    {annualized_return:>18.2f}%")

    print(f"\n{'RISK METRICS'}")
    print(f"  Max Drawdown:         {max_drawdown:>18.2f}%")
    print(f"  Sharpe Ratio:         {sharpe:>22.2f}")

    print(f"\n{'PERFORMANCE SUMMARY'}")
    if total_return > 4.0:  # Beat risk-free rate
        print(f"  ✓ Strategy outperformed risk-free rate (4%)")
    if max_drawdown > -10:
        print(f"  ✓ Low drawdown (< 10%)")
    if sharpe > 1.0:
        print(f"  ✓ Good risk-adjusted returns (Sharpe > 1.0)")

    print("\n" + "="*70 + "\n")

    return {
        'initial_capital': initial_capital,
        'final_value': float(final_value),
        'total_return': total_return,
        'annualized_return': annualized_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe,
        'days': len(historical),
        'snapshots': snapshots
    }


def main():
    """Main demo function"""
    print("\n" + "="*70)
    print(" "*15 + "1-YEAR HISTORICAL BACKTEST DEMO")
    print("="*70)
    print("\nThis demo will:")
    print("  1. Fetch 1 year of REAL Aave V3 USDC data from DefiLlama")
    print("  2. Run a backtest using actual historical APY rates")
    print("  3. Calculate performance metrics")
    print("\nNote: This uses REAL market data, not synthetic!")

    try:
        # Option 1: Just fetch and show data
        print("\n" + "="*70)
        print("OPTION 1: Fetch & Display 1 Year of Data")
        print("="*70)

        historical = fetch_1year_data()

        if historical:
            # Option 2: Run full backtest
            print("\n" + "="*70)
            print("OPTION 2: Run Full 1-Year Backtest")
            print("="*70)

            result = backtest_1year(initial_capital=10000)

            if result:
                print("\n✓ 1-YEAR BACKTEST COMPLETED SUCCESSFULLY!")
                print(f"\nWith just $10,000 invested in Aave USDC for 1 year:")
                print(f"  → Final Value: ${result['final_value']:,.2f}")
                print(f"  → Total Return: {result['total_return']:.2f}%")
                print(f"  → Annualized: {result['annualized_return']:.2f}%")
        else:
            print("\n❌ Failed to fetch data. Check your internet connection.")
            print("DefiLlama API might be temporarily unavailable.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
