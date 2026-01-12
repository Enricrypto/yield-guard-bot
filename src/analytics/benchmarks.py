"""
Benchmark Data Provider
Provides standard DeFi and TradFi benchmarks for performance comparison
"""

from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class BenchmarkType(Enum):
    """Standard benchmark types"""
    ETH_STAKING = "eth_staking"
    AAVE_USDC = "aave_usdc"
    TREASURY_BILL = "treasury_bill"
    COMPOUND_USDC = "compound_usdc"
    MORPHO_USDC = "morpho_usdc"


@dataclass
class Benchmark:
    """Benchmark definition"""
    name: str
    description: str
    type: BenchmarkType
    typical_apy: Decimal  # Typical/historical APY
    risk_level: str  # "Low", "Medium", "High"
    volatility: Decimal  # Historical volatility
    category: str  # "DeFi", "TradFi", "Crypto"


class BenchmarkProvider:
    """
    Provides benchmark data for performance comparison

    Benchmarks:
    1. ETH Staking (~3-4% APY, medium risk)
    2. Aave USDC Supply (~2-5% APY, low risk)
    3. US Treasury Bills (~4-5% APY, ultra-low risk)
    4. Compound USDC (~2-4% APY, low risk)
    5. Morpho USDC (~4-6% APY, low risk)
    """

    # Standard benchmark definitions (2025 typical rates)
    BENCHMARKS: Dict[BenchmarkType, Benchmark] = {
        BenchmarkType.ETH_STAKING: Benchmark(
            name="ETH Staking",
            description="Ethereum proof-of-stake rewards",
            type=BenchmarkType.ETH_STAKING,
            typical_apy=Decimal('0.035'),  # 3.5%
            risk_level="Medium",
            volatility=Decimal('0.15'),  # 15% - ETH price volatility
            category="Crypto"
        ),
        BenchmarkType.AAVE_USDC: Benchmark(
            name="Aave V3 USDC Supply",
            description="Base lending rate on Aave",
            type=BenchmarkType.AAVE_USDC,
            typical_apy=Decimal('0.035'),  # 3.5%
            risk_level="Low",
            volatility=Decimal('0.005'),  # 0.5% - very stable
            category="DeFi"
        ),
        BenchmarkType.TREASURY_BILL: Benchmark(
            name="US Treasury Bills (3-month)",
            description="Risk-free rate proxy",
            type=BenchmarkType.TREASURY_BILL,
            typical_apy=Decimal('0.045'),  # 4.5%
            risk_level="Ultra-Low",
            volatility=Decimal('0.001'),  # 0.1% - nearly zero
            category="TradFi"
        ),
        BenchmarkType.COMPOUND_USDC: Benchmark(
            name="Compound V3 USDC Supply",
            description="Base lending rate on Compound",
            type=BenchmarkType.COMPOUND_USDC,
            typical_apy=Decimal('0.030'),  # 3.0%
            risk_level="Low",
            volatility=Decimal('0.005'),  # 0.5%
            category="DeFi"
        ),
        BenchmarkType.MORPHO_USDC: Benchmark(
            name="Morpho USDC Supply",
            description="Optimized Aave/Compound rates",
            type=BenchmarkType.MORPHO_USDC,
            typical_apy=Decimal('0.050'),  # 5.0%
            risk_level="Low",
            volatility=Decimal('0.007'),  # 0.7%
            category="DeFi"
        ),
    }

    @classmethod
    def get_benchmark(cls, benchmark_type: BenchmarkType) -> Benchmark:
        """Get benchmark definition"""
        return cls.BENCHMARKS[benchmark_type]

    @classmethod
    def get_all_benchmarks(cls) -> List[Benchmark]:
        """Get all available benchmarks"""
        return list(cls.BENCHMARKS.values())

    @classmethod
    def get_benchmarks_by_category(cls, category: str) -> List[Benchmark]:
        """Get benchmarks filtered by category"""
        return [b for b in cls.BENCHMARKS.values() if b.category == category]

    @classmethod
    def generate_benchmark_returns(
        cls,
        benchmark_type: BenchmarkType,
        days: int,
        daily_volatility: Optional[Decimal] = None
    ) -> List[Decimal]:
        """
        Generate synthetic benchmark returns for comparison

        Args:
            benchmark_type: Type of benchmark
            days: Number of days to generate
            daily_volatility: Optional override for volatility

        Returns:
            List of daily returns (as decimals)
        """
        import random

        benchmark = cls.get_benchmark(benchmark_type)

        # Use provided volatility or benchmark's default
        vol = daily_volatility if daily_volatility else benchmark.volatility

        # Convert annual to daily
        daily_apy = benchmark.typical_apy / Decimal('365')
        daily_vol = vol / Decimal('365').sqrt() if vol > 0 else Decimal('0')

        # Generate returns with mean = daily_apy, std = daily_vol
        returns = []
        for _ in range(days):
            # Simple random walk with drift
            noise = Decimal(str(random.gauss(0, float(daily_vol))))
            daily_return = daily_apy + noise
            returns.append(daily_return)

        return returns

    @classmethod
    def calculate_benchmark_index(
        cls,
        benchmark_type: BenchmarkType,
        days: int
    ) -> List[Decimal]:
        """
        Calculate benchmark share price index over time

        Args:
            benchmark_type: Type of benchmark
            days: Number of days

        Returns:
            List of index values (starts at 1.0)
        """
        returns = cls.generate_benchmark_returns(benchmark_type, days)

        # Build index from returns
        index_values = [Decimal('1.0')]

        for daily_return in returns:
            new_index = index_values[-1] * (Decimal('1.0') + daily_return)
            index_values.append(new_index)

        return index_values


