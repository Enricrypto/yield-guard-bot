"""
Historical Risk Parameter Fetcher
Fetches historical LTV and liquidation threshold changes from protocol subgraphs
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
import requests


@dataclass
class RiskParameterSnapshot:
    """Snapshot of risk parameters at a point in time"""
    timestamp: datetime
    ltv: Decimal
    liquidation_threshold: Decimal
    liquidation_bonus: Decimal


class RiskParameterFetcher:
    """
    Fetches historical risk parameter changes for lending protocols
    Uses Aave V3 Subgraph (The Graph) for historical data
    """

    # Aave V3 Subgraph endpoints
    AAVE_SUBGRAPH_URLS = {
        'mainnet': 'https://api.thegraph.com/subgraphs/name/aave/protocol-v3',
        'polygon': 'https://api.thegraph.com/subgraphs/name/aave/protocol-v3-polygon',
        'arbitrum': 'https://api.thegraph.com/subgraphs/name/aave/protocol-v3-arbitrum',
        'optimism': 'https://api.thegraph.com/subgraphs/name/aave/protocol-v3-optimism',
    }

    # Asset addresses (mainnet)
    ASSET_ADDRESSES = {
        'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7',
        'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
        'WETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
    }

    def __init__(self, network: str = 'mainnet'):
        """
        Initialize risk parameter fetcher

        Args:
            network: Network to fetch from (mainnet, polygon, arbitrum, optimism)
        """
        if network not in self.AAVE_SUBGRAPH_URLS:
            raise ValueError(f"Unsupported network: {network}")

        self.network = network
        self.subgraph_url = self.AAVE_SUBGRAPH_URLS[network]

    def _query_subgraph(self, query: str) -> Dict:
        """Execute GraphQL query against Aave subgraph"""
        try:
            response = requests.post(
                self.subgraph_url,
                json={'query': query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying subgraph: {e}")
            return {}

    def fetch_risk_parameter_history(
        self,
        asset_symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[RiskParameterSnapshot]:
        """
        Fetch historical risk parameter changes for an asset

        Args:
            asset_symbol: Asset symbol (e.g., 'USDC')
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of risk parameter snapshots ordered by timestamp
        """
        asset_address = self.ASSET_ADDRESSES.get(asset_symbol.upper())
        if not asset_address:
            print(f"Unknown asset: {asset_symbol}")
            return []

        # Convert dates to Unix timestamps
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        # Query for ReserveConfigurationHistoryItem events
        # These track LTV, liquidation threshold, and liquidation bonus changes
        query = f"""
        {{
          reserveConfigurationHistoryItems(
            where: {{
              reserve: "{asset_address.lower()}"
              timestamp_gte: {start_timestamp}
              timestamp_lte: {end_timestamp}
            }}
            orderBy: timestamp
            orderDirection: asc
            first: 1000
          ) {{
            id
            timestamp
            ltv
            liquidationThreshold
            liquidationBonus
            reserve {{
              symbol
            }}
          }}
        }}
        """

        result = self._query_subgraph(query)

        if 'data' not in result or 'reserveConfigurationHistoryItems' not in result['data']:
            print(f"No configuration history found for {asset_symbol}")
            return self._get_current_parameters(asset_symbol, start_date)

        snapshots = []
        for item in result['data']['reserveConfigurationHistoryItems']:
            try:
                snapshot = RiskParameterSnapshot(
                    timestamp=datetime.fromtimestamp(int(item['timestamp'])),
                    # Aave stores these as basis points (10000 = 100%)
                    ltv=Decimal(str(item['ltv'])) / Decimal('10000'),
                    liquidation_threshold=Decimal(str(item['liquidationThreshold'])) / Decimal('10000'),
                    liquidation_bonus=Decimal(str(item['liquidationBonus'])) / Decimal('10000')
                )
                snapshots.append(snapshot)
            except (KeyError, ValueError) as e:
                print(f"Error parsing snapshot: {e}")
                continue

        # If no historical changes, get current parameters
        if not snapshots:
            snapshots = self._get_current_parameters(asset_symbol, start_date)

        return snapshots

    def _get_current_parameters(
        self,
        asset_symbol: str,
        as_of_date: datetime
    ) -> List[RiskParameterSnapshot]:
        """
        Get current risk parameters for an asset
        Falls back to this if no historical data available
        """
        asset_address = self.ASSET_ADDRESSES.get(asset_symbol.upper())
        if not asset_address:
            return []

        query = f"""
        {{
          reserve(id: "{asset_address.lower()}") {{
            symbol
            baseLTVasCollateral
            reserveLiquidationThreshold
            reserveLiquidationBonus
          }}
        }}
        """

        result = self._query_subgraph(query)

        if 'data' not in result or 'reserve' not in result['data'] or not result['data']['reserve']:
            # Use conservative defaults if query fails
            print(f"Could not fetch parameters for {asset_symbol}, using defaults")
            return [RiskParameterSnapshot(
                timestamp=as_of_date,
                ltv=Decimal('0.80'),  # 80% LTV
                liquidation_threshold=Decimal('0.85'),  # 85% liquidation threshold
                liquidation_bonus=Decimal('0.05')  # 5% bonus
            )]

        reserve = result['data']['reserve']

        return [RiskParameterSnapshot(
            timestamp=as_of_date,
            ltv=Decimal(str(reserve['baseLTVasCollateral'])) / Decimal('10000'),
            liquidation_threshold=Decimal(str(reserve['reserveLiquidationThreshold'])) / Decimal('10000'),
            liquidation_bonus=Decimal(str(reserve['reserveLiquidationBonus'])) / Decimal('10000')
        )]

    def get_parameters_for_date(
        self,
        asset_symbol: str,
        target_date: datetime,
        snapshots: Optional[List[RiskParameterSnapshot]] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Get LTV and liquidation threshold for a specific date

        Args:
            asset_symbol: Asset symbol
            target_date: Date to get parameters for
            snapshots: Pre-fetched snapshots (optional, will fetch if not provided)

        Returns:
            Tuple of (ltv, liquidation_threshold)
        """
        if snapshots is None:
            # Fetch parameters for a range around the target date
            start_date = target_date - timedelta(days=30)
            end_date = target_date + timedelta(days=1)
            snapshots = self.fetch_risk_parameter_history(asset_symbol, start_date, end_date)

        if not snapshots:
            # Return conservative defaults
            return Decimal('0.80'), Decimal('0.85')

        # Find the most recent snapshot before or on target_date
        applicable_snapshot = None
        for snapshot in reversed(snapshots):
            if snapshot.timestamp <= target_date:
                applicable_snapshot = snapshot
                break

        # If no snapshot before target date, use the earliest one
        if applicable_snapshot is None:
            applicable_snapshot = snapshots[0]

        return applicable_snapshot.ltv, applicable_snapshot.liquidation_threshold


