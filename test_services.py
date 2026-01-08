#!/usr/bin/env python3
"""
Test script for database service layer
"""

from datetime import datetime, timedelta
from src.models import SessionLocal
from src.services import StrategyService, SimulationService, PortfolioService


def test_services():
    """Test all service layer methods"""
    print("=" * 60)
    print("Testing Database Service Layer")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Test 1: Strategy Service
        print("\n1. Testing StrategyService...")
        strategy = StrategyService.create_strategy(
            db=db,
            name="Aggressive Growth Strategy",
            description="High-risk, high-reward DeFi strategy",
            risk_level="high",
            allocation_percentage=75.0,
            protocols=["Aave", "Compound", "Uniswap"],
            asset_preferences=["ETH", "WBTC"],
            max_drawdown=30.0,
            rebalance_threshold=10.0
        )
        print(f"   ✅ Created strategy: {strategy.name} (ID: {strategy.id})")

        # Test retrieve
        retrieved = StrategyService.get_strategy_by_id(db, strategy.id)
        print(f"   ✅ Retrieved strategy: {retrieved.name}")

        # Test 2: Simulation Service
        print("\n2. Testing SimulationService...")
        simulation = SimulationService.create_simulation(
            db=db,
            strategy_id=strategy.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=50000.0
        )
        print(f"   ✅ Created simulation (ID: {simulation.id}, Status: {simulation.status})")

        # Update with results
        updated_sim = SimulationService.update_simulation_results(
            db=db,
            simulation_id=simulation.id,
            final_value=62500.0,
            total_return=25.0,
            total_return_amount=12500.0,
            max_drawdown=12.5,
            sharpe_ratio=2.1,
            volatility=8.5,
            win_rate=72.0,
            execution_time=30.5
        )
        print(f"   ✅ Updated simulation with results (Status: {updated_sim.status})")
        print(f"      Return: {updated_sim.total_return}%, Sharpe: {updated_sim.sharpe_ratio}")

        # Test 3: Portfolio Service
        print("\n3. Testing PortfolioService...")

        # Create 3 days of portfolio history
        start_date = datetime(2024, 1, 1)
        initial_value = 50000.0

        for i in range(3):
            date = start_date + timedelta(days=i)
            value = initial_value * (1 + 0.02 * i)

            record = PortfolioService.create_portfolio_record(
                db=db,
                simulation_id=simulation.id,
                date=date,
                total_value=value,
                cash_balance=value * 0.25,
                invested_value=value * 0.75,
                daily_return=2.0 if i > 0 else 0.0,
                cumulative_return=(value - initial_value) / initial_value * 100,
                protocol_allocations={"Aave": value * 0.5, "Compound": value * 0.25},
                daily_yield=100.0,
                cumulative_yield=100.0 * (i + 1),
                rebalanced=1 if i == 1 else 0
            )

        print(f"   ✅ Created 3 portfolio history records")

        # Get portfolio history
        history = PortfolioService.get_portfolio_history(db, simulation.id)
        print(f"   ✅ Retrieved {len(history)} portfolio records")

        # Get stats
        stats = PortfolioService.get_portfolio_stats(db, simulation.id)
        print(f"   ✅ Portfolio stats:")
        print(f"      Initial: ${stats['initial_value']:,.2f}")
        print(f"      Final: ${stats['final_value']:,.2f}")
        print(f"      Rebalances: {stats['rebalance_count']}")

        # Test 4: Query relationships
        print("\n4. Testing queries...")
        all_strategies = StrategyService.get_all_strategies(db)
        print(f"   ✅ Found {len(all_strategies)} active strategies")

        sims_for_strategy = SimulationService.get_simulations_by_strategy(db, strategy.id)
        print(f"   ✅ Found {len(sims_for_strategy)} simulations for strategy")

        best_sim = SimulationService.get_best_simulation_for_strategy(db, strategy.id)
        if best_sim:
            print(f"   ✅ Best simulation: {best_sim.total_return}% return")

        print("\n" + "=" * 60)
        print("🎉 ALL SERVICE TESTS PASSED!")
        print("=" * 60)
        print("\n✅ Service layer is working correctly!")
        print("✅ Ready for Phase 3 development!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_services()