class PerformanceComparator:
    """
    Compares strategy performance against benchmarks
    Calculates alpha, information ratio, and other comparative metrics
    """

    @staticmethod
    def calculate_alpha(
        strategy_return: Decimal,
        benchmark_return: Decimal
    ) -> Decimal:
        """
        Calculate alpha (excess return over benchmark)

        Alpha = Strategy Return - Benchmark Return

        Args:
            strategy_return: Total strategy return
            benchmark_return: Total benchmark return

        Returns:
            Alpha as decimal (0.02 = 2% excess return)
        """
        return strategy_return - benchmark_return

    @staticmethod
    def calculate_annualized_alpha(
        strategy_apy: Decimal,
        benchmark_apy: Decimal
    ) -> Decimal:
        """Calculate annualized alpha"""
        return strategy_apy - benchmark_apy

    @staticmethod
    def calculate_tracking_error(
        strategy_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Decimal:
        """
        Calculate tracking error (volatility of excess returns)

        Args:
            strategy_returns: Daily strategy returns
            benchmark_returns: Daily benchmark returns

        Returns:
            Tracking error (annualized standard deviation)
        """
        if len(strategy_returns) != len(benchmark_returns):
            raise ValueError("Return series must have same length")

        # Calculate excess returns
        excess_returns = [
            s - b for s, b in zip(strategy_returns, benchmark_returns)
        ]

        if not excess_returns:
            return Decimal('0')

        # Calculate standard deviation
        mean_excess = Decimal(str(sum(excess_returns))) / Decimal(str(len(excess_returns)))
        variance = Decimal(str(sum((r - mean_excess) ** 2 for r in excess_returns))) / Decimal(str(len(excess_returns)))
        std_dev = variance.sqrt() if variance > 0 else Decimal('0')

        # Annualize (daily to annual)
        annualized_te = std_dev * Decimal('365').sqrt()

        return annualized_te

    @staticmethod
    def calculate_information_ratio(
        strategy_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Decimal:
        """
        Calculate information ratio (risk-adjusted alpha)

        IR = Alpha / Tracking Error

        Interpretation:
        - IR > 0.5: Good active management
        - IR > 1.0: Excellent active management
        - IR < 0: Underperforming benchmark

        Args:
            strategy_returns: Daily strategy returns
            benchmark_returns: Daily benchmark returns

        Returns:
            Information ratio
        """
        if len(strategy_returns) != len(benchmark_returns):
            raise ValueError("Return series must have same length")

        if not strategy_returns:
            return Decimal('0')

        # Calculate average excess return
        excess_returns = [
            s - b for s, b in zip(strategy_returns, benchmark_returns)
        ]
        avg_excess = Decimal(str(sum(excess_returns))) / Decimal(str(len(excess_returns)))

        # Calculate tracking error
        tracking_error = PerformanceComparator.calculate_tracking_error(
            strategy_returns,
            benchmark_returns
        )

        if tracking_error == 0:
            return Decimal('0')

        # Annualize average excess return
        annualized_excess = avg_excess * Decimal('365')

        # Information ratio
        return annualized_excess / tracking_error

    @staticmethod
    def calculate_downside_deviation(
        strategy_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Decimal:
        """
        Calculate downside deviation relative to benchmark
        Only considers periods where strategy underperforms

        Args:
            strategy_returns: Daily strategy returns
            benchmark_returns: Daily benchmark returns

        Returns:
            Downside deviation (annualized)
        """
        excess_returns = [
            s - b for s, b in zip(strategy_returns, benchmark_returns)
        ]

        # Only negative excess returns
        downside_returns = [r for r in excess_returns if r < 0]

        if not downside_returns:
            return Decimal('0')

        # Downside semi-variance
        mean_downside = Decimal(str(sum(downside_returns))) / Decimal(str(len(downside_returns)))
        downside_variance = Decimal(str(sum(
            (r - mean_downside) ** 2 for r in downside_returns
        ))) / Decimal(str(len(downside_returns)))

        downside_std = downside_variance.sqrt() if downside_variance > 0 else Decimal('0')

        # Annualize
        return downside_std * Decimal('365').sqrt()

    @staticmethod
    def calculate_upside_capture(
        strategy_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Decimal:
        """
        Calculate upside capture ratio
        Measures how well strategy captures benchmark gains

        Returns:
            Ratio (1.2 = captures 120% of benchmark gains)
        """
        # Filter to periods where benchmark is positive
        upside_pairs = [
            (s, b) for s, b in zip(strategy_returns, benchmark_returns)
            if b > 0
        ]

        if not upside_pairs:
            return Decimal('1.0')

        strategy_upside = Decimal(str(sum(s for s, _ in upside_pairs))) / Decimal(str(len(upside_pairs)))
        benchmark_upside = Decimal(str(sum(b for _, b in upside_pairs))) / Decimal(str(len(upside_pairs)))

        if benchmark_upside == 0:
            return Decimal('1.0')

        return strategy_upside / benchmark_upside

    @staticmethod
    def calculate_downside_capture(
        strategy_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Decimal:
        """
        Calculate downside capture ratio
        Measures how much of benchmark losses the strategy captures

        Returns:
            Ratio (0.8 = captures only 80% of benchmark losses - good!)
        """
        # Filter to periods where benchmark is negative
        downside_pairs = [
            (s, b) for s, b in zip(strategy_returns, benchmark_returns)
            if b < 0
        ]

        if not downside_pairs:
            return Decimal('1.0')

        strategy_downside = Decimal(str(sum(s for s, _ in downside_pairs))) / Decimal(str(len(downside_pairs)))
        benchmark_downside = Decimal(str(sum(b for _, b in downside_pairs))) / Decimal(str(len(downside_pairs)))

        if benchmark_downside == 0:
            return Decimal('1.0')

        return strategy_downside / benchmark_downside

    @classmethod
    def generate_comparison_report(
        cls,
        strategy_returns: List[Decimal],
        benchmark_returns: List[Decimal],
        strategy_apy: Decimal,
        benchmark_apy: Decimal,
        benchmark_name: str
    ) -> Dict:
        """
        Generate comprehensive comparison report

        Returns:
            Dictionary with all comparative metrics
        """
        alpha = cls.calculate_alpha(
            strategy_returns[-1] if strategy_returns else Decimal('0'),
            benchmark_returns[-1] if benchmark_returns else Decimal('0')
        )

        annualized_alpha = cls.calculate_annualized_alpha(strategy_apy, benchmark_apy)

        tracking_error = cls.calculate_tracking_error(strategy_returns, benchmark_returns)
        information_ratio = cls.calculate_information_ratio(strategy_returns, benchmark_returns)

        upside_capture = cls.calculate_upside_capture(strategy_returns, benchmark_returns)
        downside_capture = cls.calculate_downside_capture(strategy_returns, benchmark_returns)

        return {
            'benchmark_name': benchmark_name,
            'alpha': float(alpha),
            'alpha_pct': float(alpha * 100),
            'annualized_alpha': float(annualized_alpha),
            'annualized_alpha_pct': float(annualized_alpha * 100),
            'tracking_error': float(tracking_error),
            'tracking_error_pct': float(tracking_error * 100),
            'information_ratio': float(information_ratio),
            'upside_capture': float(upside_capture),
            'upside_capture_pct': float(upside_capture * 100),
            'downside_capture': float(downside_capture),
            'downside_capture_pct': float(downside_capture * 100),
            'strategy_apy': float(strategy_apy),
            'strategy_apy_pct': float(strategy_apy * 100),
            'benchmark_apy': float(benchmark_apy),
            'benchmark_apy_pct': float(benchmark_apy * 100),
        }


if __name__ == "__main__":
    # Example usage
    print("Available Benchmarks:\n")

    for benchmark in BenchmarkProvider.get_all_benchmarks():
        print(f"{benchmark.name} ({benchmark.category})")
        print(f"  APY: {benchmark.typical_apy * 100:.2f}%")
        print(f"  Risk: {benchmark.risk_level}")
        print(f"  Volatility: {benchmark.volatility * 100:.2f}%")
        print(f"  Description: {benchmark.description}\n")

    # Generate sample comparison
    print("\n" + "="*50)
    print("Sample Performance Comparison")
    print("="*50 + "\n")

    # Simulate 30 days
    days = 30

    # Generate benchmark returns
    benchmark_returns = BenchmarkProvider.generate_benchmark_returns(
        BenchmarkType.AAVE_USDC,
        days
    )

    # Simulate strategy returns (slightly better)
    strategy_returns = [r * Decimal('1.2') for r in benchmark_returns]

    # Generate comparison report
    report = PerformanceComparator.generate_comparison_report(
        strategy_returns=strategy_returns,
        benchmark_returns=benchmark_returns,
        strategy_apy=Decimal('0.042'),  # 4.2%
        benchmark_apy=Decimal('0.035'),  # 3.5%
        benchmark_name="Aave V3 USDC Supply"
    )

    print(f"Benchmark: {report['benchmark_name']}")
    print(f"Strategy APY: {report['strategy_apy_pct']:.2f}%")
    print(f"Benchmark APY: {report['benchmark_apy_pct']:.2f}%")
    print(f"\nAlpha: {report['annualized_alpha_pct']:.2f}%")
    print(f"Information Ratio: {report['information_ratio']:.2f}")
    print(f"Tracking Error: {report['tracking_error_pct']:.2f}%")
    print(f"Upside Capture: {report['upside_capture_pct']:.1f}%")
    print(f"Downside Capture: {report['downside_capture_pct']:.1f}%")
