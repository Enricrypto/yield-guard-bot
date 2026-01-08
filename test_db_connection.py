#!/usr/bin/env python3
"""
Database Connection Test Script
Tests database connection, creates tables, and performs basic CRUD operations
"""

from datetime import datetime, timedelta
from sqlalchemy import text
from src.models import (
    init_db,
    SessionLocal,
    StrategyConfig,
    SimulationRun,
    PortfolioHistory
)


def test_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("1. Testing Database Connection")
    print("=" * 60)

    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def create_tables():
    """Create all database tables"""
    print("\n" + "=" * 60)
    print("2. Creating Database Tables")
    print("=" * 60)

    try:
        init_db()
        print("✅ All tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def test_strategy_insert():
    """Test inserting a StrategyConfig record"""
    print("\n" + "=" * 60)
    print("3. Testing StrategyConfig Insert")
    print("=" * 60)

    try:
        db = SessionLocal()

        # Create a test strategy
        strategy = StrategyConfig(
            name="Conservative Yield Strategy",
            description="Low-risk stablecoin farming strategy",
            risk_level="low",
            allocation_percentage=50.0,
            rebalance_threshold=5.0,
            protocols=["Aave", "Compound"],
            asset_preferences=["USDC", "DAI"],
            max_drawdown=10.0,
            stop_loss_threshold=5.0
        )

        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        print(f"✅ Strategy created with ID: {strategy.id}")
        print(f"   Name: {strategy.name}")
        print(f"   Risk Level: {strategy.risk_level}")
        print(f"   Protocols: {strategy.protocols}")

        db.close()
        return strategy.id
    except Exception as e:
        print(f"❌ Failed to insert strategy: {e}")
        return None


def test_simulation_insert(strategy_id):
    """Test inserting a SimulationRun record"""
    print("\n" + "=" * 60)
    print("4. Testing SimulationRun Insert")
    print("=" * 60)

    try:
        db = SessionLocal()

        # Create a test simulation
        simulation = SimulationRun(
            strategy_id=strategy_id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=10000.0,
            final_value=11500.0,
            total_return=15.0,
            total_return_amount=1500.0,
            max_drawdown=8.5,
            sharpe_ratio=1.85,
            volatility=5.2,
            win_rate=68.5,
            avg_daily_return=0.041,
            best_day=2.5,
            worst_day=-3.2,
            status="completed",
            execution_time=45.3
        )

        db.add(simulation)
        db.commit()
        db.refresh(simulation)

        print(f"✅ Simulation created with ID: {simulation.id}")
        print(f"   Initial Capital: ${simulation.initial_capital:,.2f}")
        print(f"   Final Value: ${simulation.final_value:,.2f}")
        print(f"   Total Return: {simulation.total_return}%")
        print(f"   Sharpe Ratio: {simulation.sharpe_ratio}")

        db.close()
        return simulation.id
    except Exception as e:
        print(f"❌ Failed to insert simulation: {e}")
        return None


def test_portfolio_history_insert(simulation_id):
    """Test inserting PortfolioHistory records"""
    print("\n" + "=" * 60)
    print("5. Testing PortfolioHistory Insert")
    print("=" * 60)

    try:
        db = SessionLocal()

        # Create 5 days of portfolio history
        start_date = datetime(2024, 1, 1)
        initial_value = 10000.0

        for i in range(5):
            date = start_date + timedelta(days=i)
            value = initial_value * (1 + 0.01 * i)  # 1% growth per day

            history = PortfolioHistory(
                simulation_id=simulation_id,
                date=date,
                total_value=value,
                cash_balance=value * 0.2,
                invested_value=value * 0.8,
                daily_return=1.0 if i > 0 else 0.0,
                daily_return_amount=value - (initial_value * (1 + 0.01 * (i-1)) if i > 0 else initial_value),
                cumulative_return=(value - initial_value) / initial_value * 100,
                drawdown=0.0,
                protocol_allocations={"Aave": value * 0.6, "Compound": value * 0.2},
                asset_allocations={"USDC": value * 0.5, "DAI": value * 0.3},
                daily_yield=50.0,
                cumulative_yield=50.0 * (i + 1),
                rebalanced=1 if i == 2 else 0
            )

            db.add(history)

        db.commit()

        # Query back the records
        history_records = db.query(PortfolioHistory).filter(
            PortfolioHistory.simulation_id == simulation_id
        ).all()

        print(f"✅ Created {len(history_records)} portfolio history records")
        print("\n   Sample Records:")
        for record in history_records[:3]:
            print(f"   - {record.date.date()}: ${record.total_value:,.2f} "
                  f"(Return: {record.cumulative_return:.2f}%)")

        db.close()
        return True
    except Exception as e:
        print(f"❌ Failed to insert portfolio history: {e}")
        return False


def test_query():
    """Test querying data back"""
    print("\n" + "=" * 60)
    print("6. Testing Data Query")
    print("=" * 60)

    try:
        db = SessionLocal()

        # Query all strategies
        strategies = db.query(StrategyConfig).all()
        print(f"✅ Found {len(strategies)} strategy(ies)")

        # Query all simulations
        simulations = db.query(SimulationRun).all()
        print(f"✅ Found {len(simulations)} simulation(s)")

        # Query all portfolio history
        history_count = db.query(PortfolioHistory).count()
        print(f"✅ Found {history_count} portfolio history record(s)")

        db.close()
        return True
    except Exception as e:
        print(f"❌ Failed to query data: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🚀 Starting Database Tests\n")

    # Test 1: Connection
    if not test_connection():
        print("\n❌ Database connection failed. Please check your .env file and Docker container.")
        return

    # Test 2: Create tables
    if not create_tables():
        print("\n❌ Failed to create tables.")
        return

    # Test 3: Insert strategy
    strategy_id = test_strategy_insert()
    if not strategy_id:
        print("\n❌ Failed to create strategy.")
        return

    # Test 4: Insert simulation
    simulation_id = test_simulation_insert(strategy_id)
    if not simulation_id:
        print("\n❌ Failed to create simulation.")
        return

    # Test 5: Insert portfolio history
    if not test_portfolio_history_insert(simulation_id):
        print("\n❌ Failed to create portfolio history.")
        return

    # Test 6: Query data
    if not test_query():
        print("\n❌ Failed to query data.")
        return

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\n✅ Database is ready for development!")
    print("✅ All models are working correctly!")
    print("✅ You can now proceed to Phase 3!")


if __name__ == "__main__":
    main()
