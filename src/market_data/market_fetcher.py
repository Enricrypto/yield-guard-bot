"""
Real Market Data Fetcher
Fetches real market data from multiple sources:
- DefiLlama for TVL and protocol data
- Our protocol fetchers for APY data
- Combining real-time data with historical trends
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from decimal import Decimal
import time


@dataclass
class MarketData:
    """Real market data snapshot"""
    timestamp: datetime
    protocol: str
    asset_symbol: str

    # APY data
    supply_apy: Decimal
    borrow_apy: Decimal

    # TVL data
    tvl_usd: Decimal

    # Additional metrics
    utilization_rate: Optional[Decimal] = None
    total_borrowed: Optional[Decimal] = None
    available_liquidity: Optional[Decimal] = None


class MarketDataFetcher:
    """
    Fetches real market data from multiple sources
    """

    # DefiLlama API endpoints
    DEFILLAMA_BASE = 'https://api.llama.fi'
    DEFILLAMA_YIELDS = 'https://yields.llama.fi'

    # Protocol IDs in DefiLlama
    PROTOCOL_IDS = {
        'aave-v3': 'aave-v3',
        'morpho': 'morpho-blue',
    }

    def __init__(self, cache_ttl: int = 300):
        """
        Initialize market data fetcher

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}

    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        return '_'.join(str(arg) for arg in args)

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache_timestamps:
            return False

        age = time.time() - self._cache_timestamps[key]
        return age < self.cache_ttl

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if valid"""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None

    def _set_cache(self, key: str, value: Any):
        """Set cached data"""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def get_protocol_tvl(self, protocol_name: str) -> Optional[Decimal]:
        """
        Get current TVL for a protocol from DefiLlama

        Args:
            protocol_name: Protocol name ('aave-v3' or 'morpho')

        Returns:
            TVL in USD or None if unavailable
        """
        cache_key = self._get_cache_key('tvl', protocol_name)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        protocol_id = self.PROTOCOL_IDS.get(protocol_name)
        if not protocol_id:
            raise ValueError(f"Unknown protocol: {protocol_name}")

        try:
            url = f"{self.DEFILLAMA_BASE}/tvl/{protocol_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            tvl = Decimal(str(response.json()))
            self._set_cache(cache_key, tvl)
            return tvl

        except Exception as e:
            print(f"Warning: Could not fetch TVL for {protocol_name}: {e}")
            return None

    def get_protocol_historical_tvl(
        self,
        protocol_name: str,
        days: int = 30
    ) -> List[Dict]:
        """
        Get historical TVL data from DefiLlama

        Args:
            protocol_name: Protocol name
            days: Number of days of history

        Returns:
            List of {date, tvl} dictionaries
        """
        cache_key = self._get_cache_key('hist_tvl', protocol_name, days)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        protocol_id = self.PROTOCOL_IDS.get(protocol_name)
        if not protocol_id:
            raise ValueError(f"Unknown protocol: {protocol_name}")

        try:
            url = f"{self.DEFILLAMA_BASE}/protocol/{protocol_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            tvl_data = data.get('tvl', [])

            # Filter to requested time range
            cutoff = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff.timestamp())

            historical = [
                {
                    'date': datetime.fromtimestamp(item['date']),
                    'tvl': Decimal(str(item['totalLiquidityUSD']))
                }
                for item in tvl_data
                if item['date'] >= cutoff_timestamp
            ]

            self._set_cache(cache_key, historical)
            return historical

        except Exception as e:
            print(f"Warning: Could not fetch historical TVL for {protocol_name}: {e}")
            return []

    def get_yields_data(
        self,
        protocol_name: Optional[str] = None,
        chain: str = 'Ethereum'
    ) -> List[Dict]:
        """
        Get yield/APY data from DefiLlama Yields API

        Args:
            protocol_name: Optional protocol filter
            chain: Blockchain network

        Returns:
            List of pool data with APY information
        """
        cache_key = self._get_cache_key('yields', protocol_name, chain)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            url = f"{self.DEFILLAMA_YIELDS}/pools"
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            all_pools = response.json().get('data', [])

            # Filter by chain and protocol
            filtered_pools = [
                pool for pool in all_pools
                if pool.get('chain', '').lower() == chain.lower()
                and (protocol_name is None or protocol_name.lower() in pool.get('project', '').lower())
            ]

            self._set_cache(cache_key, filtered_pools)
            return filtered_pools

        except Exception as e:
            print(f"Warning: Could not fetch yields data: {e}")
            return []

    def get_market_snapshot(
        self,
        protocol_name: str,
        asset_symbol: str = 'USDC'
    ) -> Optional[MarketData]:
        """
        Get current market snapshot combining data from multiple sources

        Args:
            protocol_name: Protocol name
            asset_symbol: Asset symbol

        Returns:
            MarketData object or None
        """
        # Get TVL
        tvl = self.get_protocol_tvl(protocol_name)

        # Get yields data
        yields_data = self.get_yields_data(protocol_name=protocol_name)

        # Find matching pool
        matching_pool = None
        for pool in yields_data:
            if asset_symbol.lower() in pool.get('symbol', '').lower():
                matching_pool = pool
                break

        if matching_pool:
            supply_apy = Decimal(str(matching_pool.get('apy', 0))) / Decimal('100')
            borrow_apy = Decimal(str(matching_pool.get('apyBorrow', supply_apy * Decimal('1.4')))) / Decimal('100')
            utilization = Decimal(str(matching_pool.get('mu', 0))) / Decimal('100') if matching_pool.get('mu') else None
        else:
            # Fallback to defaults
            supply_apy = Decimal('0.05')
            borrow_apy = Decimal('0.07')
            utilization = None

        return MarketData(
            timestamp=datetime.now(),
            protocol=protocol_name,
            asset_symbol=asset_symbol,
            supply_apy=supply_apy,
            borrow_apy=borrow_apy,
            tvl_usd=tvl or Decimal('0'),
            utilization_rate=utilization
        )

    def get_combined_data(
        self,
        protocols: Optional[List[str]] = None,
        assets: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, MarketData]]:
        """
        Get data for multiple protocols and assets

        Args:
            protocols: List of protocol names
            assets: List of asset symbols

        Returns:
            Nested dict: {protocol: {asset: MarketData}}
        """
        if protocols is None:
            protocols = ['aave-v3', 'morpho']
        if assets is None:
            assets = ['USDC', 'DAI', 'WETH']

        result = {}

        for protocol in protocols:
            result[protocol] = {}
            for asset in assets:
                try:
                    data = self.get_market_snapshot(protocol, asset)
                    if data:
                        result[protocol][asset] = data
                except Exception as e:
                    print(f"Warning: Could not fetch data for {protocol}/{asset}: {e}")

        return result

    def get_health_status(self) -> Dict:
        """
        Check health of data sources

        Returns:
            Dictionary with health status of each source
        """
        status = {
            'defillama_api': False,
            'defillama_yields': False,
            'timestamp': datetime.now().isoformat()
        }

        # Test DefiLlama API
        try:
            response = requests.get(f"{self.DEFILLAMA_BASE}/protocols", timeout=5)
            status['defillama_api'] = response.status_code == 200
        except:
            pass

        # Test DefiLlama Yields
        try:
            response = requests.get(f"{self.DEFILLAMA_YIELDS}/pools", timeout=5)
            status['defillama_yields'] = response.status_code == 200
        except:
            pass

        status['overall_healthy'] = all([
            status['defillama_api'],
            status['defillama_yields']
        ])

        return status


if __name__ == "__main__":
    # Example usage
    fetcher = MarketDataFetcher()

    print("Testing Market Data Fetcher...")
    print("\n1. Checking health status...")
    health = fetcher.get_health_status()
    print(f"   DefiLlama API: {'✓' if health['defillama_api'] else '✗'}")
    print(f"   DefiLlama Yields: {'✓' if health['defillama_yields'] else '✗'}")
    print(f"   Overall: {'✓' if health['overall_healthy'] else '✗'}")

    print("\n2. Fetching Aave V3 TVL...")
    tvl = fetcher.get_protocol_tvl('aave-v3')
    if tvl:
        print(f"   TVL: ${tvl:,.0f}")
    else:
        print("   Could not fetch TVL")

    print("\n3. Fetching market snapshot for USDC...")
    snapshot = fetcher.get_market_snapshot('aave-v3', 'USDC')
    if snapshot:
        print(f"   Protocol: {snapshot.protocol}")
        print(f"   Supply APY: {snapshot.supply_apy * 100:.2f}%")
        print(f"   Borrow APY: {snapshot.borrow_apy * 100:.2f}%")
        print(f"   TVL: ${snapshot.tvl_usd:,.0f}")

    print("\n4. Fetching combined data...")
    combined = fetcher.get_combined_data(protocols=['aave-v3'], assets=['USDC', 'DAI'])
    for protocol, assets in combined.items():
        print(f"\n   {protocol}:")
        for asset, data in assets.items():
            print(f"     {asset}: {data.supply_apy * 100:.2f}% APY")
