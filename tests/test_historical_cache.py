#!/usr/bin/env python3
"""
Test Historical Data Caching
Verifies that the database caching system works correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db import DatabaseManager
from src.market_data.historical_fetcher import HistoricalDataFetcher
from datetime import datetime


def test_caching():
    """Test the historical data caching system"""
    print("="*70)
    print(" "*20 + "CACHING SYSTEM TEST")
    print("="*70)

    # Initialize database
    db = DatabaseManager('data/simulations.db')
    db.init_db()
    print("\n✓ Database initialized")

    # Clear any existing cache for this test
    print("✓ Clearing old cache...")
    db.clear_historical_cache()

    # Test 1: Fetch data from API
    print("\n" + "-"*70)
    print("TEST 1: Fetch Fresh Data from API")
    print("-"*70)

    fetcher = HistoricalDataFetcher()

    print("\nFetching 30 days of Aave V3 USDC data...")
    historical = fetcher.get_historical_data_for_backtest(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=30
    )

    if not historical:
        print("❌ Failed to fetch data")
        return False

    print(f"✓ Fetched {len(historical)} data points")

    # Convert to dicts
    historical_dicts = [h.to_dict() for h in historical]

    # Test 2: Save to cache
    print("\n" + "-"*70)
    print("TEST 2: Save to Cache")
    print("-"*70)

    cache_id = db.save_historical_data(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=30,
        historical_data=historical_dicts
    )

    print(f"✓ Saved to cache with ID: {cache_id}")

    # Test 3: Retrieve from cache
    print("\n" + "-"*70)
    print("TEST 3: Retrieve from Cache")
    print("-"*70)

    cached_data = db.get_historical_data(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=30,
        max_age_hours=24
    )

    if cached_data:
        print(f"✓ Retrieved {len(cached_data)} cached data points")
        print(f"  Cache hit! No API call needed")
    else:
        print("❌ Cache miss - data not found")
        return False

    # Test 4: Verify data integrity
    print("\n" + "-"*70)
    print("TEST 4: Verify Data Integrity")
    print("-"*70)

    if len(cached_data) == len(historical_dicts):
        print(f"✓ Data count matches: {len(cached_data)} items")
    else:
        print(f"❌ Data count mismatch: {len(cached_data)} vs {len(historical_dicts)}")
        return False

    # Compare first and last items
    original_first = historical_dicts[0]
    cached_first = cached_data[0]

    if original_first['apy'] == cached_first['apy']:
        print(f"✓ First APY matches: {original_first['apy']:.4f}")
    else:
        print(f"❌ APY mismatch")
        return False

    # Test 5: Update existing cache
    print("\n" + "-"*70)
    print("TEST 5: Update Existing Cache")
    print("-"*70)

    cache_id_2 = db.save_historical_data(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=30,
        historical_data=historical_dicts
    )

    if cache_id == cache_id_2:
        print(f"✓ Cache updated (same ID: {cache_id})")
    else:
        print(f"❌ New cache created instead of update")
        return False

    # Test 6: Different protocol/asset creates new cache
    print("\n" + "-"*70)
    print("TEST 6: Different Protocol Creates New Cache")
    print("-"*70)

    cache_id_3 = db.save_historical_data(
        protocol='aave-v3',
        asset_symbol='DAI',  # Different asset
        chain='Ethereum',
        days_back=30,
        historical_data=historical_dicts[:10]  # Just use subset
    )

    if cache_id_3 != cache_id:
        print(f"✓ New cache created for different asset (ID: {cache_id_3})")
    else:
        print(f"❌ Should have created new cache entry")
        return False

    # Test 7: Stale cache detection
    print("\n" + "-"*70)
    print("TEST 7: Stale Cache Detection")
    print("-"*70)

    # Try to get cache with very short max age
    stale_check = db.get_historical_data(
        protocol='aave-v3',
        asset_symbol='USDC',
        chain='Ethereum',
        days_back=30,
        max_age_hours=0  # Immediately stale
    )

    if stale_check is None:
        print("✓ Stale cache correctly rejected")
    else:
        print("❌ Stale cache should have been rejected")
        return False

    # Test 8: Cache miss for non-existent data
    print("\n" + "-"*70)
    print("TEST 8: Cache Miss for Non-Existent Data")
    print("-"*70)

    missing = db.get_historical_data(
        protocol='compound-v3',
        asset_symbol='WBTC',
        chain='Arbitrum',
        days_back=365,
        max_age_hours=24
    )

    if missing is None:
        print("✓ Correctly returned None for non-existent cache")
    else:
        print("❌ Should return None for cache miss")
        return False

    # Summary
    print("\n" + "="*70)
    print(" "*25 + "TEST SUMMARY")
    print("="*70)
    print("\n✅ ALL TESTS PASSED!")
    print("\nCaching System Features:")
    print("  ✓ Fetch and store historical data")
    print("  ✓ Retrieve cached data")
    print("  ✓ Update existing cache entries")
    print("  ✓ Create separate caches for different assets")
    print("  ✓ Detect and reject stale caches")
    print("  ✓ Handle cache misses gracefully")
    print("\n" + "="*70)

    return True


if __name__ == "__main__":
    try:
        success = test_caching()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
