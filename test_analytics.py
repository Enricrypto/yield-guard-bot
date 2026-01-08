"""
Test script for Analytics & Performance Metrics
Tests all financial metrics calculations and strategy comparisons
"""

from src.analytics import PerformanceMetrics
from src.simulator import TreasurySimulator
from src.market_data import SyntheticDataGenerator
from decimal import Decimal


def test_basic_metrics():
    """Test basic performance metrics calculations"""
    print("\n" + "="*60)
    print("TESTING BASIC PERFORMANCE METRICS")
    print("="*60)

    metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

    # Test 1: Total Return
    print("\n1. Testing Total Return calculation...")
    initial = Decimal('1000000')
    final = Decimal('1100000')
    total_return = metrics.calculate_total_return(initial, final)
    print(f"   Initial: ${initial:,.0f}")
    print(f"   Final: ${final:,.0f}")
    print(f"   ✓ Total Return: {total_return*100:.2f}%")
    assert total_return == Decimal('0.10'), "Total return should be 10%"

    # Test 2: Annualized Return
    print("\n2. Testing Annualized Return calculation...")
    ann_return = metrics.calculate_annualized_return(initial, final, days=180)
    print(f"   Over 180 days")
    print(f"   ✓ Annualized Return: {ann_return*100:.2f}%")
    assert ann_return > total_return, "Annualized return should be higher for 180 days"

    # Test 3: Max Drawdown
    print("\n3. Testing Max Drawdown calculation...")
    portfolio_values = [
        Decimal('1000000'),  # Start
        Decimal('1050000'),  # +5% (peak)
        Decimal('1020000'),  # -2.86% from peak
        Decimal('1000000'),  # -4.76% from peak
        Decimal('1040000'),  # Recovery
    ]
    dd_info = metrics.calculate_max_drawdown(portfolio_values)
    print(f"   Portfolio values: {[float(v) for v in portfolio_values]}")
    print(f"   ✓ Max Drawdown: {dd_info['max_drawdown_pct']:.2f}%")
    print(f"   Peak: ${dd_info['peak_value']:,.0f}")
    print(f"   Trough: ${dd_info['trough_value']:,.0f}")
    assert dd_info['max_drawdown_pct'] > 0, "Should have detected drawdown"

    # Test 4: Volatility
    print("\n4. Testing Volatility calculation...")
    returns = [
        Decimal('0.01'),   # +1%
        Decimal('0.02'),   # +2%
        Decimal('-0.01'),  # -1%
        Decimal('0.015'),  # +1.5%
        Decimal('0.005'),  # +0.5%
    ]
    volatility = metrics.calculate_volatility(returns, annualize=True)
    print(f"   Daily returns: {[float(r*100) for r in returns]}%")
    print(f"   ✓ Annualized Volatility: {volatility*100:.2f}%")
    assert volatility > 0, "Volatility should be positive"

    # Test 5: Sharpe Ratio
    print("\n5. Testing Sharpe Ratio calculation...")
    sharpe = metrics.calculate_sharpe_ratio(returns, annualize=True)
    print(f"   Risk-free rate: {metrics.risk_free_rate*100:.2f}%")
    print(f"   ✓ Sharpe Ratio: {sharpe:.2f}")
    print(f"   Interpretation: {'Good' if sharpe > 1 else 'Poor'} risk-adjusted return")

    # Test 6: Sortino Ratio
    print("\n6. Testing Sortino Ratio calculation...")
    sortino = metrics.calculate_sortino_ratio(returns, annualize=True)
    print(f"   ✓ Sortino Ratio: {sortino:.2f}")
    print(f"   (Only considers downside volatility)")

    print("\n✓ All basic metrics calculated correctly")
    return True


def test_comprehensive_metrics():
    """Test calculate_all_metrics function"""
    print("\n" + "="*60)
    print("TESTING COMPREHENSIVE METRICS")
    print("="*60)

    metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

    # Create realistic portfolio growth
    print("\n1. Creating realistic portfolio simulation...")
    portfolio_values = [Decimal('1000000')]  # Start with $1M

    # Simulate 180 days of growth with volatility
    import random
    random.seed(42)

    for day in range(180):
        # Average daily return of ~0.03% with volatility
        daily_return = Decimal(str(random.gauss(0.0003, 0.005)))
        new_value = portfolio_values[-1] * (Decimal('1') + daily_return)
        portfolio_values.append(new_value)

    print(f"   ✓ Simulated {len(portfolio_values)} days")
    print(f"   Initial: ${portfolio_values[0]:,.0f}")
    print(f"   Final: ${portfolio_values[-1]:,.0f}")

    # Calculate all metrics at once
    print("\n2. Calculating all metrics...")
    results = metrics.calculate_all_metrics(portfolio_values, days=180)

    print(f"\n   PERFORMANCE SUMMARY:")
    print(f"   {'─'*50}")
    print(f"   Initial Value:       ${results['initial_value']:>12,.2f}")
    print(f"   Final Value:         ${results['final_value']:>12,.2f}")
    print(f"   Days:                {results['days']:>16}")
    print(f"\n   RETURNS:")
    print(f"   Total Return:        {results['total_return_pct']:>15.2f}%")
    print(f"   Annualized Return:   {results['annualized_return_pct']:>15.2f}%")
    print(f"\n   RISK METRICS:")
    print(f"   Max Drawdown:        {results['max_drawdown_pct']:>15.2f}%")
    print(f"   Volatility:          {results['volatility_pct']:>15.2f}%")
    print(f"\n   RISK-ADJUSTED RETURNS:")
    print(f"   Sharpe Ratio:        {results['sharpe_ratio']:>19.2f}")
    print(f"   Sortino Ratio:       {results['sortino_ratio']:>19.2f}")
    print(f"   Calmar Ratio:        {results['calmar_ratio']:>19.2f}")

    # Verify all metrics are present
    required_keys = [
        'total_return', 'annualized_return', 'max_drawdown',
        'volatility', 'sharpe_ratio', 'sortino_ratio', 'calmar_ratio'
    ]
    for key in required_keys:
        assert key in results, f"Missing metric: {key}"

    print(f"\n✓ All {len(required_keys)} metrics calculated successfully")
    return True


