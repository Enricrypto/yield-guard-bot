"""
Aave Protocol Metrics Fetcher
Queries Aave V3 data via Morpho's public GraphQL API
Morpho's API provides access to underlying Aave market data (free, no API key required)

Rate Limits: 5,000 requests per 5 minutes
"""

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class AaveReserveData:
    """Data structure for Aave reserve information"""
    asset_address: str
    asset_symbol: str
    asset_name: str

    # Rates (in decimal form, e.g., 0.05 = 5%)
    liquidity_rate: Decimal  # Supply APY
    variable_borrow_rate: Decimal
    stable_borrow_rate: Decimal

    # Risk Parameters
    ltv: Decimal  # Loan-to-Value ratio
    liquidation_threshold: Decimal
    liquidation_bonus: Decimal

    # Liquidity
    total_liquidity: Decimal
    available_liquidity: Decimal
    total_borrowed: Decimal
    utilization_rate: Decimal

    # Additional info
    reserve_factor: Decimal
    is_active: bool
    is_frozen: bool

    def __repr__(self):
        return (f"<AaveReserve {self.asset_symbol}: "
                f"Supply={self.liquidity_rate*100:.2f}%, "
                f"LTV={self.ltv*100:.0f}%, "
                f"LiqThreshold={self.liquidation_threshold*100:.0f}%>")


