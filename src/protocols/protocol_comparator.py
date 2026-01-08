"""
Protocol Comparator
Compares Aave and Morpho protocols to determine which offers better terms
for lending, borrowing, and overall yield strategies.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from decimal import Decimal
from .aave_fetcher import AaveFetcher, AaveReserveData
from .morpho_fetcher import MorphoFetcher, MorphoMarketData


@dataclass
class ProtocolComparison:
    """Comparison results between Aave and Morpho for an asset"""
    asset_symbol: str

    # Supply rates
    aave_supply_apy: Decimal
    morpho_supply_apy: Decimal
    supply_advantage: Decimal  # Positive means Morpho is better
    better_supply_protocol: str

    # Borrow rates (if applicable)
    aave_borrow_apy: Optional[Decimal]
    morpho_borrow_apy: Optional[Decimal]
    borrow_advantage: Optional[Decimal]  # Positive means Morpho is better (lower rate)
    better_borrow_protocol: Optional[str]

    # Risk metrics
    aave_ltv: Decimal
    morpho_ltv: Decimal
    aave_liquidation_threshold: Decimal
    morpho_liquidation_threshold: Decimal

    # Liquidity
    aave_liquidity: Decimal
    morpho_liquidity: Decimal

    # Overall recommendation
    recommended_protocol: str
    recommendation_reason: str

    def __repr__(self):
        return (f"<Comparison {self.asset_symbol}: "
                f"Best={self.recommended_protocol} "
                f"(+{self.supply_advantage*100:.2f}% APY)>")


class ProtocolComparator:
    """
    Compares Aave and Morpho protocols to find optimal yield opportunities
    """

    def __init__(self, network: str = 'mainnet'):
        """
        Initialize protocol comparator

        Args:
            network: Network to compare on (mainnet, polygon)
        """
        self.network = network
        self.aave = AaveFetcher(network=network)
        self.morpho = MorphoFetcher(network=network)

    def compare_asset(
        self,
        symbol: str,
        use_case: Literal['supply', 'borrow', 'balanced'] = 'supply'
    ) -> ProtocolComparison:
        """
        Compare Aave vs Morpho for a specific asset

        Args:
            symbol: Asset symbol to compare
            use_case: What to optimize for:
                - 'supply': Best lending/supply rate
                - 'borrow': Best borrowing rate
                - 'balanced': Consider both supply and borrow

        Returns:
            ProtocolComparison object
        """
        # Fetch data from both protocols
        aave_data = self.aave.get_reserve_by_symbol(symbol)
        morpho_data = self.morpho.get_market_by_symbol(symbol)

        if not aave_data:
            raise ValueError(f"Asset {symbol} not found on Aave")
        if not morpho_data:
            raise ValueError(f"Asset {symbol} not found on Morpho")

        # Calculate advantages
        supply_advantage = morpho_data.supply_apy - aave_data.liquidity_rate
        borrow_advantage = aave_data.variable_borrow_rate - morpho_data.borrow_apy

        # Determine better protocols
        better_supply = "Morpho" if supply_advantage > 0 else "Aave"
        better_borrow = "Morpho" if borrow_advantage > 0 else "Aave"

        # Make recommendation based on use case
        recommended, reason = self._make_recommendation(
            use_case=use_case,
            supply_advantage=supply_advantage,
            borrow_advantage=borrow_advantage,
            aave_data=aave_data,
            morpho_data=morpho_data
        )

        return ProtocolComparison(
            asset_symbol=symbol,
            aave_supply_apy=aave_data.liquidity_rate,
            morpho_supply_apy=morpho_data.supply_apy,
            supply_advantage=supply_advantage,
            better_supply_protocol=better_supply,
            aave_borrow_apy=aave_data.variable_borrow_rate,
            morpho_borrow_apy=morpho_data.borrow_apy,
            borrow_advantage=borrow_advantage,
            better_borrow_protocol=better_borrow,
            aave_ltv=aave_data.ltv,
            morpho_ltv=morpho_data.ltv,
            aave_liquidation_threshold=aave_data.liquidation_threshold,
            morpho_liquidation_threshold=morpho_data.liquidation_threshold,
            aave_liquidity=aave_data.total_liquidity,
            morpho_liquidity=morpho_data.total_supply,
            recommended_protocol=recommended,
            recommendation_reason=reason,
        )

    def _make_recommendation(
        self,
        use_case: str,
        supply_advantage: Decimal,
        borrow_advantage: Decimal,
        aave_data: AaveReserveData,
        morpho_data: MorphoMarketData
    ) -> tuple[str, str]:
        """
        Make protocol recommendation based on use case and metrics

        Returns:
            Tuple of (protocol_name, reason)
        """
        # Supply use case: optimize for best lending rate
        if use_case == 'supply':
            if supply_advantage > Decimal('0.001'):  # > 0.1% better
                return "Morpho", f"Higher supply APY (+{supply_advantage*100:.2f}%)"
            elif supply_advantage < Decimal('-0.001'):
                return "Aave", f"Higher supply APY (Morpho is {abs(supply_advantage)*100:.2f}% lower)"
            else:
                # Rates similar, check liquidity
                if aave_data.total_liquidity > morpho_data.total_supply:
                    return "Aave", "Similar rates, but better liquidity"
                else:
                    return "Morpho", "Similar rates, optimized matching"

        # Borrow use case: optimize for best borrowing rate
        elif use_case == 'borrow':
            if borrow_advantage > Decimal('0.001'):  # Morpho has lower rate
                return "Morpho", f"Lower borrow APY (-{borrow_advantage*100:.2f}%)"
            elif borrow_advantage < Decimal('-0.001'):
                return "Aave", f"Lower borrow APY (Morpho is {abs(borrow_advantage)*100:.2f}% higher)"
            else:
                return "Aave", "Similar rates, more established for borrowing"

        # Balanced: consider both supply and borrow
        else:
            # Calculate weighted score (supply is typically more important)
            morpho_score = (supply_advantage * Decimal('0.7')) + (borrow_advantage * Decimal('0.3'))

            if morpho_score > Decimal('0.001'):
                return "Morpho", f"Better overall rates (score: +{morpho_score*100:.2f}%)"
            elif morpho_score < Decimal('-0.001'):
                return "Aave", f"Better overall rates"
            else:
                return "Morpho", "Similar rates, P2P optimization"

    def compare_multiple_assets(
        self,
        symbols: List[str],
        use_case: Literal['supply', 'borrow', 'balanced'] = 'supply'
    ) -> Dict[str, ProtocolComparison]:
        """
        Compare multiple assets at once

        Args:
            symbols: List of asset symbols
            use_case: What to optimize for

        Returns:
            Dictionary mapping symbol to ProtocolComparison
        """
        results = {}

        for symbol in symbols:
            try:
                comparison = self.compare_asset(symbol, use_case)
                results[symbol] = comparison
            except ValueError as e:
                print(f"Warning: Could not compare {symbol}: {e}")

        return results

    def find_best_yield_opportunity(
        self,
        min_liquidity: Decimal = Decimal('1000000')
    ) -> Dict:
        """
        Find the best yield opportunity across both protocols

        Args:
            min_liquidity: Minimum liquidity requirement

        Returns:
            Dictionary with best opportunity details
        """
        # Get best from each protocol
        aave_best = self.aave.get_best_supply_rate(min_liquidity)
        morpho_best = self.morpho.get_best_supply_rate(min_liquidity)

        # Compare
        if morpho_best.supply_apy > aave_best.liquidity_rate:
            return {
                'protocol': 'Morpho',
                'asset': morpho_best.asset_symbol,
                'apy': float(morpho_best.supply_apy * 100),
                'advantage_over_aave': float((morpho_best.supply_apy - morpho_best.pool_supply_apy) * 100),
                'liquidity': float(morpho_best.total_supply),
                'p2p_matching_ratio': float((morpho_best.p2p_supply_amount / morpho_best.total_supply) * 100) if morpho_best.total_supply > 0 else 0,
            }
        else:
            return {
                'protocol': 'Aave',
                'asset': aave_best.asset_symbol,
                'apy': float(aave_best.liquidity_rate * 100),
                'liquidity': float(aave_best.total_liquidity),
                'utilization': float(aave_best.utilization_rate * 100),
            }

    def get_portfolio_recommendations(
        self,
        portfolio: Dict[str, Decimal],
        use_case: Literal['supply', 'borrow', 'balanced'] = 'supply'
    ) -> Dict:
        """
        Get protocol recommendations for an entire portfolio

        Args:
            portfolio: Dictionary mapping asset symbol to amount
            use_case: What to optimize for

        Returns:
            Dictionary with recommendations and potential gains
        """
        recommendations = {}
        total_apy_gain = Decimal(0)
        total_value = sum(portfolio.values())

        for symbol, amount in portfolio.items():
            try:
                comparison = self.compare_asset(symbol, use_case)

                # Calculate weighted APY gain
                weight = amount / total_value if total_value > 0 else Decimal(0)
                apy_gain = comparison.supply_advantage * weight

                recommendations[symbol] = {
                    'current_amount': float(amount),
                    'recommended_protocol': comparison.recommended_protocol,
                    'reason': comparison.recommendation_reason,
                    'apy_gain': float(comparison.supply_advantage * 100),
                    'weighted_contribution': float(apy_gain * 100),
                }

                total_apy_gain += apy_gain

            except ValueError as e:
                print(f"Warning: Could not analyze {symbol}: {e}")

        return {
            'asset_recommendations': recommendations,
            'total_portfolio_value': float(total_value),
            'total_apy_improvement': float(total_apy_gain * 100),
            'estimated_annual_gain': float(total_value * total_apy_gain),
        }

    def generate_comparison_report(self, symbol: str) -> str:
        """
        Generate a human-readable comparison report

        Args:
            symbol: Asset symbol to compare

        Returns:
            Formatted comparison report string
        """
        comparison = self.compare_asset(symbol, use_case='balanced')

        report = f"""
