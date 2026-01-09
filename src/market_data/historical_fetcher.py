"""
Historical Data Fetcher
Fetches real historical DeFi yield data from DefiLlama and other sources
For backtesting strategies against actual market conditions
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from decimal import Decimal
import time


@dataclass
class HistoricalYield:
    """Historical yield data point"""
    timestamp: datetime
    protocol: str
    chain: str
    pool_id: str
    asset_symbol: str
    apy: Decimal
    tvl_usd: Decimal

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'protocol': self.protocol,
            'chain': self.chain,
            'pool_id': self.pool_id,
            'asset_symbol': self.asset_symbol,
            'apy': float(self.apy),
            'tvl_usd': float(self.tvl_usd)
        }


class HistoricalDataFetcher:
    """
    Fetches historical DeFi yield data for backtesting

    Uses DefiLlama's free APIs to get:
    - Historical APY data
    - Historical TVL data
    - Multiple protocols and chains
    """

    YIELDS_API = "https://yields.llama.fi"

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize historical data fetcher

        Args:
            cache_ttl: Cache time-to-live in seconds (default 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, List[HistoricalYield]] = {}
        self._cache_timestamps: Dict[str, float] = {}

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache_timestamps:
            return False

        age = time.time() - self._cache_timestamps[key]
        return age < self.cache_ttl

    def _get_cached(self, key: str) -> Optional[List[HistoricalYield]]:
        """Get cached data if valid"""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None

    def _set_cache(self, key: str, value: List[HistoricalYield]):
        """Set cached data"""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def get_pool_historical_apy(
        self,
        pool_id: str,
        use_cache: bool = True
    ) -> Optional[List[HistoricalYield]]:
        """
        Get historical APY data for a specific pool

        Args:
            pool_id: Pool UUID from DefiLlama
            use_cache: Whether to use cached data

        Returns:
            List of historical yield data points
        """
        cache_key = f"pool_history_{pool_id}"

        # Check cache
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return cached

        try:
            url = f"{self.YIELDS_API}/chart/{pool_id}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()

            if not data or 'data' not in data:
                return None

            # Parse historical data
            historical_data = []

            for point in data['data']:
                try:
                    historical_data.append(HistoricalYield(
                        timestamp=datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00')),
                        protocol=data.get('project', 'unknown'),
                        chain=data.get('chain', 'unknown'),
                        pool_id=pool_id,
                        asset_symbol=data.get('symbol', 'unknown'),
                        apy=Decimal(str(point.get('apy', 0) / 100)),  # Convert from percentage
                        tvl_usd=Decimal(str(point.get('tvlUsd', 0)))
                    ))
                except (ValueError, KeyError) as e:
                    continue

            # Cache results
            if historical_data:
                self._set_cache(cache_key, historical_data)

            return historical_data

        except requests.RequestException as e:
            print(f"Error fetching historical data for pool {pool_id}: {e}")
            return None

    def get_protocol_pools(
        self,
        protocol: str,
        chain: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all pools for a protocol

        Args:
            protocol: Protocol name (e.g., 'aave-v3', 'compound-v3')
            chain: Optional chain filter (e.g., 'Ethereum', 'Polygon')

        Returns:
            List of pool information
        """
        try:
            url = f"{self.YIELDS_API}/pools"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return []

            data = response.json()

            if not data or 'data' not in data:
                return []

            # Filter pools
            pools = []
            for pool in data['data']:
                # Match protocol
                if pool.get('project', '').lower() != protocol.lower():
                    continue

                # Match chain if specified
                if chain and pool.get('chain', '').lower() != chain.lower():
                    continue

                pools.append({
                    'pool_id': pool.get('pool'),
                    'symbol': pool.get('symbol', ''),
                    'chain': pool.get('chain', ''),
                    'project': pool.get('project', ''),
                    'apy': Decimal(str(pool.get('apy', 0) / 100)),
                    'tvl_usd': Decimal(str(pool.get('tvlUsd', 0))),
                    'exposure': pool.get('exposure', ''),
                })

            return pools

        except requests.RequestException as e:
            print(f"Error fetching pools for {protocol}: {e}")
            return []

    def find_pool_by_asset(
        self,
        protocol: str,
        asset_symbol: str,
        chain: str = 'Ethereum'
    ) -> Optional[Dict]:
        """
        Find a specific pool by protocol, asset, and chain

        Args:
            protocol: Protocol name (e.g., 'aave-v3')
            asset_symbol: Asset symbol (e.g., 'USDC', 'DAI')
            chain: Chain name (default 'Ethereum')

        Returns:
            Pool information if found
        """
        pools = self.get_protocol_pools(protocol, chain)

        # Look for exact match
        for pool in pools:
            if asset_symbol.upper() in pool['symbol'].upper():
                return pool

        return None

    def get_historical_data_for_backtest(
        self,
        protocol: str,
        asset_symbol: str,
        chain: str = 'Ethereum',
        days_back: int = 90
    ) -> Optional[List[HistoricalYield]]:
        """
        Get historical data suitable for backtesting

        Args:
            protocol: Protocol name
            asset_symbol: Asset symbol
            chain: Chain name
            days_back: How many days of history to fetch

        Returns:
            List of historical yield data points
        """
        # Find the pool
        pool = self.find_pool_by_asset(protocol, asset_symbol, chain)

        if not pool:
            print(f"Pool not found for {protocol}/{asset_symbol} on {chain}")
            return None

        # Get historical data
        historical = self.get_pool_historical_apy(pool['pool_id'])

        if not historical:
            return None

        # Filter to requested time range (make cutoff timezone-aware)
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        filtered = [h for h in historical if h.timestamp >= cutoff_date]

        # Sort by timestamp
        filtered.sort(key=lambda x: x.timestamp)

        return filtered

    def get_multiple_protocols_history(
        self,
        protocol_assets: List[Dict[str, str]],
        days_back: int = 90
    ) -> Dict[str, List[HistoricalYield]]:
        """
        Get historical data for multiple protocol/asset pairs

        Args:
            protocol_assets: List of dicts with 'protocol', 'asset', 'chain'
            days_back: How many days of history to fetch

        Returns:
            Dictionary mapping key to historical data
        """
        results = {}

        for item in protocol_assets:
            protocol = item.get('protocol')
            asset = item.get('asset')
            chain = item.get('chain', 'Ethereum')

            key = f"{protocol}_{asset}_{chain}"

            historical = self.get_historical_data_for_backtest(
                protocol=protocol, # type: ignore
                asset_symbol=asset, # type: ignore
                chain=chain,
                days_back=days_back
            )

            if historical:
                results[key] = historical

            # Be nice to the API
            time.sleep(0.5)

        return results


