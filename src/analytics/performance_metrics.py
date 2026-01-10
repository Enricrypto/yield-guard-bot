"""
Performance Metrics Calculator
Calculates financial performance metrics for portfolio simulations
Includes: Total Return, Annualized Return, Max Drawdown, Volatility, Sharpe Ratio
"""

from typing import List, Dict, Optional, Union, Any
from decimal import Decimal
from datetime import datetime, timedelta
import math


class PerformanceMetrics:
    """
    Calculate performance metrics for portfolio simulations

    Metrics calculated:
    - Total Return: Overall percentage gain/loss
    - Annualized Return: Return extrapolated to yearly basis
    - Max Drawdown: Largest peak-to-trough decline
    - Volatility: Standard deviation of returns
    - Sharpe Ratio: Risk-adjusted return metric
    """

    def __init__(self, risk_free_rate: Decimal = Decimal('0.04')):
        """
        Initialize performance metrics calculator

        Args:
            risk_free_rate: Annual risk-free rate (default 4% = 0.04)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_total_return(
        self,
        initial_value: Decimal,
        final_value: Decimal
    ) -> Decimal:
        """
        Calculate total return percentage
        Total Return = (Final Value - Initial Value) / Initial Value

        Args:
            initial_value: Starting portfolio value
            final_value: Ending portfolio value

        Returns:
            Total return as decimal (0.10 = 10%)
        """
        if initial_value <= 0:
            return Decimal('0')

        return (final_value - initial_value) / initial_value

    def calculate_annualized_return(
        self,
        initial_value: Decimal,
        final_value: Decimal,
        days: int
    ) -> Decimal:
        """
        Calculate annualized return
        Annualized Return = (Final Value / Initial Value) ^ (365 / days) - 1

        Args:
            initial_value: Starting portfolio value
            final_value: Ending portfolio value
            days: Number of days in period

        Returns:
            Annualized return as decimal
        """
        if initial_value <= 0 or days <= 0:
            return Decimal('0')

        if final_value <= 0:
            return Decimal('-1')  # Total loss

        # Convert to float for power calculation
        growth_factor = float(final_value / initial_value)
        years = days / 365

        # Annualized return = (growth_factor ^ (1/years)) - 1
        annualized = Decimal(str(math.pow(growth_factor, 1 / years) - 1))

        return annualized

    def calculate_max_drawdown(
        self,
        portfolio_values: List[Decimal]
    ) -> Dict[str, Union[Decimal, int]]:
        """
        Calculate maximum drawdown
        Max Drawdown = (Trough Value - Peak Value) / Peak Value

        Args:
            portfolio_values: Time series of portfolio values

        Returns:
            Dictionary with max_drawdown, peak_value, trough_value
        """
        if not portfolio_values or len(portfolio_values) < 2:
            return {
                'max_drawdown': Decimal('0'),
                'peak_value': Decimal('0'),
                'trough_value': Decimal('0'),
                'peak_index': 0,
                'trough_index': 0
            }

        max_drawdown = Decimal('0')
        peak_value = portfolio_values[0]
        peak_index = 0
        trough_value = portfolio_values[0]
        trough_index = 0
        max_dd_peak = peak_value
        max_dd_trough = trough_value

        for i, value in enumerate(portfolio_values):
            # Update peak if new high
            if value > peak_value:
                peak_value = value
                peak_index = i

            # Calculate drawdown from current peak
            if peak_value > 0:
                drawdown = (value - peak_value) / peak_value

                # Update max drawdown if this is worse
                if drawdown < max_drawdown:
                    max_drawdown = drawdown
                    max_dd_peak = peak_value
                    max_dd_trough = value
                    trough_index = i

        return {
            'max_drawdown': max_drawdown,  # Negative value
            'max_drawdown_pct': abs(max_drawdown * 100),  # Positive percentage
            'peak_value': max_dd_peak,
            'trough_value': max_dd_trough,
            'peak_index': peak_index,
            'trough_index': trough_index
        }

    def calculate_volatility(
        self,
        returns: List[Decimal],
        annualize: bool = True
    ) -> Decimal:
        """
        Calculate volatility (standard deviation of returns)

        Args:
            returns: List of period returns (daily, weekly, etc.)
            annualize: Whether to annualize the volatility

        Returns:
            Volatility as decimal
        """
        if not returns or len(returns) < 2:
            return Decimal('0')

        # Calculate mean return
        mean_return = sum(returns) / len(returns)

        # Calculate variance
        squared_diffs = [(r - mean_return) ** 2 for r in returns]  # type: ignore[operator]
        variance = sum(squared_diffs) / (len(returns) - 1)  # Sample variance

        # Standard deviation
        std_dev = Decimal(str(math.sqrt(float(variance))))

        # Annualize if requested (assuming daily returns)
        if annualize:
            std_dev = std_dev * Decimal(str(math.sqrt(365)))

        return std_dev

    def calculate_sharpe_ratio(
        self,
        returns: List[Decimal],
        annualize: bool = True
    ) -> Decimal:
        """
        Calculate Sharpe ratio (risk-adjusted return)
        Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns

        Args:
            returns: List of period returns
            annualize: Whether to annualize the ratio

        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return Decimal('0')

        # Calculate mean return
        mean_return = sum(returns) / len(returns)

        # Calculate volatility
        volatility = self.calculate_volatility(returns, annualize=False)

        # Minimum volatility threshold to prevent division by near-zero
        # If volatility is too low, the Sharpe ratio becomes meaningless
        min_volatility = Decimal('0.0001')  # 0.01% minimum daily volatility
        if volatility < min_volatility:
            return Decimal('0')

        # Daily risk-free rate
        daily_rf_rate = self.risk_free_rate / Decimal('365')

        # Sharpe ratio
        sharpe = (mean_return - daily_rf_rate) / volatility  # type: ignore[operator]

        # Annualize if requested
        if annualize:
            sharpe = sharpe * Decimal(str(math.sqrt(365)))

        # Cap Sharpe ratio at reasonable values (-10 to +10)
        if sharpe > Decimal('10'):
            sharpe = Decimal('10')
        elif sharpe < Decimal('-10'):
            sharpe = Decimal('-10')

        return sharpe

    def calculate_sortino_ratio(
        self,
        returns: List[Decimal],
        annualize: bool = True
    ) -> Decimal:
        """
        Calculate Sortino ratio (downside risk-adjusted return)
        Only considers downside volatility (negative returns)

        Args:
            returns: List of period returns
            annualize: Whether to annualize the ratio

        Returns:
            Sortino ratio
        """
        if not returns or len(returns) < 2:
            return Decimal('0')

        # Calculate mean return
        mean_return = sum(returns) / len(returns)

        # Calculate downside deviation (only negative returns)
        daily_rf_rate = self.risk_free_rate / Decimal('365')
        downside_diffs = [min(Decimal('0'), r - daily_rf_rate) ** 2 for r in returns]
        downside_variance = sum(downside_diffs) / len(returns)
        downside_dev = Decimal(str(math.sqrt(float(downside_variance))))

        if downside_dev == 0:
            return Decimal('0')

        # Sortino ratio
        sortino = (mean_return - daily_rf_rate) / downside_dev  # type: ignore[operator]

        # Annualize if requested
        if annualize:
            sortino = sortino * Decimal(str(math.sqrt(365)))

        return sortino

    def calculate_calmar_ratio(
        self,
        annualized_return: Decimal,
        max_drawdown: Decimal
    ) -> Decimal:
        """
        Calculate Calmar ratio
        Calmar = Annualized Return / |Max Drawdown|

        Args:
            annualized_return: Annualized return
            max_drawdown: Maximum drawdown (negative value)

        Returns:
            Calmar ratio
        """
        abs_max_dd = abs(max_drawdown)

        if abs_max_dd == 0:
            return Decimal('0')

        return annualized_return / abs_max_dd

    def calculate_win_rate(
        self,
        returns: List[Decimal]
    ) -> Decimal:
        """
        Calculate win rate (percentage of profitable periods)
        Especially useful for stablecoin strategies where consistency matters

        Args:
            returns: List of period returns

        Returns:
            Win rate as decimal (0.75 = 75%)
        """
        if not returns:
            return Decimal('0')

        winning_periods = sum(1 for r in returns if r > 0)
        total_periods = len(returns)

        if total_periods == 0:
            return Decimal('0')

        return Decimal(winning_periods) / Decimal(total_periods)

    def calculate_all_metrics(
        self,
        portfolio_values: List[Decimal],
        returns: Optional[List[Decimal]] = None,
        days: Optional[int] = None
    ) -> Dict:
        """
        Calculate all performance metrics at once

        Args:
            portfolio_values: Time series of portfolio values
            returns: Optional list of returns (calculated if not provided)
            days: Number of days (inferred from portfolio_values if not provided)

        Returns:
            Dictionary with all metrics
        """
        if not portfolio_values or len(portfolio_values) < 2:
            return self._empty_metrics()

        # Infer days if not provided
        if days is None:
            days = len(portfolio_values) - 1

        # Calculate returns if not provided
        if returns is None:
            returns = []
            for i in range(1, len(portfolio_values)):
                if portfolio_values[i - 1] > 0:
                    daily_return = (portfolio_values[i] - portfolio_values[i - 1]) / portfolio_values[i - 1]
                    returns.append(daily_return)
                else:
                    returns.append(Decimal('0'))

        # Calculate metrics
        initial_value = portfolio_values[0]
        final_value = portfolio_values[-1]

        total_return = self.calculate_total_return(initial_value, final_value)
        annualized_return = self.calculate_annualized_return(initial_value, final_value, days)
        max_dd_info = self.calculate_max_drawdown(portfolio_values)
        volatility = self.calculate_volatility(returns, annualize=True)
        sharpe_ratio = self.calculate_sharpe_ratio(returns, annualize=True)
        sortino_ratio = self.calculate_sortino_ratio(returns, annualize=True)
        calmar_ratio = self.calculate_calmar_ratio(annualized_return, max_dd_info['max_drawdown'])  # type: ignore[arg-type]
        win_rate = self.calculate_win_rate(returns)

        return {
            # Basic metrics
            'initial_value': float(initial_value),
            'final_value': float(final_value),
            'days': days,

            # Returns
            'total_return': float(total_return),
            'total_return_pct': float(total_return * 100),
            'annualized_return': float(annualized_return),
            'annualized_return_pct': float(annualized_return * 100),

            # Risk metrics
            'max_drawdown': float(max_dd_info['max_drawdown']),
            'max_drawdown_pct': float(max_dd_info['max_drawdown_pct']),
            'volatility': float(volatility),
            'volatility_pct': float(volatility * 100),

            # Risk-adjusted returns
            'sharpe_ratio': float(sharpe_ratio),
            'sortino_ratio': float(sortino_ratio),
            'calmar_ratio': float(calmar_ratio),

            # Stablecoin-specific metrics
            'win_rate': float(win_rate),
            'win_rate_pct': float(win_rate * 100),

            # Additional info
            'num_periods': len(portfolio_values),
            'num_returns': len(returns),
            'risk_free_rate': float(self.risk_free_rate),
            'risk_free_rate_pct': float(self.risk_free_rate * 100),
        }

    def _empty_metrics(self) -> Dict:
        """Return empty metrics dictionary"""
        return {
            'initial_value': 0,
            'final_value': 0,
            'days': 0,
            'total_return': 0,
            'total_return_pct': 0,
            'annualized_return': 0,
            'annualized_return_pct': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'volatility': 0,
            'volatility_pct': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'calmar_ratio': 0,
            'win_rate': 0,
            'win_rate_pct': 0,
            'num_periods': 0,
            'num_returns': 0,
            'risk_free_rate': 0,
            'risk_free_rate_pct': 0,
        }

    def compare_strategies(
        self,
        strategy_metrics: Dict[str, Dict]
    ) -> Dict:
        """
        Compare multiple strategies and rank them

        Args:
            strategy_metrics: Dict of strategy_name -> metrics

        Returns:
            Comparison report with rankings
        """
        if not strategy_metrics:
            return {'strategies': [], 'best_by_metric': {}}

        # Rank by different metrics
        rankings = {
            'total_return': [],
            'sharpe_ratio': [],
            'sortino_ratio': [],
            'calmar_ratio': [],
            'min_drawdown': []
        }

        for name, metrics in strategy_metrics.items():
            rankings['total_return'].append((name, metrics['total_return']))
            rankings['sharpe_ratio'].append((name, metrics['sharpe_ratio']))
            rankings['sortino_ratio'].append((name, metrics['sortino_ratio']))
            rankings['calmar_ratio'].append((name, metrics['calmar_ratio']))
            rankings['min_drawdown'].append((name, -metrics['max_drawdown']))  # Negative for ranking

        # Sort each ranking (higher is better)
        for metric in rankings:
            rankings[metric].sort(key=lambda x: x[1], reverse=True)

        # Find best strategy for each metric
        best_by_metric = {
            metric: rankings[metric][0][0] if rankings[metric] else None
            for metric in rankings
        }

        # Calculate overall score (average rank across metrics)
        strategy_scores = {}
        for name in strategy_metrics:
            ranks = []
            for metric, ranked_list in rankings.items():
                for rank, (strategy_name, _) in enumerate(ranked_list, 1):
                    if strategy_name == name:
                        ranks.append(rank)
                        break
            strategy_scores[name] = sum(ranks) / len(ranks) if ranks else 999

        # Overall ranking
        overall_ranking = sorted(strategy_scores.items(), key=lambda x: x[1])

        return {
            'strategies': list(strategy_metrics.keys()),
            'best_by_metric': best_by_metric,
            'rankings': rankings,
            'overall_ranking': [name for name, _ in overall_ranking],
            'best_overall': overall_ranking[0][0] if overall_ranking else None
        }


