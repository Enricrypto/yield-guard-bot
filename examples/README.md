# Examples

This directory contains example scripts and demos for the Yield Guard Bot.

## Scripts

### Backtest Examples
- `backtest_historical.py` - Run historical backtests with real market data
- `backtest_conservative.py` - Conservative backtest with lower risk parameters
- `demo_1year_backtest.py` - One-year backtest demonstration

### Protocol Demos
- `demo_protocol_fetchers.py` - Demonstrates fetching data from DeFi protocols (Aave, Compound, Morpho)
- `check_morpho_pools.py` - Check available Morpho pools and their rates
- `demo_risk_parameters.py` - Risk parameter configuration examples

### Debugging
- `debug_env.py` - Environment variable debugging utility

## Usage

All examples can be run from the project root:

```bash
# Example: Run historical backtest
python examples/backtest_historical.py

# Example: Check Morpho pools
python examples/check_morpho_pools.py
```

Make sure you have configured your `.env` file with the necessary API keys before running protocol-related examples.
