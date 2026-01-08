"""
Unit tests for PerformanceMetrics
Tests financial calculations: returns, drawdown, volatility, Sharpe ratio
"""

import pytest
from decimal import Decimal
import math

from src.analytics.performance_metrics import PerformanceMetrics


class TestReturns:
    """Test return calculations"""

    def test_calculate_total_return(self):
        """Test total return calculation"""
        metrics = PerformanceMetrics()

        # 10% gain
        total_return = metrics.calculate_total_return(
            initial_value=Decimal('100000'),
            final_value=Decimal('110000')
        )

        assert total_return == Decimal('0.10')

    def test_calculate_total_return_loss(self):
        """Test total return with loss"""
        metrics = PerformanceMetrics()

        # 5% loss
        total_return = metrics.calculate_total_return(
            initial_value=Decimal('100000'),
            final_value=Decimal('95000')
        )

        assert total_return == Decimal('-0.05')

    def test_calculate_annualized_return(self):
        """Test annualized return calculation"""
        metrics = PerformanceMetrics()

        # 5% gain over 90 days
        annualized = metrics.calculate_annualized_return(
            initial_value=Decimal('100000'),
            final_value=Decimal('105000'),
            days=90
        )

        # Annualized = (1.05 ^ (365/90)) - 1 ≈ 0.2155 (21.55%)
        assert annualized > Decimal('0.20')
        assert annualized < Decimal('0.23')

    def test_calculate_annualized_return_one_year(self):
        """Test annualized return for exactly one year"""
        metrics = PerformanceMetrics()

        annualized = metrics.calculate_annualized_return(
            initial_value=Decimal('100000'),
            final_value=Decimal('110000'),
            days=365
        )

        # Should be same as total return for 1 year
        assert annualized == Decimal('0.10')


class TestMaxDrawdown:
    """Test max drawdown calculations"""

    def test_max_drawdown_no_decline(self):
        """Test max drawdown with only gains"""
        metrics = PerformanceMetrics()

        portfolio_values = [
            Decimal('100000'),
            Decimal('105000'),
            Decimal('110000'),
            Decimal('115000')
        ]

        result = metrics.calculate_max_drawdown(portfolio_values)

        assert result['max_drawdown'] == Decimal('0')
        assert result['max_drawdown_pct'] == Decimal('0')

    def test_max_drawdown_with_decline(self):
        """Test max drawdown with decline"""
        metrics = PerformanceMetrics()

        portfolio_values = [
            Decimal('100000'),  # Start
            Decimal('110000'),  # Peak
            Decimal('105000'),  # Decline
            Decimal('100000'),  # Trough
            Decimal('108000'),  # Recovery
        ]

        result = metrics.calculate_max_drawdown(portfolio_values)

        # Max drawdown from 110k to 100k = -10k / 110k = -9.09%
        assert result['max_drawdown'] < Decimal('0')
        assert result['max_drawdown_pct'] > Decimal('9')
        assert result['max_drawdown_pct'] < Decimal('10')
        assert result['peak_value'] == Decimal('110000')
        assert result['trough_value'] == Decimal('100000')

    def test_max_drawdown_multiple_declines(self):
        """Test max drawdown with multiple declines"""
        metrics = PerformanceMetrics()

        portfolio_values = [
            Decimal('100000'),
            Decimal('110000'),
            Decimal('105000'),  # First decline: -4.5%
            Decimal('112000'),  # New peak
            Decimal('100000'),  # Second decline: -10.7%
        ]

        result = metrics.calculate_max_drawdown(portfolio_values)

        # Max drawdown should be second decline (larger)
        assert result['max_drawdown_pct'] > Decimal('10')
        assert result['peak_value'] == Decimal('112000')


class TestVolatility:
    """Test volatility calculations"""

    def test_volatility_no_variance(self):
        """Test volatility with no variance"""
        metrics = PerformanceMetrics()

        # All returns are same
        returns = [Decimal('0.01')] * 10

        volatility = metrics.calculate_volatility(returns, annualize=False)

        assert volatility == Decimal('0')

    def test_volatility_with_variance(self):
        """Test volatility with variance"""
        metrics = PerformanceMetrics()

        returns = [
            Decimal('0.01'),
            Decimal('-0.005'),
            Decimal('0.02'),
            Decimal('0.005'),
            Decimal('-0.01')
        ]

        volatility = metrics.calculate_volatility(returns, annualize=False)

        assert volatility > Decimal('0')

    def test_volatility_annualized(self):
        """Test annualized volatility"""
        metrics = PerformanceMetrics()

        returns = [Decimal('0.01')] * 30

        vol_daily = metrics.calculate_volatility(returns, annualize=False)
        vol_annual = metrics.calculate_volatility(returns, annualize=True)

        # Annual volatility = daily * sqrt(365)
        expected_ratio = Decimal(str(math.sqrt(365)))
        assert vol_annual > vol_daily


