"""
Integration tests for Yield Guard Bot
Tests full workflows: create → deposit → simulate → analyze
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.simulator.treasury_simulator import TreasurySimulator
from src.simulator.position import Position
from src.analytics.performance_metrics import PerformanceMetrics


class TestConservativeStrategy:
    """Test conservative strategy end-to-end"""

    def test_conservative_no_leverage(self):
        """Test conservative strategy without leverage"""
        # Setup: $1M conservative strategy
        treasury = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Conservative Strategy",
            min_health_factor=Decimal('2.0')
        )

        # Step 1: Deposit into multiple protocols (diversification)
        treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('333333'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            ltv=Decimal('0'),  # No leverage
            liquidation_threshold=Decimal('0.85')
        )

        treasury.deposit(
            protocol='compound-v3',
            asset_symbol='USDC',
            amount=Decimal('333333'),
            supply_apy=Decimal('0.06'),
            borrow_apy=Decimal('0.08'),
            ltv=Decimal('0'),
            liquidation_threshold=Decimal('0.85')
        )

        treasury.deposit(
            protocol='morpho-v1',
            asset_symbol='USDC',
            amount=Decimal('333334'),
            supply_apy=Decimal('0.055'),
            borrow_apy=Decimal('0.075'),
            ltv=Decimal('0'),
            liquidation_threshold=Decimal('0.85')
        )

        # Step 2: Verify diversification
        assert len(treasury.positions) == 3
        assert treasury.get_total_collateral() == Decimal('1000000')
        assert treasury.get_total_debt() == Decimal('0')
        assert treasury.calculate_health_factor() == Decimal('Infinity')

        # Step 3: Run simulation for 90 days
        snapshots = treasury.run_simulation(days=90)

        assert len(snapshots) == 90
        assert snapshots[-1].net_value > Decimal('1000000')  # Made profit
        assert snapshots[-1].cumulative_yield > Decimal('0')
        assert snapshots[-1].overall_health_factor == Decimal('Infinity')  # No debt

        # Step 4: Analyze performance
        metrics_calc = PerformanceMetrics(risk_free_rate=Decimal('0.04'))
        portfolio_values = [Decimal('1000000')] + [s.net_value for s in snapshots]

        metrics = metrics_calc.calculate_all_metrics(portfolio_values, days=90)

        # Verify conservative constraints met
        assert metrics['max_drawdown_pct'] <= 10.0  # Max 10% drawdown
        assert metrics['annualized_return_pct'] > 0  # Positive returns
        assert metrics['annualized_return_pct'] < 20.0  # Conservative returns

        # Step 5: Get portfolio summary
        summary = treasury.get_portfolio_summary()

        assert summary['num_positions'] == 3
        assert summary['total_return_pct'] > 0
        assert summary['simulation_days'] == 90


class TestModerateStrategy:
    """Test moderate strategy with leverage"""

    def test_moderate_with_leverage(self):
        """Test moderate strategy with 60% leverage"""
        # Setup: $1M moderate strategy
        treasury = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Moderate Strategy",
            min_health_factor=Decimal('1.5')
        )

        # Step 1: Deposit with 60% LTV (moderate leverage)
        pos1 = treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('500000'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            ltv=Decimal('0.60'),  # 60% leverage
            liquidation_threshold=Decimal('0.85')
        )
        pos1.borrow(Decimal('300000'))  # Borrow 60%

        pos2 = treasury.deposit(
            protocol='compound-v3',
            asset_symbol='USDC',
            amount=Decimal('500000'),
            supply_apy=Decimal('0.06'),
            borrow_apy=Decimal('0.08'),
            ltv=Decimal('0.60'),
            liquidation_threshold=Decimal('0.85')
        )
        pos2.borrow(Decimal('300000'))  # Borrow 60%

        # Step 2: Verify leverage applied
        assert treasury.get_total_collateral() == Decimal('1000000')
        assert treasury.get_total_debt() == Decimal('600000')  # 60% of 1M

        health_factor = treasury.calculate_health_factor()
        assert health_factor > Decimal('1.0')  # Safe
        assert health_factor < Decimal('2.0')  # Leveraged

        # Step 3: Run simulation
        snapshots = treasury.run_simulation(days=90)

        # Step 4: Verify performance
        final_snapshot = snapshots[-1]

        # With leverage and borrow rate > supply rate, net value will decrease
        # (debt grows faster than collateral due to rate differential)
        # Net value = Collateral - Debt should be positive but less than initial
        assert final_snapshot.net_value > Decimal('0')  # Still solvent
        assert final_snapshot.net_value < treasury.initial_capital  # Lost money due to negative spread

        # Health factor should remain above liquidation threshold
        assert final_snapshot.overall_health_factor > Decimal('1.0')

        # Should have net yield (which is negative due to borrow rate > supply rate)
        assert final_snapshot.cumulative_yield != Decimal('0')


class TestAggressiveStrategy:
    """Test aggressive strategy with high leverage"""

    def test_aggressive_high_leverage(self):
        """Test aggressive strategy with 70% leverage"""
        treasury = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Aggressive Strategy",
            min_health_factor=Decimal('1.2')
        )

        # Deposit with 70% LTV (aggressive)
        pos = treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('1000000'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            ltv=Decimal('0.70'),
            liquidation_threshold=Decimal('0.85')
        )
        pos.borrow(Decimal('700000'))  # Borrow 70%

        # Verify high leverage
        assert treasury.get_total_debt() == Decimal('700000')

        health_factor = treasury.calculate_health_factor()
        # HF = (1M * 0.85) / 700k = 1.214
        assert health_factor > Decimal('1.2')
        assert health_factor < Decimal('1.3')

        # Run short simulation (aggressive strategies need monitoring)
        snapshots = treasury.run_simulation(days=30)

        # Verify health factor stays above minimum
        for snapshot in snapshots:
            assert snapshot.overall_health_factor >= Decimal('1.0')


class TestRebalancing:
    """Test portfolio rebalancing workflow"""

    def test_rebalance_between_protocols(self):
        """Test rebalancing from one protocol to another"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        # Initial: 100% in Aave
        treasury.deposit('aave-v3', 'USDC', Decimal('1000000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        # Run for some time
        treasury.run_simulation(days=30)

        initial_value = treasury.get_net_value()

        # Rebalance: Move to Compound (better rates)
        treasury.rebalance(
            target_positions=[
                {
                    'protocol': 'compound-v3',
                    'asset_symbol': 'USDC',
                    'amount': initial_value,
                    'supply_apy': Decimal('0.06'),  # Better rate
                    'borrow_apy': Decimal('0.08'),
                    'ltv': Decimal('0'),
                    'liquidation_threshold': Decimal('0.85')
                }
            ],
            close_existing=True
        )

        # Verify rebalance
        assert len(treasury.positions) == 1
        assert treasury.positions[0].protocol == 'compound-v3'

        # Continue simulation with new allocation
        treasury.run_simulation(days=30)

        final_value = treasury.get_net_value()
        assert final_value > initial_value  # Continued to grow


class TestMarketDataIntegration:
    """Test simulation with dynamic market data"""

    def test_simulation_with_changing_rates(self):
        """Test simulation with rates that change over time"""
        treasury = TreasurySimulator(initial_capital=Decimal('1000000'))

        treasury.deposit('aave-v3', 'USDC', Decimal('1000000'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        # Market data generator that increases rates over time
        def market_data_generator(day: int):
            # Rates increase from 5% to 7% over 30 days
            supply_apy = Decimal('0.05') + (Decimal('0.02') * Decimal(day) / Decimal('30'))
            return {
                'aave-v3': {
                    'USDC': {
                        'supply_apy': supply_apy,
                        'borrow_apy': Decimal('0.07')
                    }
                }
            }

        snapshots = treasury.run_simulation(
            days=30,
            market_data_generator=market_data_generator
        )

        # Verify rates updated
        assert treasury.positions[0].supply_apy > Decimal('0.05')

        # Verify earnings increased as rates increased
        daily_yields = [s.daily_yield for s in snapshots]
        assert daily_yields[-1] > daily_yields[0]  # Later days earned more


class TestPerformanceAnalysis:
    """Test end-to-end performance analysis workflow"""

    def test_full_analysis_workflow(self):
        """Test complete workflow: create → simulate → analyze → compare"""

        # Strategy 1: Conservative
        treasury_conservative = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Conservative"
        )
        treasury_conservative.deposit('aave-v3', 'USDC', Decimal('1000000'),
                                     Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))
        snapshots_conservative = treasury_conservative.run_simulation(days=90)

        # Strategy 2: Moderate
        treasury_moderate = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Moderate"
        )
        treasury_moderate.deposit('aave-v3', 'USDC', Decimal('1000000'),
                                 Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.60'))
        snapshots_moderate = treasury_moderate.run_simulation(days=90)

        # Analyze both strategies
        metrics_calc = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

        values_conservative = [Decimal('1000000')] + [s.net_value for s in snapshots_conservative]
        values_moderate = [Decimal('1000000')] + [s.net_value for s in snapshots_moderate]

        metrics_conservative = metrics_calc.calculate_all_metrics(values_conservative, days=90)
        metrics_moderate = metrics_calc.calculate_all_metrics(values_moderate, days=90)

        # Compare strategies
        comparison = metrics_calc.compare_strategies({
            'Conservative': metrics_conservative,
            'Moderate': metrics_moderate
        })

        # Verify comparison
        assert 'Conservative' in comparison['strategies']
        assert 'Moderate' in comparison['strategies']
        assert 'best_by_metric' in comparison
        assert 'overall_ranking' in comparison

        # Conservative should have lower risk
        assert metrics_conservative['max_drawdown_pct'] <= metrics_moderate['max_drawdown_pct']


class TestErrorHandling:
    """Test error handling in workflows"""

    def test_insufficient_capital_error(self):
        """Test error when trying to deposit more than available"""
        treasury = TreasurySimulator(initial_capital=Decimal('100000'))

        with pytest.raises(ValueError, match="Insufficient capital"):
            treasury.deposit('aave-v3', 'USDC', Decimal('200000'),
                           Decimal('0.05'), Decimal('0.07'))

    def test_excessive_leverage_error(self):
        """Test error when trying to borrow too much"""
        treasury = TreasurySimulator(initial_capital=Decimal('100000'))

        # Create position with 80% LTV
        pos = treasury.deposit('aave-v3', 'USDC', Decimal('100000'),
                        Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.80'))

        # Borrow up to the max
        pos.borrow(Decimal('80000'))  # Max allowed

        # Try to borrow more - should fail
        with pytest.raises(ValueError, match="Cannot borrow"):
            pos.borrow(Decimal('10000'))

    def test_repay_too_much_error(self):
        """Test repaying more than debt - should just repay all debt"""
        treasury = TreasurySimulator(initial_capital=Decimal('100000'))

        pos = treasury.deposit('aave-v3', 'USDC', Decimal('100000'),
                        Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.50'))

        pos.borrow(Decimal('50000'))  # Borrow 50%

        # Repay more than debt - should succeed and just clear all debt
        pos.repay(Decimal('100000'))

        # All debt should be cleared
        assert pos.debt_amount == Decimal('0')  # Debt is only 50k


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
