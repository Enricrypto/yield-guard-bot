"""
Test script for Protocol Fetchers
Tests Aave, Morpho, and Protocol Comparator functionality
"""

from src.protocols.aave_fetcher import AaveFetcher
from src.protocols.morpho_fetcher import MorphoFetcher
from src.protocols.protocol_comparator import ProtocolComparator
from decimal import Decimal


def test_aave_fetcher():
    """Test Aave protocol fetcher"""
    print("\n" + "="*60)
    print("TESTING AAVE FETCHER")
    print("="*60)

    try:
        fetcher = AaveFetcher(network='mainnet')
        print("✓ Aave fetcher initialized")

        # Test getting USDC reserve data
        print("\nFetching USDC reserve data...")
        usdc = fetcher.get_reserve_by_symbol('USDC')

        if usdc:
            print(f"✓ Successfully fetched USDC data")
            print(f"  Symbol: {usdc.asset_symbol}")
            print(f"  Supply APY: {usdc.liquidity_rate * 100:.4f}%")
            print(f"  Borrow APY: {usdc.variable_borrow_rate * 100:.4f}%")
            print(f"  LTV: {usdc.ltv * 100:.2f}%")
            print(f"  Liquidation Threshold: {usdc.liquidation_threshold * 100:.2f}%")
            print(f"  Total Liquidity: ${usdc.total_liquidity:,.2f}")
            print(f"  Utilization: {usdc.utilization_rate * 100:.2f}%")
            print(f"  Is Active: {usdc.is_active}")
        else:
            print("✗ Failed to fetch USDC data")

        # Test health metrics
        print("\nFetching health metrics...")
        health = fetcher.get_asset_health_metrics('USDC')
        print(f"✓ Health check: {'Safe' if health['is_safe'] else 'Warning'}")

        # Test multiple reserves
        print("\nFetching multiple reserves...")
        symbols = ['USDC', 'DAI', 'WETH']
        reserves = fetcher.get_multiple_reserves(symbols)
        print(f"✓ Fetched {len(reserves)} reserves: {list(reserves.keys())}")

        return True

    except Exception as e:
        print(f"✗ Aave fetcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_morpho_fetcher():
    """Test Morpho protocol fetcher"""
    print("\n" + "="*60)
    print("TESTING MORPHO FETCHER")
    print("="*60)

    try:
        fetcher = MorphoFetcher(network='mainnet')
        print("✓ Morpho fetcher initialized")

        # Test getting USDC market data
        print("\nFetching USDC market data...")
        usdc = fetcher.get_market_by_symbol('USDC')

        if usdc:
            print(f"✓ Successfully fetched USDC data")
            print(f"  Symbol: {usdc.asset_symbol}")
            print(f"  Morpho Supply APY: {usdc.supply_apy * 100:.4f}%")
            print(f"  Pool Supply APY: {usdc.pool_supply_apy * 100:.4f}%")
            print(f"  P2P Supply APY: {usdc.p2p_supply_apy * 100:.4f}%")
            print(f"  APY Improvement: +{usdc.supply_apy_improvement * 100:.4f}%")
            print(f"  Total Supply: ${usdc.total_supply:,.2f}")
            print(f"  P2P Amount: ${usdc.p2p_supply_amount:,.2f}")
            print(f"  Is Active: {usdc.is_active}")
        else:
            print("✗ Failed to fetch USDC data")

        # Test P2P efficiency
        print("\nCalculating P2P matching efficiency...")
        efficiency = fetcher.get_p2p_matching_efficiency('USDC')
        print(f"✓ P2P Matching Ratio: {efficiency['p2p_matching_ratio']:.2f}%")
        print(f"  APY Improvement: +{efficiency['apy_improvement']:.4f}%")

        # Test market comparison
        print("\nGenerating market comparison...")
        comparison = fetcher.get_market_comparison('USDC')
        print(f"✓ Morpho vs Pool comparison:")
        print(f"  Supply Advantage: +{comparison['supply_advantage']:.4f}%")
        print(f"  Better for Supply: {comparison['is_better_for_supply']}")

        return True

    except Exception as e:
        print(f"✗ Morpho fetcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_protocol_comparator():
    """Test protocol comparator"""
    print("\n" + "="*60)
    print("TESTING PROTOCOL COMPARATOR")
    print("="*60)

    try:
        comparator = ProtocolComparator(network='mainnet')
        print("✓ Protocol comparator initialized")

        # Test single asset comparison
        print("\nComparing USDC on Aave vs Morpho...")
        comparison = comparator.compare_asset('USDC', use_case='supply')

        print(f"✓ Comparison complete")
        print(f"  Asset: {comparison.asset_symbol}")
        print(f"  Aave Supply APY: {comparison.aave_supply_apy * 100:.4f}%")
        print(f"  Morpho Supply APY: {comparison.morpho_supply_apy * 100:.4f}%")
        print(f"  Supply Advantage: {comparison.supply_advantage * 100:+.4f}%")
        print(f"  Better Protocol: {comparison.better_supply_protocol}")
        print(f"  Recommendation: {comparison.recommended_protocol}")
        print(f"  Reason: {comparison.recommendation_reason}")

        # Test multiple assets
        print("\nComparing multiple assets...")
        symbols = ['USDC', 'DAI']
        comparisons = comparator.compare_multiple_assets(symbols, use_case='supply')
        print(f"✓ Compared {len(comparisons)} assets")

        for symbol, comp in comparisons.items():
            print(f"  {symbol}: {comp.recommended_protocol} "
                  f"({comp.supply_advantage * 100:+.2f}%)")

        # Test portfolio recommendations
        print("\nGenerating portfolio recommendations...")
        portfolio = {
            'USDC': Decimal('10000'),
            'DAI': Decimal('5000'),
        }
        recommendations = comparator.get_portfolio_recommendations(portfolio, use_case='supply')
        print(f"✓ Portfolio analysis complete")
        print(f"  Total Value: ${recommendations['total_portfolio_value']:,.2f}")
        print(f"  Total APY Improvement: {recommendations['total_apy_improvement']:+.4f}%")
        print(f"  Est. Annual Gain: ${recommendations['estimated_annual_gain']:,.2f}")

        # Test finding best opportunity
        print("\nFinding best yield opportunity...")
        best = comparator.find_best_yield_opportunity(min_liquidity=Decimal('1000000'))
        print(f"✓ Best opportunity found")
        print(f"  Protocol: {best['protocol']}")
        print(f"  Asset: {best['asset']}")
        print(f"  APY: {best['apy']:.4f}%")

        # Generate full report
        print("\nGenerating comparison report...")
        report = comparator.generate_comparison_report('USDC')
        print(report)

        return True

    except Exception as e:
        print(f"✗ Protocol comparator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PROTOCOL FETCHERS TEST SUITE")
    print("="*60)
    print("\nThis script tests the Aave and Morpho protocol fetchers")
    print("It queries real subgraph data from mainnet")
    print("\nNote: Tests may fail if:")
    print("  - Subgraph endpoints are down")
    print("  - Network connectivity issues")
    print("  - Assets not available on the protocols")

    results = []

    # Run tests
    results.append(("Aave Fetcher", test_aave_fetcher()))
    results.append(("Morpho Fetcher", test_morpho_fetcher()))
    results.append(("Protocol Comparator", test_protocol_comparator()))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
