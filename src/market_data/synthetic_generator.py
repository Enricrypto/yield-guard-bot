"""
Synthetic Market Data Generator
Generates realistic market data for simulations including:
- APY movements with volatility
- TVL changes
- Risk scores
- Market conditions (bull/bear/neutral)
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from decimal import Decimal
import pandas as pd


@dataclass
class MarketSnapshot:
    """Single snapshot of market data at a point in time"""
    timestamp: datetime

    # APY data
    aave_supply_apy: Decimal
    aave_borrow_apy: Decimal
    morpho_supply_apy: Decimal
    morpho_borrow_apy: Decimal

    # TVL data
    aave_tvl: Decimal
    morpho_tvl: Decimal

    # Risk metrics
    risk_score: float  # 0-100, where 0 is safest
    volatility: float  # Annualized volatility

    # Market conditions
    market_condition: Literal['bull', 'bear', 'neutral', 'volatile']

    # Asset-specific (can be expanded)
    asset_symbol: str = 'USDC'


class SyntheticDataGenerator:
    """
    Generates synthetic but realistic market data for simulations
    Uses random walk with mean reversion for APY movements
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize synthetic data generator

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

        # Base parameters (realistic ranges)
        self.base_aave_supply = Decimal('0.05')  # 5% base APY
        self.base_aave_borrow = Decimal('0.07')  # 7% base APY
        self.base_morpho_boost = Decimal('0.01')  # 1% boost over Aave

        self.base_aave_tvl = Decimal('1000000000')  # $1B base TVL
        self.base_morpho_tvl = Decimal('200000000')  # $200M base TVL

        # Volatility parameters
        self.apy_volatility = 0.15  # 15% annual volatility for APY
        self.tvl_volatility = 0.10  # 10% annual volatility for TVL

        # Mean reversion parameters
        self.mean_reversion_strength = 0.1  # How quickly APY reverts to mean

    def generate_timeseries(
        self,
        days: int = 180,
        start_date: Optional[datetime] = None,
        asset_symbol: str = 'USDC',
        market_regime: Literal['normal', 'bull', 'bear', 'volatile'] = 'normal'
    ) -> List[MarketSnapshot]:
        """
        Generate a time series of market data

        Args:
            days: Number of days to generate
            start_date: Starting date (default: today - days)
            asset_symbol: Asset to generate data for
            market_regime: Overall market conditions

        Returns:
            List of MarketSnapshot objects
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)

        snapshots = []

        # Initial values
        current_aave_supply = float(self.base_aave_supply)
        current_aave_borrow = float(self.base_aave_borrow)
        current_morpho_supply = current_aave_supply + float(self.base_morpho_boost)
        current_morpho_borrow = current_aave_borrow + float(self.base_morpho_boost)

        current_aave_tvl = float(self.base_aave_tvl)
        current_morpho_tvl = float(self.base_morpho_tvl)

        # Apply market regime adjustments
        regime_params = self._get_regime_parameters(market_regime)

        for day in range(days):
            timestamp = start_date + timedelta(days=day)

            # Update APY with mean reversion random walk
            current_aave_supply = self._random_walk_mean_reversion(
                current_aave_supply,
                float(self.base_aave_supply) * regime_params['apy_multiplier'],
                self.apy_volatility * regime_params['volatility_multiplier'],
                self.mean_reversion_strength
            )

            current_aave_borrow = self._random_walk_mean_reversion(
                current_aave_borrow,
                float(self.base_aave_borrow) * regime_params['apy_multiplier'],
                self.apy_volatility * regime_params['volatility_multiplier'],
                self.mean_reversion_strength
            )

            # Morpho APY maintains boost over Aave
            boost = float(self.base_morpho_boost) * (1 + random.uniform(-0.2, 0.2))
            current_morpho_supply = current_aave_supply + boost
            current_morpho_borrow = current_aave_borrow + boost

            # Update TVL with trend
            current_aave_tvl = self._random_walk_with_trend(
                current_aave_tvl,
                float(self.base_aave_tvl),
                self.tvl_volatility,
                regime_params['tvl_trend']
            )

            current_morpho_tvl = self._random_walk_with_trend(
                current_morpho_tvl,
                float(self.base_morpho_tvl),
                self.tvl_volatility * 1.5,  # More volatile
                regime_params['tvl_trend'] * 1.2  # Stronger trend
            )

            # Calculate risk score
            risk_score = self._calculate_risk_score(
                current_aave_supply,
                current_aave_borrow,
                regime_params['base_risk']
            )

            # Determine daily market condition
            market_condition = self._determine_market_condition(
                risk_score,
                regime_params['volatility_multiplier']
            )

            # Create snapshot
            snapshot = MarketSnapshot(
                timestamp=timestamp,
                aave_supply_apy=Decimal(str(max(0.001, current_aave_supply))),
                aave_borrow_apy=Decimal(str(max(0.002, current_aave_borrow))),
                morpho_supply_apy=Decimal(str(max(0.001, current_morpho_supply))),
                morpho_borrow_apy=Decimal(str(max(0.002, current_morpho_borrow))),
                aave_tvl=Decimal(str(max(100000000, current_aave_tvl))),
                morpho_tvl=Decimal(str(max(10000000, current_morpho_tvl))),
                risk_score=risk_score,
                volatility=self.apy_volatility * regime_params['volatility_multiplier'],
                market_condition=market_condition,
                asset_symbol=asset_symbol
            )

            snapshots.append(snapshot)

        return snapshots

    def _get_regime_parameters(self, regime: str) -> Dict:
        """Get parameters for different market regimes"""
        regimes = {
            'normal': {
                'apy_multiplier': 1.0,
                'volatility_multiplier': 1.0,
                'tvl_trend': 0.0002,  # Slight upward trend
                'base_risk': 30.0
            },
            'bull': {
                'apy_multiplier': 1.3,  # Higher APYs
                'volatility_multiplier': 0.8,  # Lower volatility
                'tvl_trend': 0.001,  # Strong upward trend
                'base_risk': 20.0  # Lower risk
            },
            'bear': {
                'apy_multiplier': 0.7,  # Lower APYs
                'volatility_multiplier': 1.5,  # Higher volatility
                'tvl_trend': -0.0005,  # Downward trend
                'base_risk': 50.0  # Higher risk
            },
            'volatile': {
                'apy_multiplier': 1.0,
                'volatility_multiplier': 2.0,  # Very high volatility
                'tvl_trend': 0.0,  # No trend
                'base_risk': 45.0  # Higher risk
            }
        }
        return regimes.get(regime, regimes['normal'])

    def _random_walk_mean_reversion(
        self,
        current_value: float,
        mean_value: float,
        volatility: float,
        reversion_strength: float
    ) -> float:
        """
        Random walk with mean reversion (Ornstein-Uhlenbeck process)

        Args:
            current_value: Current value
            mean_value: Long-term mean to revert to
            volatility: Daily volatility
            reversion_strength: How quickly to revert (0-1)

        Returns:
            New value after one step
        """
        # Mean reversion component
        reversion = reversion_strength * (mean_value - current_value)

        # Random component (Brownian motion)
        random_change = volatility * random.gauss(0, 1) / math.sqrt(252)  # Daily volatility

        # New value
        new_value = current_value + reversion + current_value * random_change

        return new_value

    def _random_walk_with_trend(
        self,
        current_value: float,
        base_value: float,
        volatility: float,
        trend: float
    ) -> float:
        """
        Random walk with trend component

        Args:
            current_value: Current value
            base_value: Base value (for bounds)
            volatility: Daily volatility
            trend: Trend component (daily)

        Returns:
            New value after one step
        """
        # Trend component
        trend_change = current_value * trend

        # Random component
        random_change = current_value * volatility * random.gauss(0, 1) / math.sqrt(252)

        # New value with bounds
        new_value = current_value + trend_change + random_change

        # Keep within reasonable bounds (50% to 200% of base)
        new_value = max(base_value * 0.5, min(base_value * 2.0, new_value))

        return new_value

    def _calculate_risk_score(
        self,
        supply_apy: float,
        borrow_apy: float,
        base_risk: float
    ) -> float:
        """
        Calculate risk score based on market conditions

        Args:
            supply_apy: Current supply APY
            borrow_apy: Current borrow APY
            base_risk: Base risk score

        Returns:
            Risk score (0-100)
        """
        # Higher spread = lower risk
        spread = borrow_apy - supply_apy
        spread_risk = max(0, 20 - spread * 500)  # Penalize low spreads

        # Very high APYs = higher risk
        high_apy_risk = max(0, (supply_apy - 0.15) * 100) if supply_apy > 0.15 else 0

        # Combine components
        total_risk = base_risk + spread_risk + high_apy_risk

        # Add random noise
        total_risk += random.uniform(-5, 5)

        # Clamp to 0-100
        return max(0, min(100, total_risk))

    def _determine_market_condition(
        self,
        risk_score: float,
        volatility_multiplier: float
    ) -> Literal['bull', 'bear', 'neutral', 'volatile']:
        """Determine market condition based on risk and volatility"""
        if volatility_multiplier > 1.5:
            return 'volatile'
        elif risk_score < 25:
            return 'bull'
        elif risk_score > 60:
            return 'bear'
        else:
            return 'neutral'

    def to_dataframe(self, snapshots: List[MarketSnapshot]) -> pd.DataFrame:
        """Convert snapshots to pandas DataFrame for analysis"""
        data = []
        for snapshot in snapshots:
            data.append({
                'timestamp': snapshot.timestamp,
                'asset_symbol': snapshot.asset_symbol,
                'aave_supply_apy': float(snapshot.aave_supply_apy),
                'aave_borrow_apy': float(snapshot.aave_borrow_apy),
                'morpho_supply_apy': float(snapshot.morpho_supply_apy),
                'morpho_borrow_apy': float(snapshot.morpho_borrow_apy),
                'aave_tvl': float(snapshot.aave_tvl),
                'morpho_tvl': float(snapshot.morpho_tvl),
                'risk_score': snapshot.risk_score,
                'volatility': snapshot.volatility,
                'market_condition': snapshot.market_condition
            })

        return pd.DataFrame(data)

    def generate_multiple_assets(
        self,
        days: int = 180,
        assets: List[str] = None,
        market_regime: str = 'normal'
    ) -> Dict[str, List[MarketSnapshot]]:
        """
        Generate data for multiple assets

        Args:
            days: Number of days
            assets: List of asset symbols
            market_regime: Market regime

        Returns:
            Dictionary mapping asset symbol to snapshots
        """
        if assets is None:
            assets = ['USDC', 'DAI', 'WETH', 'WBTC']

        result = {}

        for asset in assets:
            # Vary parameters slightly per asset
            self.base_aave_supply *= Decimal(str(random.uniform(0.9, 1.1)))
            self.base_aave_borrow *= Decimal(str(random.uniform(0.9, 1.1)))

            result[asset] = self.generate_timeseries(
                days=days,
                asset_symbol=asset,
                market_regime=market_regime
            )

        return result


if __name__ == "__main__":
    # Example usage
    generator = SyntheticDataGenerator(seed=42)

    print("Generating 180 days of market data...")
    snapshots = generator.generate_timeseries(days=180, market_regime='normal')

    print(f"\nGenerated {len(snapshots)} snapshots")
    print(f"\nFirst snapshot:")
    print(f"  Date: {snapshots[0].timestamp.strftime('%Y-%m-%d')}")
    print(f"  Aave Supply APY: {snapshots[0].aave_supply_apy * 100:.2f}%")
    print(f"  Morpho Supply APY: {snapshots[0].morpho_supply_apy * 100:.2f}%")
    print(f"  Risk Score: {snapshots[0].risk_score:.1f}")

    print(f"\nLast snapshot:")
    print(f"  Date: {snapshots[-1].timestamp.strftime('%Y-%m-%d')}")
    print(f"  Aave Supply APY: {snapshots[-1].aave_supply_apy * 100:.2f}%")
    print(f"  Morpho Supply APY: {snapshots[-1].morpho_supply_apy * 100:.2f}%")
    print(f"  Risk Score: {snapshots[-1].risk_score:.1f}")

    # Convert to DataFrame
    df = generator.to_dataframe(snapshots)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"\nSample statistics:")
    print(df[['aave_supply_apy', 'morpho_supply_apy', 'risk_score']].describe())
