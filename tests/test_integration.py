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
        # Adjust amounts to account for $15 gas fee per deposit (3 deposits = $45 total)
        treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('333318'),  # Reduced to account for gas fees
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            ltv=Decimal('0'),  # No leverage
            liquidation_threshold=Decimal('0.85')
        )

        treasury.deposit(
            protocol='compound-v3',
            asset_symbol='USDC',
            amount=Decimal('333318'),  # Reduced to account for gas fees
            supply_apy=Decimal('0.06'),
            borrow_apy=Decimal('0.08'),
            ltv=Decimal('0'),
            liquidation_threshold=Decimal('0.85')
        )

        treasury.deposit(
            protocol='morpho-v1',
            asset_symbol='USDC',
            amount=Decimal('333319'),  # Reduced to account for gas fees
            supply_apy=Decimal('0.055'),
            borrow_apy=Decimal('0.075'),
            ltv=Decimal('0'),
            liquidation_threshold=Decimal('0.85')
        )

        # Step 2: Verify diversification
        assert len(treasury.positions) == 3
        # Total collateral will be less due to gas fees (45) and protocol fees
        # Aave: 333318 - 299.86 (0.09%) - 33.33 (0.01%) = 332984.81
        # Compound: 333318 - 0 (0%) - 33.33 (0.01%) = 333284.67
        # Morpho: 333319 - 166.59 (0.05%) - 33.33 (0.01%) = 333118.91
        # Total: ~999388
        total_collateral = treasury.get_total_collateral()
        assert total_collateral > Decimal('999300')  # After all fees
        assert total_collateral < Decimal('1000000')
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
        # Account for 2 deposits with $15 gas each = $30 total
        # Collateral after fees: 499985 - 449.99 (0.09%) - 50 (0.01%) = 499485.01
        pos1 = treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('499985'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            ltv=Decimal('0.60'),  # 60% leverage
            liquidation_threshold=Decimal('0.85')
        )
        # Max borrow at 60%: 499485 * 0.60 = 299691
        pos1.borrow(Decimal('299691'))

        # Collateral after fees: 499985 - 0 (0%) - 50 (0.01%) = 499935
        pos2 = treasury.deposit(
            protocol='compound-v3',
            asset_symbol='USDC',
            amount=Decimal('499985'),
            supply_apy=Decimal('0.06'),
            borrow_apy=Decimal('0.08'),
            ltv=Decimal('0.60'),
            liquidation_threshold=Decimal('0.85')
        )
        # Max borrow at 60%: 499935 * 0.60 = 299961
        pos2.borrow(Decimal('299961'))

        # Step 2: Verify leverage applied
        total_collateral = treasury.get_total_collateral()
        assert total_collateral > Decimal('999400')  # ~999,420 after fees
        assert total_collateral < Decimal('1000000')
        total_debt = treasury.get_total_debt()
        assert total_debt == Decimal('599652')  # 299691 + 299961

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
        # Account for $15 gas fee: deposit 999985 to stay within 1M budget
        # Collateral after fees: 999985 - 899.89 (0.09%) - 99.99 (0.01%) = 998985.12
        pos = treasury.deposit(
            protocol='aave-v3',
            asset_symbol='USDC',
            amount=Decimal('999985'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            ltv=Decimal('0.70'),
            liquidation_threshold=Decimal('0.85')
        )
        # Max borrow at 70%: ~998985 * 0.70 = 699289.5
        pos.borrow(Decimal('699289'))

        # Verify high leverage
        total_debt = treasury.get_total_debt()
        assert total_debt > Decimal('699000')
        assert total_debt < Decimal('700000')

        health_factor = treasury.calculate_health_factor()
        # HF should still be around 1.2
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

        # Initial: 100% in Aave (account for $15 gas fee)
        treasury.deposit('aave-v3', 'USDC', Decimal('999985'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

        # Run for some time
        treasury.run_simulation(days=30)

        initial_value = treasury.get_net_value()

        # Rebalance: Move to Compound (better rates)
        # Subtract gas fees to ensure we have enough
        rebalance_amount = initial_value - Decimal('50')  # Buffer for gas and fees
        treasury.rebalance(
            target_positions=[
                {
                    'protocol': 'compound-v3',
                    'asset_symbol': 'USDC',
                    'amount': rebalance_amount,
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

        # Account for $15 gas fee
        treasury.deposit('aave-v3', 'USDC', Decimal('999985'), Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))

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

        # Strategy 1: Conservative (account for gas fees)
        treasury_conservative = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Conservative"
        )
        treasury_conservative.deposit('aave-v3', 'USDC', Decimal('999985'),
                                     Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0'))
        snapshots_conservative = treasury_conservative.run_simulation(days=90)

        # Strategy 2: Moderate (account for gas fees)
        treasury_moderate = TreasurySimulator(
            initial_capital=Decimal('1000000'),
            name="Moderate"
        )
        treasury_moderate.deposit('aave-v3', 'USDC', Decimal('999985'),
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

        # Create position with 80% LTV (account for $15 gas fee)
        # Collateral after fees: 99985 - 89.99 (0.09%) - 10 (0.01%) = 99885.01
        pos = treasury.deposit('aave-v3', 'USDC', Decimal('99985'),
                        Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.80'))

        # Max borrow at 80%: 99885 * 0.80 = 79908
        pos.borrow(Decimal('79908'))  # Max allowed

        # Try to borrow more - should fail
        with pytest.raises(ValueError, match="Cannot borrow"):
            pos.borrow(Decimal('10000'))

    def test_repay_too_much_error(self):
        """Test repaying more than debt - should just repay all debt"""
        treasury = TreasurySimulator(initial_capital=Decimal('100000'))

        # Account for $15 gas fee
        # Collateral after fees: 99985 - 89.99 - 10 = 99885.01
        pos = treasury.deposit('aave-v3', 'USDC', Decimal('99985'),
                        Decimal('0.05'), Decimal('0.07'), ltv=Decimal('0.50'))

        # Max borrow at 50%: 99885 * 0.50 = 49942.5
        pos.borrow(Decimal('49942'))  # Borrow 50%

        # Repay more than debt - should succeed and just clear all debt
        pos.repay(Decimal('100000'))

        # All debt should be cleared
        assert pos.debt_amount == Decimal('0')


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
