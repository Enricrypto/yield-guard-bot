"""
Test script for Treasury Simulator
Tests Position and TreasurySimulator with realistic scenarios
"""

from src.simulator import Position, TreasurySimulator
from src.market_data import SyntheticDataGenerator
from decimal import Decimal
from datetime import datetime


def test_position():
    """Test Position dataclass"""
    print("\n" + "="*60)
    print("TESTING POSITION")
    print("="*60)

    # Test 1: Create position
    print("\n1. Creating basic position...")
    pos = Position(
        protocol='aave-v3',
        asset_symbol='USDC',
        collateral_amount=Decimal('100000'),
        supply_apy=Decimal('0.05'),
        borrow_apy=Decimal('0.07')
    )
    print(f"   ✓ {pos}")
    print(f"   Health Factor: {pos.health_factor}")
    print(f"   Max Borrowable: ${pos.max_borrowable:,.2f}")

    # Test 2: Borrowing
    print("\n2. Testing borrowing...")
    pos.borrow(Decimal('50000'))
    print(f"   ✓ Borrowed $50,000")
    print(f"   Health Factor: {pos.health_factor:.2f}")
    print(f"   Current LTV: {pos.current_ltv*100:.1f}%")
    print(f"   Net APY: {pos.get_net_apy()*100:.2f}%")

    # Test 3: Interest accrual
    print("\n3. Accruing interest for 30 days...")
    earned, paid = pos.accrue_interest(days=Decimal('30'))
    print(f"   ✓ Interest earned: ${earned:,.2f}")
    print(f"   Interest paid: ${paid:,.2f}")
    print(f"   Net interest: ${earned - paid:,.2f}")

    # Test 4: Withdrawal
    print("\n4. Testing withdrawal...")
    try:
        pos.withdraw(Decimal('10000'))
        print(f"   ✓ Withdrew $10,000")
        print(f"   New collateral: ${pos.collateral_amount:,.2f}")
        print(f"   Health Factor: {pos.health_factor:.2f}")
    except ValueError as e:
        print(f"   ✗ Withdrawal failed: {e}")

    # Test 5: Repayment
    print("\n5. Testing debt repayment...")
    pos.repay(Decimal('20000'))
    print(f"   ✓ Repaid $20,000")
    print(f"   Remaining debt: ${pos.debt_amount:,.2f}")
    print(f"   Health Factor: {pos.health_factor:.2f}")

    return True


def test_treasury_simulator():
    """Test TreasurySimulator"""
    print("\n" + "="*60)
    print("TESTING TREASURY SIMULATOR")
    print("="*60)

    # Test 1: Initialize treasury
    print("\n1. Initializing treasury with $1M...")
    treasury = TreasurySimulator(
        initial_capital=Decimal('1000000'),
        name="Test Treasury",
        min_health_factor=Decimal('1.5')
    )
    print(f"   ✓ {treasury}")

    # Test 2: Deposit into protocols
    print("\n2. Depositing into protocols...")
    treasury.deposit(
        protocol='aave-v3',
        asset_symbol='USDC',
        amount=Decimal('500000'),
        supply_apy=Decimal('0.05'),
        borrow_apy=Decimal('0.07')
    )
    print(f"   ✓ Deposited $500k into Aave")

    treasury.deposit(
        protocol='morpho',
        asset_symbol='USDC',
        amount=Decimal('300000'),
        supply_apy=Decimal('0.06'),
        borrow_apy=Decimal('0.075')
    )
    print(f"   ✓ Deposited $300k into Morpho")

    print(f"\n   Total collateral: ${treasury.get_total_collateral():,.0f}")
    print(f"   Available capital: ${treasury.available_capital:,.0f}")
    print(f"   Health factor: {treasury.calculate_health_factor()}")

    # Test 3: Simulate 30 days
    print("\n3. Simulating 30 days...")
    snapshots = treasury.run_simulation(days=30)
    print(f"   ✓ Simulated {len(snapshots)} days")

    final = snapshots[-1]
    print(f"   Final net value: ${final.net_value:,.2f}")
    print(f"   Cumulative yield: ${final.cumulative_yield:,.2f}")
    print(f"   Daily return: {final.daily_return_pct:.4f}%")

    # Test 4: Portfolio summary
    print("\n4. Getting portfolio summary...")
    summary = treasury.get_portfolio_summary()
    print(f"   ✓ Positions: {summary['num_positions']}")
    print(f"   Total return: {summary['total_return_pct']:.2f}%")
    print(f"   Simulation days: {summary['simulation_days']}")

    return True