def test_strategy_comparison():
    """Test comparing multiple strategies"""
    print("\n" + "="*60)
    print("TESTING STRATEGY COMPARISON")
    print("="*60)

    metrics_calc = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

    # Simulate three different strategies
    print("\n1. Simulating three different strategies...")

    # Strategy A: Conservative (low volatility, steady growth)
    print("   Simulating Strategy A (Conservative)...")
    values_a = [Decimal('1000000')]
    for _ in range(180):
        values_a.append(values_a[-1] * Decimal('1.0002'))  # 0.02% daily

    # Strategy B: Aggressive (high volatility, higher returns)
    print("   Simulating Strategy B (Aggressive)...")
    import random
    random.seed(42)
    values_b = [Decimal('1000000')]
    for _ in range(180):
        daily_return = Decimal(str(random.gauss(0.0005, 0.01)))  # Higher volatility
        values_b.append(values_b[-1] * (Decimal('1') + daily_return))

    # Strategy C: Moderate (balanced)
    print("   Simulating Strategy C (Moderate)...")
    random.seed(123)
    values_c = [Decimal('1000000')]
    for _ in range(180):
        daily_return = Decimal(str(random.gauss(0.0004, 0.006)))
        values_c.append(values_c[-1] * (Decimal('1') + daily_return))

    print(f"   ✓ Generated {len(values_a)-1} days for each strategy")

    # Calculate metrics for each strategy
    print("\n2. Calculating metrics for each strategy...")
    strategy_metrics = {
        'Conservative': metrics_calc.calculate_all_metrics(values_a, days=180),
        'Aggressive': metrics_calc.calculate_all_metrics(values_b, days=180),
        'Moderate': metrics_calc.calculate_all_metrics(values_c, days=180)
    }

    # Display metrics for each strategy
    print(f"\n   STRATEGY METRICS:")
    print(f"   {'─'*70}")
    print(f"   {'Strategy':<15} {'Return':<10} {'Sharpe':<10} {'Drawdown':<12} {'Volatility'}")
    print(f"   {'─'*70}")

    for name, m in strategy_metrics.items():
        print(f"   {name:<15} {m['total_return_pct']:>7.2f}%  "
              f"{m['sharpe_ratio']:>8.2f}  "
              f"{m['max_drawdown_pct']:>9.2f}%  "
              f"{m['volatility_pct']:>9.2f}%")

    # Compare strategies
    print("\n3. Comparing strategies...")
    comparison = metrics_calc.compare_strategies(strategy_metrics)

    print(f"\n   BEST PERFORMERS BY METRIC:")
    print(f"   {'─'*50}")
    for metric, best_strategy in comparison['best_by_metric'].items():
        print(f"   {metric.replace('_', ' ').title():<25}: {best_strategy}")

    print(f"\n   OVERALL RANKING:")
    print(f"   {'─'*50}")
    for rank, strategy in enumerate(comparison['overall_ranking'], 1):
        print(f"   {rank}. {strategy}")

    print(f"\n   ✓ Best Overall Strategy: {comparison['best_overall']}")

    assert comparison['best_overall'] is not None, "Should identify best strategy"
    assert len(comparison['overall_ranking']) == 3, "Should rank all 3 strategies"

    print("\n✓ Strategy comparison completed successfully")
    return True


