# Automation Scripts

Scripts for automated daily simulations and reporting.

## Scripts

### daily_simulation.py

Main automation script that runs simulations and saves results to database.

**Usage:**

```bash
# Run daily simulation with default parameters
python scripts/daily_simulation.py

# Run with custom parameters
python scripts/daily_simulation.py --capital 1000000 --days 1

# View summary of recent simulations
python scripts/daily_simulation.py --summary-only

# Use custom database path
python scripts/daily_simulation.py --db-path /path/to/db.sqlite
```

**Options:**

- `--capital`: Initial capital (default: 1000000)
- `--days`: Number of days to simulate (default: 1)
- `--db-path`: Database file path (default: data/simulations.db)
- `--summary-only`: Only show summary of recent simulations

**What it does:**

1. Initializes SQLite database
2. Fetches current market data from DeFi protocols (Aave V3, Compound V3, Morpho)
3. Creates conservative strategy portfolio
4. Runs simulation
5. Calculates performance metrics
6. Saves results to database
7. Displays summary report

### setup_cron.sh

Helper script to set up automated daily execution via cron.

**Usage:**

```bash
./scripts/setup_cron.sh
```

This will display instructions and a ready-to-use cron entry.

## Setting Up Automated Daily Runs

### Option 1: Using Cron (Recommended for local/server)

1. Run the setup helper:
   ```bash
   ./scripts/setup_cron.sh
   ```

2. Follow the displayed instructions to add the cron job

3. Verify cron job:
   ```bash
   crontab -l
   ```

4. Check logs:
   ```bash
   tail -f logs/daily_simulation.log
   ```

### Option 2: Manual Execution

Run the script manually whenever needed:

```bash
source .venv/bin/activate
python scripts/daily_simulation.py
```

## Database Schema

The simulation results are stored in SQLite with two main tables:

### simulation_runs

Stores high-level simulation metadata and results:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| strategy_name | TEXT | Strategy name (e.g., 'Conservative') |
| initial_capital | REAL | Starting capital |
| simulation_days | INTEGER | Number of days simulated |
| protocols_used | TEXT | Comma-separated protocol list |
| total_return | REAL | Total return (decimal) |
| annualized_return | REAL | Annualized return (decimal) |
| max_drawdown | REAL | Maximum drawdown (decimal) |
| sharpe_ratio | REAL | Sharpe ratio |
| final_value | REAL | Final portfolio value |
| created_at | TIMESTAMP | When simulation was run |

### portfolio_snapshots

Stores daily portfolio states:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| simulation_id | INTEGER | Foreign key to simulation_runs |
| day | INTEGER | Day number in simulation |
| net_value | REAL | Net portfolio value |
| total_collateral | REAL | Total collateral |
| total_debt | REAL | Total debt |
| overall_health_factor | REAL | Health factor (NULL if no debt) |
| cumulative_yield | REAL | Cumulative yield earned |
| timestamp | TIMESTAMP | Snapshot timestamp |

## Viewing Results

### Command Line

View recent simulations:

```bash
python scripts/daily_simulation.py --summary-only
```

### Python API

Query database programmatically:

```python
from src.database.db import DatabaseManager

db = DatabaseManager('data/simulations.db')

# Get recent simulations
recent = db.get_recent_simulations(limit=10)
for sim in recent:
    print(f"{sim.strategy_name}: {sim.total_return*100:.2f}% return")

# Get snapshots for a specific simulation
snapshots = db.get_snapshots_for_simulation(simulation_id=1)
for snapshot in snapshots:
    print(f"Day {snapshot.day}: ${snapshot.net_value:,.2f}")
```

## Logs

Logs are stored in `logs/daily_simulation.log` when running via cron.

View logs:

```bash
# View entire log
cat logs/daily_simulation.log

# View last 50 lines
tail -n 50 logs/daily_simulation.log

# Follow log in real-time
tail -f logs/daily_simulation.log
```

## Troubleshooting

### Script fails to run

1. Check virtual environment is activated:
   ```bash
   source .venv/bin/activate
   ```

2. Verify dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

3. Check Python path in cron:
   ```bash
   which python
   ```

### No market data

If the script reports "No market data available", check:

1. Internet connection
2. DefiLlama API availability
3. Protocol names are correct (aave-v3, compound-v3, morpho-v1)

### Database issues

If database errors occur:

1. Check database file exists and is writable:
   ```bash
   ls -la data/simulations.db
   ```

2. Reinitialize database:
   ```bash
   rm data/simulations.db
   python scripts/daily_simulation.py
   ```

## Future Enhancements

Potential improvements:

- [ ] Support for moderate and aggressive strategies
- [ ] Email/Slack notifications on simulation completion
- [ ] Web dashboard for viewing results
- [ ] Automatic rebalancing based on performance
- [ ] Multi-strategy comparison reports
- [ ] Export results to CSV/Excel
- [ ] Integration with monitoring tools (Prometheus, Grafana)