def test_long_simulation():
    """Test 180-day simulation with realistic market data"""
    print("\n" + "="*60)
    print("TESTING 180-DAY SIMULATION")
    print("="*60)

    # Create treasury
    print("\n1. Setting up treasury with $1M capital...")
    treasury = TreasurySimulator(
        initial_capital=Decimal('1000000'),
        name="Long-term Treasury",
        min_health_factor=Decimal('1.5')
    )

    # Deposit across multiple protocols
    treasury.deposit(
        protocol='aave-v3',
        asset_symbol='USDC',
        amount=Decimal('400000'),
        supply_apy=Decimal('0.05'),
        borrow_apy=Decimal('0.07')
    )

    treasury.deposit(
        protocol='morpho',
        asset_symbol='USDC',
        amount=Decimal('350000'),
        supply_apy=Decimal('0.06'),
        borrow_apy=Decimal('0.075')
    )

    treasury.deposit(
        protocol='aave-v3',
        asset_symbol='DAI',
        amount=Decimal('150000'),
        supply_apy=Decimal('0.048'),
        borrow_apy=Decimal('0.068')
    )

    print(f"   ✓ Opened {len(treasury.positions)} positions")
    print(f"   Total deployed: ${treasury.get_total_collateral():,.0f}")

    # Generate synthetic market data
    print("\n2. Generating 180 days of market data...")
    generator = SyntheticDataGenerator(seed=42)
    market_snapshots = generator.generate_timeseries(
        days=180,
        asset_symbol='USDC',
        market_regime='normal'
    )
    print(f"   ✓ Generated {len(market_snapshots)} market snapshots")

    # Create market data generator function
    def market_data_generator(day):
        """Generate market data for simulation"""
        if day < len(market_snapshots):
            snapshot = market_snapshots[day]
            return {
                'aave-v3': {
                    'USDC': {
                        'supply_apy': snapshot.aave_supply_apy,
                        'borrow_apy': snapshot.aave_borrow_apy
                    },
                    'DAI': {
                        'supply_apy': snapshot.aave_supply_apy * Decimal('0.96'),  # DAI slightly lower
                        'borrow_apy': snapshot.aave_borrow_apy * Decimal('0.97')
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

    # Track progress
    milestones = [30, 60, 90, 120, 150, 180]
    milestone_idx = 0

    def progress_callback(day, snapshot):
        nonlocal milestone_idx
        if milestone_idx < len(milestones) and day + 1 == milestones[milestone_idx]:
            print(f"   Day {day + 1}: Value=${snapshot.net_value:,.0f}, "
                  f"Yield=${snapshot.cumulative_yield:,.0f}, "
                  f"HF={snapshot.overall_health_factor:.2f}")
            milestone_idx += 1

    # Run simulation
    print("\n3. Running 180-day simulation...")
    snapshots = treasury.run_simulation(
        days=180,
        market_data_generator=market_data_generator,
        daily_callback=progress_callback
    )

    # Analyze results
    print("\n4. Analyzing results...")
    final = snapshots[-1]
    initial_value = treasury.initial_capital

    print(f"\n   FINAL RESULTS:")
    print(f"   {'─'*50}")
    print(f"   Initial Capital:     ${initial_value:>12,.2f}")
    print(f"   Final Net Value:     ${final.net_value:>12,.2f}")
    print(f"   Cumulative Yield:    ${final.cumulative_yield:>12,.2f}")
    print(f"   Total Return:        {((final.net_value - initial_value) / initial_value * 100):>12.2f}%")
    print(f"   Annualized Return:   {((final.net_value / initial_value) ** Decimal(365/180) - 1) * 100:>12.2f}%")
    print(f"   Final Health Factor: {final.overall_health_factor:>16.2f}")
    print(f"   Number of Positions: {final.num_positions:>16}")

    # Calculate statistics
    yields = [s.daily_yield for s in snapshots]
    avg_daily_yield = sum(yields) / len(yields)

    print(f"\n   STATISTICS:")
    print(f"   {'─'*50}")
    print(f"   Avg Daily Yield:     ${avg_daily_yield:>12,.2f}")
    print(f"   Min Health Factor:   {min(s.overall_health_factor for s in snapshots):>16.2f}")
    print(f"   Max Health Factor:   {max(s.overall_health_factor for s in snapshots):>16.2f}")
    print(f"   Days Simulated:      {len(snapshots):>16}")

    # Check if profitable
    is_profitable = final.net_value > initial_value
    print(f"\n   Result: {'✓ PROFITABLE' if is_profitable else '✗ LOSS'}")

    return is_profitable


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TESTING EDGE CASES")
    print("="*60)

    # Test 1: Insufficient capital
    print("\n1. Testing insufficient capital...")
    treasury = TreasurySimulator(initial_capital=Decimal('100000'))
    try:
        treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('200000'),  # More than available
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07')
        )
        print("   ✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly raised error: {str(e)[:50]}...")

    # Test 2: Over-borrowing
    print("\n2. Testing over-borrowing...")
    pos = Position(
        protocol='aave-v3',
        asset_symbol='USDC',
        collateral_amount=Decimal('100000'),
        ltv=Decimal('0.80')
    )
    try:
        pos.borrow(Decimal('90000'))  # Exceeds LTV
        print("   ✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly raised error: {str(e)[:50]}...")

    # Test 3: Unsafe withdrawal
    print("\n3. Testing unsafe withdrawal...")
    pos = Position(
        protocol='aave-v3',
        asset_symbol='USDC',
        collateral_amount=Decimal('100000'),
        debt_amount=Decimal('70000'),
        liquidation_threshold=Decimal('0.85')
    )
    try:
        pos.withdraw(Decimal('50000'))  # Would make HF < 1
        print("   ✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly raised error: {str(e)[:50]}...")

    # Test 4: Zero debt health factor
    print("\n4. Testing health factor with zero debt...")
    pos = Position(
        protocol='aave-v3',
        asset_symbol='USDC',
        collateral_amount=Decimal('100000')
    )
    hf = pos.health_factor
    print(f"   ✓ Health factor with zero debt: {hf}")

    print("\n✓ All edge cases handled correctly")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" "*15 + "TREASURY SIMULATOR TEST SUITE")
    print("="*60)
    print("\nTesting Phase 5: Treasury Simulator")
    print("This suite tests:")
    print("  - Position management (deposits, borrows, interest)")
    print("  - Treasury simulator core functions")
    print("  - 180-day simulation with market data")
    print("  - Edge cases and error handling")

    results = []

    try:
        # Run tests
        results.append(("Position", test_position()))
        results.append(("Treasury Simulator", test_treasury_simulator()))
        results.append(("180-Day Simulation", test_long_simulation()))
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