class TestSharpeRatio:
    """Test Sharpe ratio calculations"""

    def test_sharpe_ratio_positive(self):
        """Test Sharpe ratio with positive returns"""
        metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

        # Returns averaging 0.02% per day (7.3% annual)
        returns = [Decimal('0.0002')] * 30

        sharpe = metrics.calculate_sharpe_ratio(returns, annualize=True)

        # Should be positive since returns > risk-free rate
        assert sharpe > Decimal('0')

    def test_sharpe_ratio_negative(self):
        """Test Sharpe ratio with negative excess returns"""
        metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

        # Returns averaging 0.005% per day (1.8% annual) - below risk-free
        returns = [Decimal('0.00005')] * 30

        sharpe = metrics.calculate_sharpe_ratio(returns, annualize=True)

        # Should be negative since returns < risk-free rate
        assert sharpe < Decimal('0')

    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility"""
        metrics = PerformanceMetrics()

        returns = [Decimal('0.01')] * 10

        sharpe = metrics.calculate_sharpe_ratio(returns, annualize=False)

        # Should return 0 when volatility is 0
        assert sharpe == Decimal('0')


class TestSortinoRatio:
    """Test Sortino ratio calculations"""

    def test_sortino_ratio(self):
        """Test Sortino ratio calculation"""
        metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

        # Mix of positive and negative returns
        returns = [
            Decimal('0.01'),
            Decimal('0.02'),
            Decimal('-0.005'),
            Decimal('0.015'),
            Decimal('-0.01'),
            Decimal('0.02')
        ]

        sortino = metrics.calculate_sortino_ratio(returns, annualize=False)

        # Sortino focuses on downside deviation
        assert isinstance(sortino, Decimal)


class TestCalmarRatio:
    """Test Calmar ratio calculations"""

    def test_calmar_ratio(self):
        """Test Calmar ratio calculation"""
        metrics = PerformanceMetrics()

        calmar = metrics.calculate_calmar_ratio(
            annualized_return=Decimal('0.15'),  # 15% annual return
            max_drawdown=Decimal('-0.10')       # -10% max drawdown
        )

        # Calmar = 0.15 / 0.10 = 1.5
        assert calmar == Decimal('1.5')

    def test_calmar_ratio_zero_drawdown(self):
        """Test Calmar ratio with zero drawdown"""
        metrics = PerformanceMetrics()

        calmar = metrics.calculate_calmar_ratio(
            annualized_return=Decimal('0.10'),
            max_drawdown=Decimal('0')
        )

        assert calmar == Decimal('0')


class TestAllMetrics:
    """Test calculate_all_metrics function"""

    def test_calculate_all_metrics(self):
        """Test calculating all metrics at once"""
        metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

        portfolio_values = [
            Decimal('1000000'),
            Decimal('1005000'),
            Decimal('1010000'),
            Decimal('1008000'),
            Decimal('1015000')
        ]

        result = metrics.calculate_all_metrics(portfolio_values, days=4)

        # Check all expected keys present
        assert 'initial_value' in result
        assert 'final_value' in result
        assert 'total_return' in result
        assert 'total_return_pct' in result
        assert 'annualized_return' in result
        assert 'annualized_return_pct' in result
        assert 'max_drawdown' in result
        assert 'max_drawdown_pct' in result
        assert 'volatility' in result
        assert 'sharpe_ratio' in result
        assert 'sortino_ratio' in result
        assert 'calmar_ratio' in result

        # Check values are reasonable
        assert result['initial_value'] == 1000000.0
        assert result['final_value'] == 1015000.0
        assert result['total_return_pct'] > 0
        assert result['days'] == 4

    def test_calculate_all_metrics_empty(self):
        """Test calculating metrics with empty data"""
        metrics = PerformanceMetrics()

        result = metrics.calculate_all_metrics([], days=0)

        assert result['initial_value'] == 0
        assert result['final_value'] == 0
        assert result['total_return'] == 0


class TestStrategyComparison:
    """Test strategy comparison functionality"""

    def test_compare_strategies(self):
        """Test comparing multiple strategies"""
        metrics = PerformanceMetrics()

        strategy_metrics = {
            'Conservative': {
                'total_return': 0.05,
                'sharpe_ratio': 1.2,
                'sortino_ratio': 1.5,
                'calmar_ratio': 0.5,
                'max_drawdown': -0.02
            },
            'Aggressive': {
                'total_return': 0.15,
                'sharpe_ratio': 0.8,
                'sortino_ratio': 1.0,
                'calmar_ratio': 1.5,
                'max_drawdown': -0.10
            },
            'Balanced': {
                'total_return': 0.10,
                'sharpe_ratio': 1.5,
                'sortino_ratio': 1.8,
                'calmar_ratio': 1.0,
                'max_drawdown': -0.05
            }
        }

        comparison = metrics.compare_strategies(strategy_metrics)

        assert 'strategies' in comparison
        assert 'best_by_metric' in comparison
        assert 'overall_ranking' in comparison
        assert 'best_overall' in comparison

        # Check best by total return
        assert comparison['best_by_metric']['total_return'] == 'Aggressive'

        # Check best by Sharpe ratio
        assert comparison['best_by_metric']['sharpe_ratio'] == 'Balanced'

    def test_compare_strategies_empty(self):
        """Test comparing with no strategies"""
        metrics = PerformanceMetrics()

        comparison = metrics.compare_strategies({})

        assert comparison['strategies'] == []
        assert comparison['best_by_metric'] == {}


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
