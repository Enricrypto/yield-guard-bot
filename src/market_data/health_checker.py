"""
Health Checker
Validates data quality and checks system health
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from decimal import Decimal
import statistics


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    check_name: str
    passed: bool
    message: str
    severity: str  # 'info', 'warning', 'error'
    timestamp: datetime


class HealthChecker:
    """
    Validates data quality and system health
    """

    def __init__(self):
        """Initialize health checker"""
        self.results: List[HealthCheckResult] = []

    def check_apy_sanity(
        self,
        supply_apy: Decimal,
        borrow_apy: Decimal,
        asset_symbol: str = 'Unknown'
    ) -> HealthCheckResult:
        """
        Check if APY values are within reasonable ranges

        Args:
            supply_apy: Supply APY (as decimal, e.g., 0.05 = 5%)
            borrow_apy: Borrow APY
            asset_symbol: Asset symbol for reporting

        Returns:
            HealthCheckResult
        """
        issues = []

        # Check supply APY range (0.01% to 50%)
        if supply_apy < Decimal('0.0001'):
            issues.append(f"Supply APY too low: {supply_apy*100:.2f}%")
        elif supply_apy > Decimal('0.5'):
            issues.append(f"Supply APY suspiciously high: {supply_apy*100:.2f}%")

        # Check borrow APY range (0.01% to 100%)
        if borrow_apy < Decimal('0.0001'):
            issues.append(f"Borrow APY too low: {borrow_apy*100:.2f}%")
        elif borrow_apy > Decimal('1.0'):
            issues.append(f"Borrow APY suspiciously high: {borrow_apy*100:.2f}%")

        # Check spread (borrow should be higher than supply)
        if borrow_apy <= supply_apy:
            issues.append(f"Invalid spread: borrow ({borrow_apy*100:.2f}%) <= supply ({supply_apy*100:.2f}%)")

        # Check spread magnitude
        spread = borrow_apy - supply_apy
        if spread < Decimal('0.001'):  # Less than 0.1% spread
            issues.append(f"Spread too narrow: {spread*100:.2f}%")

        if issues:
            result = HealthCheckResult(
                check_name=f"APY Sanity Check - {asset_symbol}",
                passed=False,
                message="; ".join(issues),
                severity='error',
                timestamp=datetime.now()
            )
        else:
            result = HealthCheckResult(
                check_name=f"APY Sanity Check - {asset_symbol}",
                passed=True,
                message=f"APYs within normal range (Supply: {supply_apy*100:.2f}%, Borrow: {borrow_apy*100:.2f}%)",
                severity='info',
                timestamp=datetime.now()
            )

        self.results.append(result)
        return result

    def check_tvl_sanity(
        self,
        tvl: Decimal,
        protocol: str = 'Unknown',
        min_tvl: Decimal = Decimal('1000000'),  # $1M minimum
        max_tvl: Decimal = Decimal('100000000000')  # $100B maximum
    ) -> HealthCheckResult:
        """
        Check if TVL is within reasonable ranges

        Args:
            tvl: Total Value Locked in USD
            protocol: Protocol name
            min_tvl: Minimum acceptable TVL
            max_tvl: Maximum reasonable TVL

        Returns:
            HealthCheckResult
        """
        if tvl < min_tvl:
            result = HealthCheckResult(
                check_name=f"TVL Sanity Check - {protocol}",
                passed=False,
                message=f"TVL too low: ${tvl:,.0f} < ${min_tvl:,.0f}",
                severity='warning',
                timestamp=datetime.now()
            )
        elif tvl > max_tvl:
            result = HealthCheckResult(
                check_name=f"TVL Sanity Check - {protocol}",
                passed=False,
                message=f"TVL suspiciously high: ${tvl:,.0f} > ${max_tvl:,.0f}",
                severity='warning',
                timestamp=datetime.now()
            )
        else:
            result = HealthCheckResult(
                check_name=f"TVL Sanity Check - {protocol}",
                passed=True,
                message=f"TVL within normal range: ${tvl:,.0f}",
                severity='info',
                timestamp=datetime.now()
            )

        self.results.append(result)
        return result

    def check_data_freshness(
        self,
        data_timestamp: datetime,
        max_age_minutes: int = 60
    ) -> HealthCheckResult:
        """
        Check if data is fresh enough

        Args:
            data_timestamp: When the data was fetched
            max_age_minutes: Maximum acceptable age in minutes

        Returns:
            HealthCheckResult
        """
        age = datetime.now() - data_timestamp
        age_minutes = age.total_seconds() / 60

        if age_minutes > max_age_minutes:
            result = HealthCheckResult(
                check_name="Data Freshness Check",
                passed=False,
                message=f"Data is stale: {age_minutes:.0f} minutes old (max: {max_age_minutes})",
                severity='warning',
                timestamp=datetime.now()
            )
        else:
            result = HealthCheckResult(
                check_name="Data Freshness Check",
                passed=True,
                message=f"Data is fresh: {age_minutes:.0f} minutes old",
                severity='info',
                timestamp=datetime.now()
            )

        self.results.append(result)
        return result

    def check_volatility(
        self,
        values: List[Decimal],
        max_stddev: Decimal = Decimal('0.1')  # 10% max standard deviation
    ) -> HealthCheckResult:
        """
        Check if volatility is within acceptable ranges

        Args:
            values: List of values to check
            max_stddev: Maximum acceptable standard deviation

        Returns:
            HealthCheckResult
        """
        if len(values) < 2:
            result = HealthCheckResult(
                check_name="Volatility Check",
                passed=False,
                message="Not enough data points for volatility check",
                severity='warning',
                timestamp=datetime.now()
            )
        else:
            float_values = [float(v) for v in values]
            mean = statistics.mean(float_values)
            stddev = statistics.stdev(float_values)
            relative_stddev = stddev / mean if mean != 0 else float('inf')

            if relative_stddev > float(max_stddev):
                result = HealthCheckResult(
                    check_name="Volatility Check",
                    passed=False,
                    message=f"High volatility detected: {relative_stddev*100:.1f}% stddev",
                    severity='warning',
                    timestamp=datetime.now()
                )
            else:
                result = HealthCheckResult(
                    check_name="Volatility Check",
                    passed=True,
                    message=f"Volatility within normal range: {relative_stddev*100:.1f}% stddev",
                    severity='info',
                    timestamp=datetime.now()
                )

        self.results.append(result)
        return result

    def check_protocol_comparison(
        self,
        aave_apy: Decimal,
        morpho_apy: Decimal,
        expected_boost_range: tuple = (Decimal('0.001'), Decimal('0.05'))  # 0.1% to 5% boost
    ) -> HealthCheckResult:
        """
        Check if Morpho APY boost over Aave is reasonable

        Args:
            aave_apy: Aave supply APY
            morpho_apy: Morpho supply APY
            expected_boost_range: Expected boost range (min, max)

        Returns:
            HealthCheckResult
        """
        boost = morpho_apy - aave_apy
        min_boost, max_boost = expected_boost_range

        if boost < Decimal('0'):
            result = HealthCheckResult(
                check_name="Protocol Comparison Check",
                passed=False,
                message=f"Morpho APY lower than Aave: {boost*100:+.2f}%",
                severity='warning',
                timestamp=datetime.now()
            )
        elif boost < min_boost:
            result = HealthCheckResult(
                check_name="Protocol Comparison Check",
                passed=True,
                message=f"Morpho boost very small: +{boost*100:.2f}%",
                severity='info',
                timestamp=datetime.now()
            )
        elif boost > max_boost:
            result = HealthCheckResult(
                check_name="Protocol Comparison Check",
                passed=False,
                message=f"Morpho boost suspiciously high: +{boost*100:.2f}%",
                severity='warning',
                timestamp=datetime.now()
            )
        else:
            result = HealthCheckResult(
                check_name="Protocol Comparison Check",
                passed=True,
                message=f"Morpho boost within expected range: +{boost*100:.2f}%",
                severity='info',
                timestamp=datetime.now()
            )

        self.results.append(result)
        return result

    def get_summary(self) -> Dict:
        """
        Get summary of all health checks

        Returns:
            Dictionary with health check summary
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        errors = [r for r in self.results if not r.passed and r.severity == 'error']
        warnings = [r for r in self.results if not r.passed and r.severity == 'warning']

        return {
            'total_checks': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'errors': len(errors),
            'warnings': len(warnings),
            'error_details': [r.message for r in errors],
            'warning_details': [r.message for r in warnings],
            'overall_healthy': len(errors) == 0,
            'timestamp': datetime.now().isoformat()
        }

    def clear_results(self):
        """Clear all health check results"""
        self.results = []


