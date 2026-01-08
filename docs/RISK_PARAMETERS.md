# Dynamic Risk Parameters

## Overview

LTV (Loan-to-Value) and liquidation threshold parameters **do change over time** on lending protocols based on:
- Protocol governance votes
- Risk assessments
- Market conditions
- Asset volatility changes

This feature tracks and applies historical risk parameter changes during simulations.

## Why This Matters

### For Conservative Strategy (No Leverage)
**Impact: Minimal** - Since there's no borrowing (LTV=0), changes to LTV/liquidation thresholds don't affect:
- Health factor (always Infinity)
- Liquidation risk (none)
- Portfolio value

### For Moderate/Aggressive Strategies (With Leverage)
**Impact: Significant** - Parameter changes directly affect:
- **Health Factor**: Even small changes can push positions closer to/further from liquidation
- **Liquidation Risk**: Lower thresholds = higher risk
- **Borrowing Capacity**: LTV changes affect max borrowing

## Example Impact

Position: $100,000 collateral, $70,000 debt (70% LTV)

| Liquidation Threshold | Health Factor | Status |
|-----------------------|---------------|--------|
| 83% (decreased)       | 1.186         | ⚠️ At Risk |
| 85% (original)        | 1.214         | ✅ Safe |
| 87% (increased)       | 1.243         | ✅ Safer |

**A 2% change in liquidation threshold changes health factor by ~5%!**

## Implementation

### 1. Fetch Historical Parameters

```python
from src.market_data.risk_parameter_fetcher import RiskParameterFetcher
from datetime import datetime, timedelta

fetcher = RiskParameterFetcher(network='mainnet')

end_date = datetime.now()
start_date = end_date - timedelta(days=90)

# Fetch USDC risk parameter history
snapshots = fetcher.fetch_risk_parameter_history('USDC', start_date, end_date)

for snapshot in snapshots:
    print(f"Date: {snapshot.timestamp}")
    print(f"LTV: {snapshot.ltv * 100:.1f}%")
    print(f"Liquidation Threshold: {snapshot.liquidation_threshold * 100:.1f}%")
```

### 2. Use in Simulation

```python
from src.market_data.risk_parameter_fetcher import get_risk_parameters_for_simulation
from src.simulator.treasury_simulator import TreasurySimulator

# Get parameters for simulation period
risk_params = get_risk_parameters_for_simulation(
    protocol='aave-v3',
    asset_symbol='USDC',
    start_date=datetime(2024, 1, 1),
    days=90,
    network='mainnet'
)

# Market data generator with dynamic risk parameters
def market_data_generator(day_index: int):
    ltv, liq_threshold = risk_params[day_index]

    return {
        'aave-v3': {
            'USDC': {
                'supply_apy': Decimal('0.05'),
                'borrow_apy': Decimal('0.07'),
                'ltv': ltv,  # Updated daily
                'liquidation_threshold': liq_threshold  # Updated daily
            }
        }
    }

# Run simulation with dynamic parameters
snapshots = treasury.run_simulation(
    days=90,
    market_data_generator=market_data_generator
)
```

### 3. Manual Parameter Updates

You can also manually update risk parameters on positions:

```python
# Update LTV only
position.update_risk_parameters(ltv=Decimal('0.82'))

# Update liquidation threshold only
position.update_risk_parameters(liquidation_threshold=Decimal('0.87'))

# Update both
position.update_risk_parameters(
    ltv=Decimal('0.82'),
    liquidation_threshold=Decimal('0.87')
)
```

## Data Sources

### Aave V3
- **Source**: The Graph (Aave V3 Subgraph)
- **Free**: Yes, no API key required
- **Coverage**: Mainnet, Polygon, Arbitrum, Optimism
- **Data**: Historical `ReserveConfigurationHistoryItem` events

### Compound V3
- **Fallback**: Uses fixed conservative defaults (80% LTV, 85% liquidation threshold)
- **Note**: Could be enhanced to query Compound subgraph in future

### Morpho
- **Fallback**: Uses underlying protocol parameters (Aave/Compound)

## Limitations

1. **Historical Data**: Subgraph data only goes back to protocol deployment
2. **Network Support**: Limited to networks with active subgraphs
3. **Rate Limits**: The Graph has rate limits (~1000 requests/day for free tier)

## Conservative Defaults

If historical data unavailable, the system uses conservative defaults:
- **LTV**: 80%
- **Liquidation Threshold**: 85%
- **Liquidation Bonus**: 5%

## Testing

Run the demo to see dynamic risk parameters in action:

```bash
python demo_risk_parameters.py
```

This demonstrates:
1. Fetching historical parameter changes
2. Running simulations with dynamic parameters
3. Impact of parameter changes on health factor

## Future Enhancements

- [ ] Add Compound V3 subgraph support
- [ ] Cache historical parameters to reduce API calls
- [ ] Add alerts when parameters change significantly
- [ ] Visualize parameter changes over time
- [ ] Support for more assets beyond USDC