def test_integration_with_simulator():
    """Test integration with Treasury Simulator"""
    print("\n" + "="*60)
    print("TESTING INTEGRATION WITH TREASURY SIMULATOR")
    print("="*60)

    # Run a simulation
    print("\n1. Running treasury simulation...")
    treasury = TreasurySimulator(
        initial_capital=Decimal('1000000'),
        name="Analytics Test",
        min_health_factor=Decimal('1.5')
    )

    # Deposit into protocols
    treasury.deposit(
        protocol='aave-v3',
        asset_symbol='USDC',
        amount=Decimal('500000'),
        supply_apy=Decimal('0.05'),
        borrow_apy=Decimal('0.07')
    )

    treasury.deposit(
        protocol='morpho',
        asset_symbol='USDC',
        amount=Decimal('300000'),
        supply_apy=Decimal('0.06'),
        borrow_apy=Decimal('0.075')
    )

    # Generate market data
    generator = SyntheticDataGenerator(seed=42)
    market_snapshots = generator.generate_timeseries(
        days=90,
        asset_symbol='USDC',
        market_regime='normal'
    )

    def market_data_generator(day):
        if day < len(market_snapshots):
            snapshot = market_snapshots[day]
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

    # Run simulation
    snapshots = treasury.run_simulation(
        days=90,
        market_data_generator=market_data_generator
    )

    print(f"   ✓ Completed 90-day simulation")
    print(f"   Initial value: ${treasury.initial_capital:,.0f}")
    print(f"   Final value: ${snapshots[-1].net_value:,.0f}")

    # Extract portfolio values
    print("\n2. Extracting portfolio values...")
    portfolio_values = [Decimal(str(treasury.initial_capital))]  # Start with initial
    portfolio_values.extend([s.net_value for s in snapshots])

    print(f"   ✓ Extracted {len(portfolio_values)} portfolio values")

    # Calculate performance metrics
    print("\n3. Calculating performance metrics...")
    metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))
    results = metrics.calculate_all_metrics(portfolio_values, days=90)

    print(f"\n   SIMULATION PERFORMANCE:")
    print(f"   {'─'*50}")
    print(f"   Total Return:        {results['total_return_pct']:>15.2f}%")
    print(f"   Annualized Return:   {results['annualized_return_pct']:>15.2f}%")
    print(f"   Max Drawdown:        {results['max_drawdown_pct']:>15.2f}%")
    print(f"   Sharpe Ratio:        {results['sharpe_ratio']:>19.2f}")

    # Verify results make sense
    assert results['total_return_pct'] != 0, "Should have some return"
    assert results['annualized_return_pct'] != 0, "Should have annualized return"
    assert 'sharpe_ratio' in results, "Should calculate Sharpe ratio"

    print(f"\n✓ Successfully integrated with Treasury Simulator")
    return True


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TESTING EDGE CASES")
    print("="*60)

    metrics = PerformanceMetrics()

    # Test 1: Empty portfolio values
    print("\n1. Testing empty portfolio values...")
    results = metrics.calculate_all_metrics([])
    print(f"   ✓ Handled empty list: returned {len(results)} metrics")
    assert results['total_return'] == 0, "Should return 0 for empty portfolio"

    # Test 2: Single value
    print("\n2. Testing single portfolio value...")
    results = metrics.calculate_all_metrics([Decimal('1000000')])
    print(f"   ✓ Handled single value")
    assert results['total_return'] == 0, "Single value should have 0 return"

    # Test 3: Negative returns (loss scenario)
    print("\n3. Testing negative returns (loss scenario)...")
    portfolio_values = [
        Decimal('1000000'),
        Decimal('950000'),
        Decimal('900000'),
    ]
    results = metrics.calculate_all_metrics(portfolio_values, days=2)
    print(f"   Loss: {results['total_return_pct']:.2f}%")
    print(f"   ✓ Correctly handled negative returns")
    assert results['total_return_pct'] < 0, "Should show negative return"

    # Test 4: Zero initial value
    print("\n4. Testing zero initial value...")
    total_return = metrics.calculate_total_return(Decimal('0'), Decimal('100000'))
    print(f"   ✓ Handled zero initial value: {total_return}")
    assert total_return == Decimal('0'), "Should return 0 for zero initial"

    # Test 5: Complete loss
    print("\n5. Testing complete loss scenario...")
    ann_return = metrics.calculate_annualized_return(
        Decimal('1000000'),
        Decimal('0'),
        days=365
    )
    print(f"   ✓ Handled complete loss: {ann_return*100:.0f}%")
    assert ann_return == Decimal('-1'), "Should return -100% for total loss"

    print("\n✓ All edge cases handled correctly")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" "*15 + "ANALYTICS TEST SUITE")
    print("="*60)
    print("\nTesting Phase 6: Analytics & Performance Metrics")
    print("This suite tests:")
    print("  - Basic metric calculations (return, drawdown, volatility)")
    print("  - Comprehensive metrics (Sharpe, Sortino, Calmar ratios)")
    print("  - Strategy comparison and ranking")
    print("  - Integration with Treasury Simulator")
    print("  - Edge cases and error handling")

    results = []

    try:
        # Run tests
        results.append(("Basic Metrics", test_basic_metrics()))
        results.append(("Comprehensive Metrics", test_comprehensive_metrics()))
        results.append(("Strategy Comparison", test_strategy_comparison()))
        results.append(("Simulator Integration", test_integration_with_simulator()))
        results.append(("Edge Cases", test_edge_cases()))

        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{name}: {status}")

        print(f"\nTotal: {passed}/{total} test suites passed")

        if passed == total:
            print("\n🎉 All tests passed!")
            print("\n✓ Can calculate all financial metrics")
            print("✓ Can compare different strategies")
            print("✓ Ready for analysis")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test suite(s) failed")
            return 1

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