if __name__ == "__main__":
    # Example usage
    print("Performance Metrics Calculator\n")

    # Example portfolio values (simulating growth)
    portfolio_values = [
        Decimal('1000000'),  # Day 0: $1M
        Decimal('1005000'),  # Day 1: +0.5%
        Decimal('1008000'),  # Day 2: +0.3%
        Decimal('1003000'),  # Day 3: -0.5% (small drawdown)
        Decimal('1012000'),  # Day 4: +0.9%
        Decimal('1015000'),  # Day 5: +0.3%
    ]

    metrics = PerformanceMetrics(risk_free_rate=Decimal('0.04'))

    # Calculate all metrics
    results = metrics.calculate_all_metrics(portfolio_values, days=5)

    print("Portfolio Performance Metrics:")
    print(f"  Initial Value: ${results['initial_value']:,.2f}")
    print(f"  Final Value: ${results['final_value']:,.2f}")
    print(f"  Total Return: {results['total_return_pct']:.2f}%")
    print(f"  Annualized Return: {results['annualized_return_pct']:.2f}%")
    print(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    print(f"  Volatility: {results['volatility_pct']:.2f}%")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio: {results['sortino_ratio']:.2f}")
    print(f"  Calmar Ratio: {results['calmar_ratio']:.2f}")
