"""
Unit tests for TreasurySimulator
Tests deposit, portfolio management, health factor, and simulation
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.simulator.treasury_simulator import TreasurySimulator


class TestTreasuryBasics:
    """Test basic treasury functionality"""

    def test_create_treasury(self):
        """Test creating a new treasury"""
        treasury = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Test Treasury",
            min_health_factor=Decimal('1.5')
        )

        assert treasury.initial_capital == Decimal('1000000')
        assert treasury.available_capital == Decimal('1000000')
        assert treasury.name == "Test Treasury"
        assert treasury.min_health_factor == Decimal('1.5')
        assert len(treasury.positions) == 0

    def test_deposit(self):
        """Test depositing capital into a protocol"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        position = treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('100000'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            ltv=Decimal('0.70'),
            liquidation_threshold=Decimal('0.85')
        )

        assert len(treasury.positions) == 1
        assert treasury.available_capital == Decimal('900000')
        assert position.collateral_amount == Decimal('100000')

    def test_deposit_insufficient_funds(self):
        """Test depositing more than available capital"""
        treasury = TreasurySimulator(initial_capital=Decimal('100000'))

        with pytest.raises(ValueError, match="Insufficient capital"):
            treasury.deposit(
                protocol='aave-v3',
                asset_symbol='USDC',
                amount=Decimal('200000'),  # More than available
                supply_apy=Decimal('0.05'),
                borrow_apy=Decimal('0.07')
            )

    def test_deposit_negative_amount(self):
        """Test depositing negative amount"""
        treasury = TreasurySimulator(initial_capital=Decimal('100000'))

        with pytest.raises(ValueError, match="must be positive"):
            treasury.deposit(
                protocol='aave-v3',
                asset_symbol='USDC',
                amount=Decimal('-1000'),
                supply_apy=Decimal('0.05'),
                borrow_apy=Decimal('0.07')
            )

    def test_multiple_deposits(self):
        """Test depositing into multiple protocols"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Deposit into Aave
        treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('300000'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07')
        )

        # Deposit into Compound
        treasury.deposit(
            protocol='compound-v3',
            asset_symbol='USDC',
            amount=Decimal('300000'),
            supply_apy=Decimal('0.06'),
            borrow_apy=Decimal('0.08')
        )

        assert len(treasury.positions) == 2
        assert treasury.available_capital == Decimal('400000')


class TestPortfolioMetrics:
    """Test portfolio-level metrics"""

    def test_get_total_collateral(self):
        """Test calculating total collateral"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('300000'), Decimal('0.05'), Decimal('0.07'))
        treasury.deposit('compound-v3', 'USDC', Decimal('400000'), Decimal('0.06'), Decimal('0.08'))

        total_collateral = treasury.get_total_collateral()
        assert total_collateral == Decimal('700000')

    def test_get_total_debt(self):
        """Test calculating total debt"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.70'))
        treasury.deposit('compound-v3', 'USDC', Decimal('100000'), Decimal('0.06'), Decimal('0.08'), ltv=Decimal('0.60'))

        total_debt = treasury.get_total_debt()
        # Position 1: 70% of 100k = 70k
        # Position 2: 60% of 100k = 60k
        # Total: 130k
        assert total_debt == Decimal('130000')

    def test_get_net_value(self):
        """Test calculating net portfolio value"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.70'))

        net_value = treasury.get_net_value()
        # Collateral (100k) - Debt (70k) + Available (900k) = 930k
        assert net_value == Decimal('930000')

    def test_calculate_health_factor_no_debt(self):
        """Test health factor with no debt"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        hf = treasury.calculate_health_factor()
        assert hf == Decimal('Infinity')

    def test_calculate_health_factor_with_debt(self):
        """Test health factor with debt"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Single position with 70% LTV, 85% liquidation threshold
        treasury.deposit(
            'aave-v3', 'USDC', Decimal('100000'),
            Decimal('0.05'), Decimal('0.07'),
            ltv=Decimal('0.70'),
            liquidation_threshold=Decimal('0.85')
        )

        hf = treasury.calculate_health_factor()
        # HF = (100k * 0.85) / 70k = 1.214...
        assert hf > Decimal('1.2')
        assert hf < Decimal('1.3')

    def test_get_weighted_ltv(self):
        """Test calculating weighted average LTV"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Position 1: 100k at 70% LTV
        treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.70'))

        # Position 2: 200k at 50% LTV
        treasury.deposit('compound-v3', 'USDC', Decimal('200000'), Decimal('0.06'), Decimal('0.08'), ltv=Decimal('0.50'))

        weighted_ltv = treasury.get_weighted_ltv()
        # Weighted = (100k * 0.70 + 200k * 0.50) / 300k = (70k + 100k) / 300k = 0.5667
        expected = (Decimal('100000') * Decimal('0.70') + Decimal('200000') * Decimal('0.50')) / Decimal('300000')
        assert abs(weighted_ltv - expected) < Decimal('0.001')


class TestSimulation:
    """Test simulation functionality"""

    def test_step_no_positions(self):
        """Test simulation step with no positions"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        snapshot = treasury.step(days=Decimal('1'))

        assert snapshot.net_value == Decimal('1000000')
        assert snapshot.daily_yield == Decimal('0')
        assert snapshot.cumulative_yield == Decimal('0')

    def test_step_with_positions(self):
        """Test simulation step with positions"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        snapshot = treasury.step(days=Decimal('1'))

        # Should earn interest
        assert snapshot.daily_yield > Decimal('0')
        assert snapshot.cumulative_yield > Decimal('0')
        assert snapshot.net_value > Decimal('1000000')

    def test_step_with_market_data(self):
        """Test simulation step with market data updates"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        # Market data with updated rates
        market_data = {
            'aave-v3': {
                'USDC': {
                    'supply_apy': Decimal('0.06'),  # Increased from 5% to 6%
                    'borrow_apy': Decimal('0.08')
                }
            }
        }

        snapshot = treasury.step(days=Decimal('1'), market_data=market_data)

        # Position should have updated rates
        assert treasury.positions[0].supply_apy == Decimal('0.06')

    def test_run_simulation(self):
        """Test running multi-day simulation"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('500000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        snapshots = treasury.run_simulation(days=30)

        assert len(snapshots) == 30
        assert snapshots[0].cumulative_yield > Decimal('0')
        assert snapshots[-1].cumulative_yield > snapshots[0].cumulative_yield

    def test_run_simulation_with_generator(self):
        """Test running simulation with market data generator"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        def market_data_generator(day: int):
            # Gradually increase APY
            apy = Decimal('0.05') + Decimal(str(day)) * Decimal('0.001')
            return {
                'aave-v3': {
                    'USDC': {
                        'supply_apy': apy,
                        'borrow_apy': Decimal('0.07')
                    }
                }
            }

        snapshots = treasury.run_simulation(days=10, market_data_generator=market_data_generator)

        assert len(snapshots) == 10
        # Last day should have higher APY than first
        assert treasury.positions[0].supply_apy > Decimal('0.05')


