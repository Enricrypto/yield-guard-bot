# Protocol Metrics Fetchers

This module provides real-time data fetching from DeFi lending protocols (Aave and Morpho) and comparison utilities.

## Features

### 1. Aave Fetcher (`aave_fetcher.py`)
Fetches real-time metrics from Aave V3 Protocol using The Graph's subgraph.

**Capabilities:**
- Query reserve data (supply/borrow rates)
- Get liquidation thresholds and LTV ratios
- Check total liquidity and utilization
- Fetch risk parameters
- Support for multiple networks (mainnet, polygon, arbitrum, optimism)

**Example Usage:**
```python
from src.protocols import AaveFetcher

fetcher = AaveFetcher(network='mainnet')

# Get data for a specific asset
usdc = fetcher.get_reserve_by_symbol('USDC')
print(f"Supply APY: {usdc.liquidity_rate * 100:.2f}%")
print(f"LTV: {usdc.ltv * 100:.0f}%")

# Get health metrics
health = fetcher.get_asset_health_metrics('USDC')
print(f"Is Safe: {health['is_safe']}")
```

### 2. Morpho Fetcher (`morpho_fetcher.py`)
Fetches real-time metrics from Morpho Protocol, which optimizes yields on top of Aave through P2P matching.

**Capabilities:**
- Query market data with enhanced P2P rates
- Compare P2P vs pool rates
- Calculate APY improvements over base protocol
- Check P2P matching efficiency
- Support for mainnet and polygon

**Example Usage:**
```python
from src.protocols import MorphoFetcher

fetcher = MorphoFetcher(network='mainnet')

# Get market data
usdc = fetcher.get_market_by_symbol('USDC')
print(f"Morpho APY: {usdc.supply_apy * 100:.2f}%")
print(f"Improvement over Aave: +{usdc.supply_apy_improvement * 100:.2f}%")

# Check P2P efficiency
efficiency = fetcher.get_p2p_matching_efficiency('USDC')
print(f"P2P Matching: {efficiency['p2p_matching_ratio']:.1f}%")
```

### 3. Protocol Comparator (`protocol_comparator.py`)
Compares Aave and Morpho to determine which protocol offers better terms.

**Capabilities:**
- Compare supply and borrow rates
- Analyze risk parameters
- Make protocol recommendations
- Calculate portfolio-wide improvements
- Generate comparison reports

**Example Usage:**
```python
from src.protocols import ProtocolComparator
from decimal import Decimal

comparator = ProtocolComparator(network='mainnet')

# Compare single asset
comparison = comparator.compare_asset('USDC', use_case='supply')
print(f"Recommended: {comparison.recommended_protocol}")
print(f"Reason: {comparison.recommendation_reason}")

# Analyze portfolio
portfolio = {
    'USDC': Decimal('10000'),
    'DAI': Decimal('5000'),
}
recommendations = comparator.get_portfolio_recommendations(portfolio)
print(f"Total APY Improvement: {recommendations['total_apy_improvement']:.2f}%")

# Find best opportunity
best = comparator.find_best_yield_opportunity()
print(f"Best yield: {best['asset']} on {best['protocol']} at {best['apy']:.2f}%")
```

## Data Sources

### Aave Subgraphs
- **Mainnet**: `https://api.thegraph.com/subgraphs/name/aave/protocol-v3`
- **Polygon**: `https://api.thegraph.com/subgraphs/name/aave/protocol-v3-polygon`
- **Arbitrum**: `https://api.thegraph.com/subgraphs/name/aave/protocol-v3-arbitrum`
- **Optimism**: `https://api.thegraph.com/subgraphs/name/aave/protocol-v3-optimism`

### Morpho Subgraphs
- **Mainnet**: `https://api.thegraph.com/subgraphs/name/morpho-labs/morpho-aave-v3-mainnet`
- **Polygon**: `https://api.thegraph.com/subgraphs/name/morpho-labs/morpho-aave-v3-polygon`

## Data Structures

### AaveReserveData
```python
@dataclass
class AaveReserveData:
    asset_symbol: str
    liquidity_rate: Decimal          # Supply APY
    variable_borrow_rate: Decimal    # Borrow APY
    ltv: Decimal                     # Loan-to-Value
    liquidation_threshold: Decimal   # Liquidation threshold
    total_liquidity: Decimal         # Total available liquidity
    utilization_rate: Decimal        # Pool utilization
    # ... and more
```

### MorphoMarketData
```python
@dataclass
class MorphoMarketData:
    asset_symbol: str
    supply_apy: Decimal              # Blended supply rate
    p2p_supply_apy: Decimal          # P2P matched rate
    pool_supply_apy: Decimal         # Underlying pool rate
    supply_apy_improvement: Decimal  # Improvement over pool
    p2p_supply_amount: Decimal       # Amount matched P2P
    # ... and more
```

### ProtocolComparison
```python
@dataclass
class ProtocolComparison:
    asset_symbol: str
    aave_supply_apy: Decimal
    morpho_supply_apy: Decimal
    supply_advantage: Decimal
    recommended_protocol: str
    recommendation_reason: str
    # ... and more
```

## Testing

Run the test suite:
```bash
python test_protocol_fetchers.py
```

This will test:
- Aave data fetching
- Morpho data fetching
- Protocol comparison
- Portfolio recommendations

## Notes

- All rates are returned as Decimals (e.g., 0.05 = 5%)
- Multiply by 100 to display as percentage
- Requires active internet connection to query subgraphs
- Data is fetched in real-time from on-chain sources
- Subgraph data may have slight delays (~few minutes)

## Dependencies

- `requests`: For HTTP requests to subgraphs
- `decimal`: For precise financial calculations
- `dataclasses`: For structured data objects

## Error Handling

All fetchers include error handling for:
- Network connectivity issues
- Invalid asset symbols
- Subgraph query errors
- Missing data

Errors are raised as Python exceptions with descriptive messages.
