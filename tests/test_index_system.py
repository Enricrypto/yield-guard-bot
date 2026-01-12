#!/usr/bin/env python3
"""
Test script for index-based accounting system
"""

from decimal import Decimal
from datetime import datetime
from src.simulator.position import Position
from src.simulator.treasury_simulator import TreasurySimulator
from src.database.db import DatabaseManager, SimulationRun, PortfolioSnapshot


def test_position_index_system():
    """Test Position with index-based accounting"""
    print('=== Test 1: Position Index System ===')

    pos = Position(
        protocol='aave-v3',
        asset_symbol='USDC',
        collateral_amount=Decimal('10000'),
        supply_apy=Decimal('0.05'),
        borrow_apy=Decimal('0.07')
    )

    print(f'Initial: Collateral=${pos.collateral_amount}, Index={pos.share_price_index}, Shares={pos.initial_shares}')

    # Accrue yield for 3 days (no harvest yet)
    for day in range(3):
        net_yield = pos.accrue_yield()
        print(f'Day {day+1}: Accrued ${net_yield:.2f}, Pending=${pos.pending_yield:.2f}, Index={pos.share_price_index:.6f}')

    # Harvest
    harvested = pos.harvest()
    print(f'Harvest: ${harvested:.2f}, New Index={pos.share_price_index:.6f}, Realized=${pos.realized_yield:.2f}')
    print(f'Index Return: {pos.get_index_return() * 100:.4f}%')

    assert pos.share_price_index > Decimal('1.0'), "Index should increase after harvest"
    assert pos.pending_yield == Decimal('0'), "Pending yield should be zero after harvest"
    assert pos.realized_yield > Decimal('0'), "Realized yield should be positive"

    print('✅ Position index system working correctly\n')


def test_simulator_harvest_system():
    """Test Simulator with harvest frequency"""
    print('=== Test 2: Simulator Harvest System ===')

    sim = TreasurySimulator(
        initial_capital=Decimal('100000'),
        harvest_frequency_days=3
    )

    # Open a position
    protocol_data = {
        'protocol': 'aave-v3',
        'asset_symbol': 'USDC',
        'supply_apy': Decimal('0.05'),
        'borrow_apy': Decimal('0.07'),
        'ltv': Decimal('0.80'),
        'liquidation_threshold': Decimal('0.85')
    }

    sim.deposit(
        protocol=protocol_data['protocol'],
        asset_symbol=protocol_data['asset_symbol'],
        amount=Decimal('99900'),  # Leave room for gas fees
        supply_apy=protocol_data['supply_apy'],
        borrow_apy=protocol_data['borrow_apy'],
        ltv=protocol_data['ltv'],
        liquidation_threshold=protocol_data['liquidation_threshold']
    )

    print(f'Initial Portfolio Value: ${sim.get_net_value():.2f}')
    print(f'Harvest Frequency: {sim.harvest_frequency_days} days')

    # Simulate 10 days
    for day in range(1, 11):
        sim.step()
        pos = sim.positions[0]
        print(f'Day {day}: Value=${sim.get_net_value():.2f}, Index={pos.share_price_index:.6f}, Pending=${pos.pending_yield:.2f}, Harvests={sim.num_harvests}')

    print(f'\nFinal Stats:')
    print(f'  Total Harvests: {sim.num_harvests}')
    print(f'  Final Index: {sim.positions[0].share_price_index:.6f}')
    print(f'  Index Return: {sim.positions[0].get_index_return() * 100:.4f}%')
    print(f'  Realized Yield: ${sim.positions[0].realized_yield:.2f}')
    print(f'  Unrealized Yield: ${sim.positions[0].unrealized_yield:.2f}')

    # Assertions
    assert sim.num_harvests == 3, f"Expected 3 harvests in 10 days, got {sim.num_harvests}"
    assert sim.positions[0].share_price_index > Decimal('1.0'), "Index should increase"

    print('✅ Simulator harvest system working correctly\n')


def test_database_save():
    """Test database save with index fields"""
    print('=== Test 3: Database Save with Index Fields ===')

    db = DatabaseManager('data/test_simulations.db')
    db.init_db()

    # Create test simulation run
    sim_run = SimulationRun(
        strategy_name='Test Strategy',
        initial_capital=100000.0,
        simulation_days=30,
        protocols_used='aave-v3',
        total_return=0.05,
        annualized_return=0.60,
        max_drawdown=-0.02,
        sharpe_ratio=2.5,
        final_value=105000.0,
        total_gas_fees=50.0,
        num_rebalances=0,
        sortino_ratio=3.0,
        win_rate=0.95,
        index_return=0.048,  # NEW
        final_index=1.048,  # NEW
        harvest_frequency_days=3,  # NEW
        created_at=datetime.now()
    )

    sim_id = db.save_simulation_run(sim_run)
    print(f'Saved simulation run with ID: {sim_id}')

    # Create test portfolio snapshot
    snapshot = PortfolioSnapshot(
        simulation_id=sim_id,
        day=1,
        net_value=100500.0,
        total_collateral=100000.0,
        total_debt=0.0,
        overall_health_factor=None,
        cumulative_yield=500.0,
        timestamp=datetime.now(),
        share_price_index=1.005,  # NEW
        realized_yield=500.0,  # NEW
        unrealized_yield=0.0,  # NEW
        num_harvests=1  # NEW
    )

    snapshot_id = db.save_portfolio_snapshot(snapshot)
    print(f'Saved portfolio snapshot with ID: {snapshot_id}')

    # Retrieve and verify
    retrieved_sim = db.get_simulation_by_id(sim_id)
    assert retrieved_sim is not None, "Failed to retrieve simulation"
    print(f'Retrieved simulation: index_return={retrieved_sim.index_return}, final_index={retrieved_sim.final_index}')

    snapshots = db.get_snapshots_for_simulation(sim_id)
    assert len(snapshots) == 1, "Failed to retrieve snapshot"
    print(f'Retrieved snapshot: share_price_index={snapshots[0].share_price_index}, realized_yield={snapshots[0].realized_yield}')

    # Cleanup
    db.delete_simulation(sim_id)

    print('✅ Database save/retrieve working correctly\n')


if __name__ == '__main__':
    print('Testing Index-Based Accounting System\n')
    print('=' * 50)

    try:
        test_position_index_system()
        test_simulator_harvest_system()
        test_database_save()

        print('=' * 50)
        print('✅ ALL TESTS PASSED!')

    except AssertionError as e:
        print(f'\n❌ TEST FAILED: {e}')
        exit(1)
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
