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
        # 1000000 - 100000 (deposited) - 15 (gas fee) = 899985
        assert treasury.available_capital == Decimal('899985')
        # Collateral after protocol fee (0.09%) and slippage (0.01%): 100000 - 90 - 10 = 99900
        assert position.collateral_amount == Decimal('99900')

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
        # 1000000 - 300000 - 15 (gas) - 300000 - 15 (gas) = 399970
        assert treasury.available_capital == Decimal('399970')


class TestPortfolioMetrics:
    """Test portfolio-level metrics"""

    def test_get_total_collateral(self):
        """Test calculating total collateral"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('300000'), Decimal('0.05'), Decimal('0.07'))
        treasury.deposit('compound-v3', 'USDC', Decimal('400000'), Decimal('0.06'), Decimal('0.08'))

        total_collateral = treasury.get_total_collateral()
        # Aave: 300000 - 270 (0.09%) - 30 (0.01%) = 299700
        # Compound: 400000 - 0 (0%) - 40 (0.01%) = 399960
        # Total: 699660
        assert total_collateral == Decimal('699660')

    def test_get_total_debt(self):
        """Test calculating total debt"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Create positions and manually borrow
        # pos1 collateral: 100000 - 90 (0.09%) - 10 (0.01%) = 99900
        pos1 = treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.70'))
        # Max borrow at 70% LTV: 99900 * 0.70 = 69930
        pos1.borrow(Decimal('69930'))

        # pos2 collateral: 100000 - 0 (0%) - 10 (0.01%) = 99990
        pos2 = treasury.deposit('compound-v3', 'USDC', Decimal('100000'), Decimal('0.06'), Decimal('0.08'), ltv=Decimal('0.60'))
        # Max borrow at 60% LTV: 99990 * 0.60 = 59994
        pos2.borrow(Decimal('59994'))

        total_debt = treasury.get_total_debt()
        assert total_debt == Decimal('129924')

    def test_get_net_value(self):
        """Test calculating net portfolio value"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Collateral: 100000 - 90 - 10 = 99900
        pos = treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.70'))
        # Max borrow: 99900 * 0.70 = 69930
        pos.borrow(Decimal('69930'))

        net_value = treasury.get_net_value()
        # Collateral (99900) - Debt (69930) + Available (1000000 - 100000 - 15 gas = 899985) = 929955
        assert net_value == Decimal('929955')

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
        # Collateral: 100000 - 90 - 10 = 99900
        pos = treasury.deposit(
            'aave-v3', 'USDC', Decimal('100000'),
            Decimal('0.05'), Decimal('0.07'),
            ltv=Decimal('0.70'),
            liquidation_threshold=Decimal('0.85')
        )
        # Max borrow: 99900 * 0.70 = 69930
        pos.borrow(Decimal('69930'))

        hf = treasury.calculate_health_factor()
        # HF = (99900 * 0.85) / 69930 = 1.214...
        assert hf > Decimal('1.2')
        assert hf < Decimal('1.3')

    def test_get_weighted_ltv(self):
        """Test calculating weighted average LTV"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Position 1: 100k - 90 - 10 = 99900 collateral, borrow at 70% LTV
        pos1 = treasury.deposit('aave-v3', 'USDC', Decimal('100000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.70'))
        pos1.borrow(Decimal('69930'))  # 99900 * 0.70

        # Position 2: 200k - 180 - 20 = 199800 collateral, borrow at 50% LTV
        pos2 = treasury.deposit('compound-v3', 'USDC', Decimal('200000'), Decimal('0.06'), Decimal('0.08'), ltv=Decimal('0.50'))
        pos2.borrow(Decimal('99900'))  # 199800 * 0.50

        weighted_ltv = treasury.get_weighted_ltv()
        # Weighted = (99900 * 0.70 + 199800 * 0.50) / (99900 + 199800) = (69930 + 99900) / 299700 = 0.5667
        expected = (Decimal('99900') * Decimal('0.70') + Decimal('199800') * Decimal('0.50')) / Decimal('299700')
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

        # Should earn interest (daily_yield is positive)
        assert snapshot.daily_yield > Decimal('0')
        # Net value: collateral (99900) + available (899985) = 999885
        assert snapshot.net_value == Decimal('999885')
        assert snapshot.net_value < Decimal('1000000')

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
        # After 30 days, cumulative yield should be positive and growing
        assert snapshots[-1].cumulative_yield > Decimal('0')
        # Daily yield should be positive
        assert snapshots[-1].daily_yield > Decimal('0')

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
        # 1000000 - 300000 - 15 - 300000 - 15 = 399970
        assert treasury.available_capital == Decimal('399970')

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
        # After rebalance with gas fees, available capital will be less than simple 500k
        # The exact amount depends on withdraw + deposit gas fees
        assert treasury.available_capital < Decimal('500000')
        assert treasury.available_capital > Decimal('490000')


class TestPortfolioSummary:
    """Test portfolio summary generation"""

    def test_get_portfolio_summary(self):
        """Test getting comprehensive portfolio summary"""
        treasury = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Test Portfolio"
        )

        # Collateral after fees: 300000 - 270 - 30 = 299700
        pos = treasury.deposit('aave-v3', 'USDC', Decimal('300000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.60'))
        # Max borrow: 299700 * 0.60 = 179820
        pos.borrow(Decimal('179820'))

        # Run some simulation
        treasury.run_simulation(days=30)

        summary = treasury.get_portfolio_summary()

        assert summary['name'] == "Test Portfolio"
        assert summary['initial_capital'] == 1000000.0
        # 1000000 - 300000 - 15 (gas) = 699985
        assert summary['available_capital'] == 699985.0
        assert summary['total_collateral'] > 299700.0  # Increased by interest
        # Debt may not increase significantly in 30 days with 7% borrow APY (only ~3.45 added)
        assert summary['total_debt'] >= 179820.0
        assert summary['num_positions'] == 1
        assert summary['simulation_days'] == 30
        assert summary['cumulative_yield'] != 0  # Net yield (could be positive or negative)
        assert 'created_at' in summary
        assert 'current_date' in summary


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
