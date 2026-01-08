#!/usr/bin/env python3
"""
Check what Morpho pools are available in DefiLlama
"""

import requests

def search_morpho_pools():
    """Search for Morpho pools in DefiLlama"""
    print("Searching for Morpho pools in DefiLlama...\n")

    try:
        url = "https://yields.llama.fi/pools"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"Error: Status code {response.status_code}")
            return

        data = response.json()

        if not data or 'data' not in data:
            print("No data returned")
            return

        # Search for Morpho pools
        morpho_pools = []
        for pool in data['data']:
            project = pool.get('project', '').lower()
            if 'morpho' in project:
                morpho_pools.append(pool)

        print(f"Found {len(morpho_pools)} Morpho pools\n")

        if not morpho_pools:
            print("No Morpho pools found!")
            print("\nSearching for pools with 'morph' in the name...")

            # Broader search
            similar = []
            for pool in data['data']:
                project = pool.get('project', '').lower()
                symbol = pool.get('symbol', '').lower()
                if 'morph' in project or 'morph' in symbol:
                    similar.append(pool)

            if similar:
                print(f"Found {len(similar)} similar pools:")
                for pool in similar[:10]:  # Show first 10
                    print(f"  - {pool.get('project')}: {pool.get('symbol')} ({pool.get('chain')})")
        else:
            # Group by chain and asset
            print("Morpho Pools by Chain:")

            chains = {}
            for pool in morpho_pools:
                chain = pool.get('chain', 'Unknown')
                if chain not in chains:
                    chains[chain] = []
                chains[chain].append(pool)

            for chain, pools in chains.items():
                print(f"\n{chain}:")
                for pool in pools[:5]:  # Show first 5 per chain
                    symbol = pool.get('symbol', '')
                    apy = pool.get('apy', 0)
                    tvl = pool.get('tvlUsd', 0)
                    project = pool.get('project', '')
                    pool_id = pool.get('pool', '')

                    print(f"  {symbol:8} | APY: {apy:.2f}% | TVL: ${tvl:>12,.0f}")
                    print(f"           | Project: {project}")
                    print(f"           | Pool ID: {pool_id}")
                    print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_morpho_pools()