if __name__ == "__main__":
    # Example usage
    print("Testing Historical Data Fetcher\n")

    fetcher = HistoricalDataFetcher()

    # Test 1: Find Aave USDC pool
    print("1. Finding Aave V3 USDC pool on Ethereum...")
    pool = fetcher.find_pool_by_asset('aave-v3', 'USDC', 'Ethereum')

    if pool:
        print(f"   Found: {pool['symbol']}")
        print(f"   Pool ID: {pool['pool_id']}")
        print(f"   Current APY: {pool['apy']*100:.2f}%")
        print(f"   TVL: ${pool['tvl_usd']:,.0f}")

        # Test 2: Get historical data
        print("\n2. Fetching 30 days of historical data...")
        historical = fetcher.get_historical_data_for_backtest(
            protocol='aave-v3',
            asset_symbol='USDC',
            chain='Ethereum',
            days_back=30
        )

        if historical:
            print(f"   ✓ Retrieved {len(historical)} data points")
            print(f"   Date range: {historical[0].timestamp.date()} to {historical[-1].timestamp.date()}")

            apys = [float(h.apy * 100) for h in historical]
            print(f"   APY range: {min(apys):.2f}% - {max(apys):.2f}%")
            print(f"   Average APY: {sum(apys)/len(apys):.2f}%")
    else:
        print("   ✗ Pool not found")