class AaveFetcher:
    """
    Fetches real-time metrics from Aave V3 Protocol
    Uses Morpho's public GraphQL API (free, no API key required)
    """

    # Morpho's public GraphQL API - includes Aave underlying data
    API_URL = 'https://api.morpho.org/graphql'

    # Network IDs for Morpho API
    CHAIN_IDS = {
        'mainnet': 1,
        'polygon': 137,
        'arbitrum': 42161,
        'optimism': 10,
        'base': 8453,
    }

    # Common stablecoin and asset addresses (mainnet)
    COMMON_ASSETS = {
        'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7',
        'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
        'WETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
        'WBTC': '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
    }

    def __init__(self, network: str = 'mainnet'):
        """
        Initialize Aave fetcher

        Args:
            network: Network to fetch from (mainnet, polygon, arbitrum, optimism, base)
        """
        if network not in self.CHAIN_IDS:
            raise ValueError(f"Unsupported network: {network}. Choose from {list(self.CHAIN_IDS.keys())}")

        self.network = network
        self.chain_id = self.CHAIN_IDS[network]

    def _query_graphql(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute GraphQL query against Morpho API

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query result data
        """
        try:
            payload = {'query': query}
            if variables:
                payload['variables'] = variables

            response = requests.post(
                self.API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            response.raise_for_status()

            result = response.json()
            if 'errors' in result:
                raise Exception(f"GraphQL errors: {result['errors']}")

            return result.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to query Morpho API: {str(e)}")

    def get_reserve_data(self, asset_address: Optional[str] = None) -> List[AaveReserveData]:
        """
        Fetch reserve data for a specific asset or all assets

        Args:
            asset_address: Optional specific asset address (lowercase)

        Returns:
            List of AaveReserveData objects
        """
        # GraphQL query to get market data including underlying Aave rates
        query = """
        query GetMarkets($chainIds: [Int!]!, $first: Int!) {
          markets(
            where: { chainId_in: $chainIds }
            first: $first
          ) {
            items {
              uniqueKey
              loanAsset {
                address
                symbol
                name
                decimals
              }
              state {
                supplyApy
                borrowApy
                supplyAssetsUsd
                borrowAssetsUsd
                liquidityAssetsUsd
                utilization
                rewards {
                  supplyApr
                  borrowApr
                }
              }
              lltv
              collateralAsset {
                address
                symbol
              }
            }
          }
        }
        """

        variables = {
            'chainIds': [self.chain_id],
            'first': 100
        }

        data = self._query_graphql(query, variables)
        markets = data.get('markets', {}).get('items', [])

        # Group by loan asset and aggregate data
        assets_map = {}
        for market in markets:
            loan_asset = market.get('loanAsset', {})
            asset_addr = loan_asset.get('address', '').lower()

            if asset_address and asset_addr != asset_address.lower():
                continue

            symbol = loan_asset.get('symbol', '')

            if symbol not in assets_map:
                assets_map[symbol] = {
                    'address': asset_addr,
                    'symbol': symbol,
                    'name': loan_asset.get('name', ''),
                    'decimals': loan_asset.get('decimals', 18),
                    'markets': []
                }

            assets_map[symbol]['markets'].append(market)

        # Convert to AaveReserveData objects
        reserves = []
        for asset_data in assets_map.values():
            reserves.append(self._aggregate_asset_data(asset_data))

        return reserves

    def _aggregate_asset_data(self, asset_data: Dict) -> AaveReserveData:
        """Aggregate market data for an asset into AaveReserveData"""

        markets = asset_data['markets']

        # Calculate weighted averages based on liquidity
        # Handle None values by converting to 0
        total_supply_usd = sum(
            Decimal(str(m.get('state', {}).get('supplyAssetsUsd') or 0))
            for m in markets
        )

        if total_supply_usd == 0:
            # Use first market if no supply data
            market = markets[0] if markets else {}
            state = market.get('state', {})
            supply_apy = Decimal(str(state.get('supplyApy') or 0))
            borrow_apy = Decimal(str(state.get('borrowApy') or 0))
            utilization = Decimal(str(state.get('utilization') or 0))
            lltv = Decimal(str(market.get('lltv') or 0))
        else:
            # Weighted average
            supply_apy = sum(
                Decimal(str(m.get('state', {}).get('supplyApy') or 0)) *
                Decimal(str(m.get('state', {}).get('supplyAssetsUsd') or 0))
                for m in markets
            ) / total_supply_usd

            total_borrow_usd = sum(Decimal(str(m.get('state', {}).get('borrowAssetsUsd') or 0)) for m in markets)
            if total_borrow_usd > 0:
                borrow_apy = sum(
                    Decimal(str(m.get('state', {}).get('borrowApy') or 0)) *
                    Decimal(str(m.get('state', {}).get('borrowAssetsUsd') or 0))
                    for m in markets
                ) / total_borrow_usd
            else:
                borrow_apy = Decimal('0')

            utilization = sum(Decimal(str(m.get('state', {}).get('utilization') or 0)) for m in markets) / len(markets)
            lltv = sum(Decimal(str(m.get('lltv') or 0)) for m in markets) / len(markets)

        total_supply = sum(Decimal(str(m.get('state', {}).get('supplyAssetsUsd') or 0)) for m in markets)
        total_borrow = sum(Decimal(str(m.get('state', {}).get('borrowAssetsUsd') or 0)) for m in markets)
        total_liquidity = sum(Decimal(str(m.get('state', {}).get('liquidityAssetsUsd') or 0)) for m in markets)

        # Convert LLTV to LTV and liquidation threshold
        # LLTV (Liquidation LTV) is typically slightly below liquidation threshold
        ltv = lltv * Decimal('0.9')  # Approximate LTV as 90% of LLTV
        liquidation_threshold = lltv

        return AaveReserveData(
            asset_address=asset_data['address'],
            asset_symbol=asset_data['symbol'],
            asset_name=asset_data['name'],
            liquidity_rate=supply_apy,
            variable_borrow_rate=borrow_apy,
            stable_borrow_rate=borrow_apy * Decimal('1.1'),  # Estimate stable rate as 10% higher
            ltv=ltv,
            liquidation_threshold=liquidation_threshold,
            liquidation_bonus=Decimal('0.05'),  # Standard 5% liquidation bonus
            total_liquidity=total_liquidity,
            available_liquidity=total_liquidity,
            total_borrowed=total_borrow,
            utilization_rate=utilization,
            reserve_factor=Decimal('0.1'),  # Standard 10%
            is_active=True,
            is_frozen=False,
        )

    def get_reserve_by_symbol(self, symbol: str) -> Optional[AaveReserveData]:
        """
        Get reserve data for a specific asset by symbol

        Args:
            symbol: Asset symbol (e.g., 'USDC', 'WETH')

        Returns:
            AaveReserveData or None if not found
        """
        all_reserves = self.get_reserve_data()

        for reserve in all_reserves:
            if reserve.asset_symbol.upper() == symbol.upper():
                return reserve

        return None

    def get_multiple_reserves(self, symbols: List[str]) -> Dict[str, AaveReserveData]:
        """
        Get reserve data for multiple assets

        Args:
            symbols: List of asset symbols

        Returns:
            Dictionary mapping symbol to AaveReserveData
        """
        result = {}
        all_reserves = self.get_reserve_data()

        # Create a lookup dictionary
        reserves_by_symbol = {r.asset_symbol.upper(): r for r in all_reserves}

        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper in reserves_by_symbol:
                result[symbol] = reserves_by_symbol[symbol_upper]

        return result

    def get_best_supply_rate(self, min_liquidity: Decimal = Decimal('1000000')) -> AaveReserveData:
        """
        Find the reserve with the best supply rate

        Args:
            min_liquidity: Minimum liquidity required (in USD equivalent)

        Returns:
            AaveReserveData with highest supply rate
        """
        reserves = self.get_reserve_data()

        # Filter by liquidity and active status
        eligible = [r for r in reserves if r.is_active and not r.is_frozen
                   and r.total_liquidity >= min_liquidity]

        if not eligible:
            raise Exception("No eligible reserves found")

        return max(eligible, key=lambda r: r.liquidity_rate)

    def get_asset_health_metrics(self, symbol: str) -> Dict:
        """
        Get comprehensive health metrics for an asset

        Args:
            symbol: Asset symbol

        Returns:
            Dictionary with health metrics
        """
        reserve = self.get_reserve_by_symbol(symbol)
        if not reserve:
            raise ValueError(f"Reserve not found for {symbol}")

        return {
            'symbol': reserve.asset_symbol,
            'supply_apy': float(reserve.liquidity_rate * 100),
            'borrow_apy': float(reserve.variable_borrow_rate * 100),
            'utilization': float(reserve.utilization_rate * 100),
            'ltv': float(reserve.ltv * 100),
            'liquidation_threshold': float(reserve.liquidation_threshold * 100),
            'liquidation_penalty': float(reserve.liquidation_bonus * 100),
            'total_liquidity': float(reserve.total_liquidity),
            'available_liquidity': float(reserve.available_liquidity),
            'is_safe': reserve.is_active and not reserve.is_frozen and reserve.utilization_rate < Decimal('0.9'),
        }


if __name__ == "__main__":
    # Example usage
    fetcher = AaveFetcher(network='mainnet')

    print("Fetching USDC reserve data from Aave V3...")
    usdc = fetcher.get_reserve_by_symbol('USDC')

    if usdc:
        print(f"\n{usdc}")
        print(f"Supply APY: {usdc.liquidity_rate * 100:.2f}%")
        print(f"Borrow APY: {usdc.variable_borrow_rate * 100:.2f}%")
        print(f"Utilization: {usdc.utilization_rate * 100:.2f}%")
        print(f"Total Liquidity: ${usdc.total_liquidity:,.2f}")

        health = fetcher.get_asset_health_metrics('USDC')
        print(f"\nHealth Metrics: {health}")