if __name__ == "__main__":
    # Example usage
    checker = HealthChecker()

    print("Running Health Checks...")

    # Check APY sanity
    print("\n1. APY Sanity Checks:")
    result = checker.check_apy_sanity(Decimal('0.05'), Decimal('0.07'), 'USDC')
    print(f"   {result.check_name}: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print(f"   {result.message}")

    result = checker.check_apy_sanity(Decimal('0.08'), Decimal('0.06'), 'DAI')  # Invalid spread
    print(f"   {result.check_name}: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print(f"   {result.message}")

    # Check TVL sanity
    print("\n2. TVL Sanity Checks:")
    result = checker.check_tvl_sanity(Decimal('1000000000'), 'Aave V3')  # $1B
    print(f"   {result.check_name}: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print(f"   {result.message}")

    # Check data freshness
    print("\n3. Data Freshness Check:")
    result = checker.check_data_freshness(datetime.now() - timedelta(minutes=10))
    print(f"   {result.check_name}: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print(f"   {result.message}")

    # Check protocol comparison
    print("\n4. Protocol Comparison Check:")
    result = checker.check_protocol_comparison(Decimal('0.05'), Decimal('0.06'))  # 1% boost
    print(f"   {result.check_name}: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print(f"   {result.message}")

    # Get summary
    print("\n" + "="*50)
    print("HEALTH CHECK SUMMARY")
    print("="*50)
    summary = checker.get_summary()
    print(f"Total Checks: {summary['total_checks']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"Overall Healthy: {'✓ YES' if summary['overall_healthy'] else '✗ NO'}")

    if summary['errors']:
        print(f"\nErrors ({summary['errors']}):")
        for error in summary['error_details']:
            print(f"  - {error}")

    if summary['warnings']:
        print(f"\nWarnings ({summary['warnings']}):")
        for warning in summary['warning_details']:
            print(f"  - {warning}")