class TestRebalancing:
    """Test portfolio rebalancing"""

    def test_rebalance_close_existing(self):
        """Test rebalancing by closing existing positions"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Initial positions
        treasury.deposit('aave-v3', 'USDC', Decimal('300000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))
        treasury.deposit('compound-v3', 'USDC', Decimal('300000'), Decimal('0.06'), Decimal('0.08'), ltv=Decimal('0'))

        assert len(treasury.positions) == 2
        assert treasury.available_capital == Decimal('400000')

        # Rebalance: close all and open new position
        treasury.rebalance(
            target_positions=[
                {
                    'protocol': 'morpho-v1',
                    'asset_symbol': 'USDC',
                    'amount': Decimal('500000'),
                    'supply_apy': Decimal('0.055'),
                    'borrow_apy': Decimal('0.075'),
                    'ltv': Decimal('0'),
                    'liquidation_threshold': Decimal('0.85')
                }
            ],
            close_existing=True
        )

        assert len(treasury.positions) == 1
        assert treasury.positions[0].protocol == 'morpho-v1'
        assert treasury.available_capital == Decimal('500000')  # 1M - 500k


class TestPortfolioSummary:
    """Test portfolio summary generation"""

    def test_get_portfolio_summary(self):
        """Test getting comprehensive portfolio summary"""
        treasury = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Test Portfolio"
        )

        treasury.deposit('aave-v3', 'USDC', Decimal('300000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.60'))

        # Run some simulation
        treasury.run_simulation(days=30)

        summary = treasury.get_portfolio_summary()

        assert summary['name'] == "Test Portfolio"
        assert summary['initial_capital'] == 1000000.0
        assert summary['available_capital'] == 700000.0
        assert summary['total_collateral'] > 300000.0  # Increased by interest
        assert summary['total_debt'] > 180000.0  # 60% of 300k, increased by interest
        assert summary['num_positions'] == 1
        assert summary['simulation_days'] == 30
        assert summary['cumulative_yield'] > 0
        assert 'created_at' in summary
        assert 'current_date' in summary


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
