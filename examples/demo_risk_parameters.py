"""
Demo: Historical Risk Parameter Tracking
Shows how LTV and liquidation thresholds change over time and affect simulations
"""

from decimal import Decimal
from datetime import datetime, timedelta

from src.market_data.risk_parameter_fetcher import (
    RiskParameterFetcher,
    get_risk_parameters_for_simulation
)
from src.simulator.treasury_simulator import TreasurySimulator


def demo_fetch_historical_parameters():
    """Demo: Fetch historical risk parameter changes"""
    print("=" * 80)
    print("DEMO 1: Fetching Historical Risk Parameters from Aave Subgraph")
    print("=" * 80)

    fetcher = RiskParameterFetcher(network='mainnet')

    # Fetch USDC risk parameters for last 90 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    print(f"\nFetching USDC risk parameters from {start_date.date()} to {end_date.date()}...")

    snapshots = fetcher.fetch_risk_parameter_history('USDC', start_date, end_date)

    if snapshots:
        print(f"\n✓ Found {len(snapshots)} risk parameter change(s)")

        for snapshot in snapshots:
            print(f"\n  Date: {snapshot.timestamp.strftime('%Y-%m-%d')}")
            print(f"  LTV: {snapshot.ltv * 100:.1f}%")
            print(f"  Liquidation Threshold: {snapshot.liquidation_threshold * 100:.1f}%")
            print(f"  Liquidation Bonus: {snapshot.liquidation_bonus * 100:.1f}%")
    else:
        print("\n⚠️  No historical changes found (using current parameters)")

    return snapshots


def demo_simulation_with_dynamic_parameters():
    """Demo: Run simulation with changing risk parameters"""
    print("\n" + "=" * 80)
    print("DEMO 2: Simulation with Dynamic Risk Parameters")
    print("=" * 80)

    # Setup simulation dates
    start_date = datetime(2024, 1, 1)
    days = 90

    print(f"\nSimulation: {days} days starting {start_date.date()}")

    # Get risk parameters for simulation period
    print("\nFetching historical risk parameters...")
    risk_params = get_risk_parameters_for_simulation(
        protocol='aave-v3',
        asset_symbol='USDC',
        start_date=start_date,
        days=days,
        network='mainnet'
    )

    # Check if parameters change during simulation
    unique_params = set(risk_params.values())
    if len(unique_params) > 1:
        print(f"✓ Parameters change {len(unique_params) - 1} time(s) during simulation")
        print("\nParameter timeline:")
        prev_params = None
        for day, params in sorted(risk_params.items()):
            if params != prev_params:
                ltv, liq_threshold = params
                print(f"  Day {day:3d}: LTV={ltv*100:.1f}%, Liq Threshold={liq_threshold*100:.1f}%")
                prev_params = params
    else:
        ltv, liq_threshold = list(unique_params)[0]
        print(f"✓ Parameters constant: LTV={ltv*100:.1f}%, Liq Threshold={liq_threshold*100:.1f}%")

    # Create treasury with leverage strategy
    treasury = TreasurySimulator(
        initial_capital=Decimal('1000000'),
        name="Moderate Leverage Strategy"
    )

    # Open leveraged position
    initial_ltv, initial_liq_threshold = risk_params[0]

    pos = treasury.deposit(
        protocol='aave-v3',
        asset_symbol='USDC',
        amount=Decimal('1000000'),
        supply_apy=Decimal('0.05'),  # 5% supply
        borrow_apy=Decimal('0.07'),  # 7% borrow
        ltv=initial_ltv,
        liquidation_threshold=initial_liq_threshold
    )

    # Borrow 60% (moderate leverage)
    pos.borrow(Decimal('600000'))

    print(f"\nInitial Position:")
    print(f"  Collateral: $1,000,000")
    print(f"  Debt: $600,000 (60%)")
    print(f"  Health Factor: {treasury.calculate_health_factor():.3f}")

    # Market data generator with dynamic risk parameters
    def market_data_generator(day_index: int):
        ltv, liq_threshold = risk_params[day_index]

        return {
            'aave-v3': {
                'USDC': {
                    'supply_apy': Decimal('0.05'),
                    'borrow_apy': Decimal('0.07'),
                    'ltv': ltv,
                    'liquidation_threshold': liq_threshold
                }
            }
        }

    # Run simulation
    print(f"\nRunning {days}-day simulation with dynamic risk parameters...")
    snapshots = treasury.run_simulation(
        days=days,
        market_data_generator=market_data_generator
    )

    # Show results
    final_snapshot = snapshots[-1]

    print(f"\nFinal Position (Day {days}):")
    print(f"  Net Value: ${final_snapshot.net_value:,.2f}")
    print(f"  Health Factor: {final_snapshot.overall_health_factor:.3f}")
    print(f"  Total Return: ${final_snapshot.net_value - treasury.initial_capital:,.2f}")

    # Show how health factor changed with parameter changes
    print(f"\nHealth Factor Timeline:")
    for i in [0, 30, 60, 89]:
        snapshot = snapshots[i]
        print(f"  Day {i:3d}: HF = {snapshot.overall_health_factor:.3f}")


def demo_parameter_impact():
    """Demo: Show impact of parameter changes on health factor"""
    print("\n" + "=" * 80)
    print("DEMO 3: Impact of Risk Parameter Changes")
    print("=" * 80)

    # Same position, different parameters
    collateral = Decimal('100000')
    debt = Decimal('70000')  # 70% LTV

    scenarios = [
        ("Original Parameters", Decimal('0.85')),
        ("Increased Threshold (+2%)", Decimal('0.87')),
        ("Decreased Threshold (-2%)", Decimal('0.83')),
    ]

    print(f"\nPosition: ${collateral:,} collateral, ${debt:,} debt (70% LTV)")
    print("\nHealth Factor under different liquidation thresholds:")

    for name, liq_threshold in scenarios:
        hf = (collateral * liq_threshold) / debt
        print(f"  {name:30s}: {hf:.3f}")

    print("\nKey Insight:")
    print("  Even small changes in liquidation threshold significantly affect")
    print("  liquidation risk for leveraged positions!")


if __name__ == "__main__":
    try:
        # Demo 1: Fetch historical parameters
        snapshots = demo_fetch_historical_parameters()

        # Demo 2: Simulation with dynamic parameters
        demo_simulation_with_dynamic_parameters()

        # Demo 3: Show parameter impact
        demo_parameter_impact()

        print("\n" + "=" * 80)
        print("✓ All demos completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error running demos: {e}")
        import traceback
        traceback.print_exc()
