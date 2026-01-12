"""
Interactive demo of Protocol Fetchers
Shows real-time data from Aave and Morpho protocols
"""

from src.protocols import AaveFetcher, MorphoFetcher, ProtocolComparator
from decimal import Decimal


def demo_aave_fetcher():
    """Demo Aave protocol data fetching"""
    print("\n" + "="*70)
    print("AAVE PROTOCOL DATA FETCHER DEMO")
    print("="*70)

    fetcher = AaveFetcher(network='mainnet')

    # Fetch top assets
    print("\n📊 Fetching top Aave markets on mainnet...")
    reserves = fetcher.get_reserve_data()

    # Sort by liquidity
    top_reserves = sorted(reserves, key=lambda r: r.total_liquidity, reverse=True)[:5]

    print(f"\n🏆 Top 5 Aave Markets by Liquidity:\n")
    print(f"{'Asset':<8} {'Supply APY':>12} {'Borrow APY':>12} {'Liquidity':>15} {'LTV':>8}")
    print("-" * 70)

    for reserve in top_reserves:
        print(f"{reserve.asset_symbol:<8} "
              f"{reserve.liquidity_rate*100:>11.2f}% "
              f"{reserve.variable_borrow_rate*100:>11.2f}% "
              f"${reserve.total_liquidity:>13,.0f} "
              f"{reserve.ltv*100:>7.1f}%")


def demo_morpho_fetcher():
    """Demo Morpho protocol data fetching"""
    print("\n" + "="*70)
    print("MORPHO PROTOCOL DATA FETCHER DEMO")
    print("="*70)

    fetcher = MorphoFetcher(network='mainnet')

    print("\n📊 Fetching Morpho markets on mainnet...")
    markets = fetcher.get_market_data()

    # Filter markets with actual supply
    active_markets = [m for m in markets if m.total_supply > 0]

    # Sort by total supply
    top_markets = sorted(active_markets, key=lambda m: m.total_supply, reverse=True)[:5]

    print(f"\n🏆 Top 5 Morpho Markets by TVL:\n")
    print(f"{'Asset':<8} {'Supply APY':>12} {'Borrow APY':>12} {'TVL':>15} {'APY Boost':>12}")
    print("-" * 70)

    for market in top_markets:
        print(f"{market.asset_symbol:<8} "
              f"{market.supply_apy*100:>11.2f}% "
              f"{market.borrow_apy*100:>11.2f}% "
              f"${market.total_supply:>13,.0f} "
              f"+{market.supply_apy_improvement*100:>10.2f}%")


def demo_protocol_comparator():
    """Demo protocol comparison functionality"""
    print("\n" + "="*70)
    print("PROTOCOL COMPARISON DEMO")
    print("="*70)

    comparator = ProtocolComparator(network='mainnet')

    # Compare popular stablecoins
    assets_to_compare = ['USDC', 'DAI', 'WETH']

    print(f"\n🔍 Comparing Aave vs Morpho for popular assets...\n")
    print(f"{'Asset':<8} {'Aave APY':>12} {'Morpho APY':>12} {'Best':>8} {'Difference':>12}")
    print("-" * 70)

    for symbol in assets_to_compare:
        try:
            comparison = comparator.compare_asset(symbol, use_case='supply')

            aave_apy = comparison.aave_supply_apy * 100
            morpho_apy = comparison.morpho_supply_apy * 100
            best = comparison.better_supply_protocol
            diff = comparison.supply_advantage * 100

            print(f"{symbol:<8} "
                  f"{aave_apy:>11.2f}% "
                  f"{morpho_apy:>11.2f}% "
                  f"{best:>8} "
                  f"{diff:>+11.2f}%")
        except Exception as e:
            print(f"{symbol:<8} Error: {str(e)[:40]}")

    # Find best opportunity
    print(f"\n💰 Finding best yield opportunity across all protocols...")
    best = comparator.find_best_yield_opportunity(min_liquidity=Decimal('1000000'))

    print(f"\n🎯 Best Yield Opportunity:")
    print(f"   Protocol: {best['protocol']}")
    print(f"   Asset:    {best['asset']}")
    print(f"   APY:      {best['apy']:.2f}%")
    print(f"   Liquidity: ${best.get('liquidity', 0):,.0f}")


def demo_detailed_comparison():
    """Demo detailed comparison report"""
    print("\n" + "="*70)
    print("DETAILED COMPARISON REPORT")
    print("="*70)

    comparator = ProtocolComparator(network='mainnet')

    print("\n📋 Generating detailed comparison for USDC...\n")

    try:
        report = comparator.generate_comparison_report('USDC')
        print(report)
    except Exception as e:
        print(f"Error generating report: {e}")


def demo_portfolio_analysis():
    """Demo portfolio-wide analysis"""
    print("\n" + "="*70)
    print("PORTFOLIO ANALYSIS DEMO")
    print("="*70)

    comparator = ProtocolComparator(network='mainnet')

    # Sample portfolio
    portfolio = {
        'USDC': Decimal('50000'),
        'DAI': Decimal('30000'),
        'WETH': Decimal('20000'),
    }

    print(f"\n💼 Analyzing sample portfolio:")
    print(f"   USDC: $50,000")
    print(f"   DAI:  $30,000")
    print(f"   WETH: $20,000")
    print(f"   Total: $100,000")

    recommendations = comparator.get_portfolio_recommendations(portfolio, use_case='supply')

    print(f"\n📊 Portfolio Analysis Results:\n")
    print(f"{'Asset':<8} {'Amount':>12} {'Best Protocol':>15} {'APY Gain':>12}")
    print("-" * 70)

    for asset, rec in recommendations['asset_recommendations'].items():
        print(f"{asset:<8} "
              f"${rec['current_amount']:>11,.0f} "
              f"{rec['recommended_protocol']:>15} "
              f"{rec['apy_gain']:>+11.2f}%")

    print(f"\n💡 Portfolio-Wide Optimization:")
    print(f"   Total APY Improvement: {recommendations['total_apy_improvement']:+.2f}%")
    print(f"   Estimated Annual Gain: ${recommendations['estimated_annual_gain']:+,.2f}")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print(" "*15 + "PROTOCOL FETCHERS - INTERACTIVE DEMO")
    print("="*70)
    print("\nThis demo fetches REAL data from Aave and Morpho protocols")
    print("Data is live from mainnet via Morpho's public GraphQL API")
    print("\nPress Ctrl+C to exit at any time")

    try:
        # Run all demos
        demo_aave_fetcher()
        demo_morpho_fetcher()
        demo_protocol_comparator()
        demo_detailed_comparison()
        demo_portfolio_analysis()

        print("\n" + "="*70)
        print("✅ Demo completed successfully!")
        print("="*70)
        print("\n💡 You can now use these fetchers in your Yield Guard Bot")
        print("   to make real-time protocol comparisons and recommendations!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