def get_risk_parameters_for_simulation(
    protocol: str,
    asset_symbol: str,
    start_date: datetime,
    days: int,
    network: str = 'mainnet'
) -> Dict[int, Tuple[Decimal, Decimal]]:
    """
    Get risk parameters for each day of a simulation

    Args:
        protocol: Protocol name (e.g., 'aave-v3')
        asset_symbol: Asset symbol (e.g., 'USDC')
        start_date: Simulation start date
        days: Number of days to simulate
        network: Network (mainnet, polygon, etc.)

    Returns:
        Dictionary mapping day index to (ltv, liquidation_threshold)
    """
    # Only fetch for Aave (others will use defaults)
    if 'aave' not in protocol.lower():
        # Return static parameters for non-Aave protocols
        default_ltv = Decimal('0.80')
        default_liq_threshold = Decimal('0.85')
        return {day: (default_ltv, default_liq_threshold) for day in range(days)}

    fetcher = RiskParameterFetcher(network=network)

    # Fetch historical parameter changes
    end_date = start_date + timedelta(days=days)
    snapshots = fetcher.fetch_risk_parameter_history(asset_symbol, start_date, end_date)

    # Map each simulation day to its parameters
    parameters_by_day = {}
    for day in range(days):
        day_date = start_date + timedelta(days=day)
        ltv, liq_threshold = fetcher.get_parameters_for_date(asset_symbol, day_date, snapshots)
        parameters_by_day[day] = (ltv, liq_threshold)

    return parameters_by_day