Protocol Comparison Report: {symbol}
{'=' * 50}

SUPPLY (LENDING) RATES:
  Aave:   {comparison.aave_supply_apy * 100:>6.2f}%
  Morpho: {comparison.morpho_supply_apy * 100:>6.2f}%
  Winner: {comparison.better_supply_protocol} (+{abs(comparison.supply_advantage) * 100:.2f}%)

BORROW RATES:
  Aave:   {comparison.aave_borrow_apy * 100:>6.2f}%
  Morpho: {comparison.morpho_borrow_apy * 100:>6.2f}%
  Winner: {comparison.better_borrow_protocol} (-{abs(comparison.borrow_advantage) * 100:.2f}%)

RISK PARAMETERS:
  LTV:                 Aave: {comparison.aave_ltv * 100:.0f}%, Morpho: {comparison.morpho_ltv * 100:.0f}%
  Liq. Threshold:      Aave: {comparison.aave_liquidation_threshold * 100:.0f}%, Morpho: {comparison.morpho_liquidation_threshold * 100:.0f}%

LIQUIDITY:
  Aave:   ${comparison.aave_liquidity:>12,.2f}
  Morpho: ${comparison.morpho_liquidity:>12,.2f}

RECOMMENDATION:
  Protocol: {comparison.recommended_protocol}
  Reason:   {comparison.recommendation_reason}
{'=' * 50}
"""
        return report


if __name__ == "__main__":
    # Example usage
    comparator = ProtocolComparator(network='mainnet')

    print("Comparing USDC on Aave vs Morpho...")
    comparison = comparator.compare_asset('USDC', use_case='supply')

    print(comparison)
    print(f"\nRecommendation: Use {comparison.recommended_protocol}")
    print(f"Reason: {comparison.recommendation_reason}")

    # Generate full report
    report = comparator.generate_comparison_report('USDC')
    print(report)

    # Find best opportunity
    print("\nFinding best yield opportunity...")
    best = comparator.find_best_yield_opportunity()
    print(f"Best opportunity: {best}")
