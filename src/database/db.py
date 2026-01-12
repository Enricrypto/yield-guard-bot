"""
Database Management for Simulation Results
Uses SQLite for persistent storage of simulation runs and portfolio snapshots
"""

import sqlite3
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class SimulationRun:
    """Represents a single simulation run"""
    strategy_name: str
    initial_capital: float
    simulation_days: int
    protocols_used: str  # Comma-separated list
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    final_value: float
    created_at: datetime
    total_gas_fees: float = 0.0
    num_rebalances: int = 0
    sortino_ratio: float = 0.0
    win_rate: float = 0.0
    worst_daily_loss: float = 0.0  # Worst single-day loss experienced
    # Index-based fields
    index_return: float = 0.0  # Return based on share price index (TWR)
    final_index: float = 1.0  # Final share price index value
    harvest_frequency_days: int = 3  # How often harvests occurred
    id: Optional[int] = None


@dataclass
class PortfolioSnapshot:
    """Represents a portfolio state at a specific point in time"""
    simulation_id: int
    day: int
    net_value: float
    total_collateral: float
    total_debt: float
    overall_health_factor: Optional[float]
    cumulative_yield: float
    timestamp: datetime
    # Index-based fields
    share_price_index: float = 1.0  # Weighted avg share price index across positions
    realized_yield: float = 0.0  # Harvested yield (in index)
    unrealized_yield: float = 0.0  # Pending yield (before harvest)
    num_harvests: int = 0  # Number of harvests so far
    # Real-time drawdown tracking
    current_drawdown: float = 0.0  # Current drawdown from peak
    peak_value: float = 0.0  # Running peak value
    id: Optional[int] = None


@dataclass
class HistoricalDataCache:
    """Cached historical market data"""
    protocol: str
    asset_symbol: str
    chain: str
    days_back: int
    data_json: str  # JSON string of historical data points
    fetched_at: datetime
    id: Optional[int] = None


class DatabaseManager:
    """
    Manages SQLite database for simulation results
    """

    def __init__(self, db_path: str = 'data/simulations.db'):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create simulation_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                simulation_days INTEGER NOT NULL,
                protocols_used TEXT NOT NULL,
                total_return REAL NOT NULL,
                annualized_return REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                sharpe_ratio REAL NOT NULL,
                final_value REAL NOT NULL,
                total_gas_fees REAL DEFAULT 0.0,
                num_rebalances INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL
            )
        """)

        # Create portfolio_snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id INTEGER NOT NULL,
                day INTEGER NOT NULL,
                net_value REAL NOT NULL,
                total_collateral REAL NOT NULL,
                total_debt REAL NOT NULL,
                overall_health_factor REAL,
                cumulative_yield REAL NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (simulation_id) REFERENCES simulation_runs(id)
            )
        """)

        # Create historical_data_cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_data_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol TEXT NOT NULL,
                asset_symbol TEXT NOT NULL,
                chain TEXT NOT NULL,
                days_back INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                fetched_at TIMESTAMP NOT NULL
            )
        """)

        # Create indices for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_simulation_runs_created_at
            ON simulation_runs(created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_simulation_id
            ON portfolio_snapshots(simulation_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_historical_cache_lookup
            ON historical_data_cache(protocol, asset_symbol, chain, days_back)
        """)

        # Migration: Add sortino_ratio and win_rate columns if they don't exist
        try:
            cursor.execute("ALTER TABLE simulation_runs ADD COLUMN sortino_ratio REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE simulation_runs ADD COLUMN win_rate REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Migration: Add worst-case period loss tracking
        try:
            cursor.execute("ALTER TABLE simulation_runs ADD COLUMN worst_daily_loss REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Migration: Add index tracking columns to portfolio_snapshots
        try:
            cursor.execute("ALTER TABLE portfolio_snapshots ADD COLUMN share_price_index REAL DEFAULT 1.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE portfolio_snapshots ADD COLUMN realized_yield REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE portfolio_snapshots ADD COLUMN unrealized_yield REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Migration: Add real-time drawdown tracking columns
        try:
            cursor.execute("ALTER TABLE portfolio_snapshots ADD COLUMN current_drawdown REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE portfolio_snapshots ADD COLUMN peak_value REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE portfolio_snapshots ADD COLUMN num_harvests INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Migration: Add index-based return fields to simulation_runs
        try:
            cursor.execute("ALTER TABLE simulation_runs ADD COLUMN index_return REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE simulation_runs ADD COLUMN final_index REAL DEFAULT 1.0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE simulation_runs ADD COLUMN harvest_frequency_days INTEGER DEFAULT 3")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        conn.close()

    def save_simulation_run(self, simulation: SimulationRun) -> int:
        """
        Save simulation run to database

        Args:
            simulation: SimulationRun object

        Returns:
            ID of saved simulation
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO simulation_runs (
                strategy_name, initial_capital, simulation_days,
                protocols_used, total_return, annualized_return,
                max_drawdown, sharpe_ratio, final_value, total_gas_fees,
                num_rebalances, sortino_ratio, win_rate, worst_daily_loss,
                index_return, final_index, harvest_frequency_days, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            simulation.strategy_name,
            simulation.initial_capital,
            simulation.simulation_days,
            simulation.protocols_used,
            simulation.total_return,
            simulation.annualized_return,
            simulation.max_drawdown,
            simulation.sharpe_ratio,
            simulation.final_value,
            simulation.total_gas_fees,
            simulation.num_rebalances,
            simulation.sortino_ratio,
            simulation.win_rate,
            simulation.worst_daily_loss,
            simulation.index_return,
            simulation.final_index,
            simulation.harvest_frequency_days,
            simulation.created_at
        ))

        simulation_id = cursor.lastrowid
        simulation.id = simulation_id

        conn.commit()
        conn.close()

        return int(simulation_id) # type: ignore

    def save_portfolio_snapshot(self, snapshot: PortfolioSnapshot) -> int:
        """
        Save portfolio snapshot to database

        Args:
            snapshot: PortfolioSnapshot object

        Returns:
            ID of saved snapshot
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO portfolio_snapshots (
                simulation_id, day, net_value, total_collateral,
                total_debt, overall_health_factor, cumulative_yield, timestamp,
                share_price_index, realized_yield, unrealized_yield, num_harvests,
                current_drawdown, peak_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.simulation_id,
            snapshot.day,
            snapshot.net_value,
            snapshot.total_collateral,
            snapshot.total_debt,
            snapshot.overall_health_factor,
            snapshot.cumulative_yield,
            snapshot.timestamp,
            snapshot.share_price_index,
            snapshot.realized_yield,
            snapshot.unrealized_yield,
            snapshot.num_harvests,
            snapshot.current_drawdown,
            snapshot.peak_value
        ))

        snapshot_id = cursor.lastrowid
        snapshot.id = snapshot_id

        conn.commit()
        conn.close()

        return int(snapshot_id) # type: ignore

    def get_simulation_by_id(self, simulation_id: int) -> Optional[SimulationRun]:
        """
        Get simulation run by ID

        Args:
            simulation_id: Simulation ID

        Returns:
            SimulationRun object or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM simulation_runs WHERE id = ?
        """, (simulation_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return SimulationRun(
            id=row['id'],
            strategy_name=row['strategy_name'],
            initial_capital=row['initial_capital'],
            simulation_days=row['simulation_days'],
            protocols_used=row['protocols_used'],
            total_return=row['total_return'],
            annualized_return=row['annualized_return'],
            max_drawdown=row['max_drawdown'],
            sharpe_ratio=row['sharpe_ratio'],
            final_value=row['final_value'],
            created_at=datetime.fromisoformat(row['created_at'])
        )

    def get_recent_simulations(self, limit: int = 10) -> List[SimulationRun]:
        """
        Get most recent simulation runs

        Args:
            limit: Maximum number of results

        Returns:
            List of SimulationRun objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM simulation_runs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        simulations = []
        for row in rows:
            simulations.append(SimulationRun(
                id=row['id'],
                strategy_name=row['strategy_name'],
                initial_capital=row['initial_capital'],
                simulation_days=row['simulation_days'],
                protocols_used=row['protocols_used'],
                total_return=row['total_return'],
                annualized_return=row['annualized_return'],
                max_drawdown=row['max_drawdown'],
                sharpe_ratio=row['sharpe_ratio'],
                final_value=row['final_value'],
                created_at=datetime.fromisoformat(row['created_at'])
            ))

        return simulations

    def get_snapshots_for_simulation(self, simulation_id: int) -> List[PortfolioSnapshot]:
        """
        Get all portfolio snapshots for a simulation

        Args:
            simulation_id: Simulation ID

        Returns:
            List of PortfolioSnapshot objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM portfolio_snapshots
            WHERE simulation_id = ?
            ORDER BY day ASC
        """, (simulation_id,))

        rows = cursor.fetchall()
        conn.close()

        snapshots = []
        for row in rows:
            snapshots.append(PortfolioSnapshot(
                id=row['id'],
                simulation_id=row['simulation_id'],
                day=row['day'],
                net_value=row['net_value'],
                total_collateral=row['total_collateral'],
                total_debt=row['total_debt'],
                overall_health_factor=row['overall_health_factor'],
                cumulative_yield=row['cumulative_yield'],
                timestamp=datetime.fromisoformat(row['timestamp'])
            ))

        return snapshots

    def get_simulations_by_strategy(self, strategy_name: str, limit: int = 10) -> List[SimulationRun]:
        """
        Get simulation runs for a specific strategy

        Args:
            strategy_name: Strategy name (e.g., 'Conservative')
            limit: Maximum number of results

        Returns:
            List of SimulationRun objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM simulation_runs
            WHERE strategy_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (strategy_name, limit))

        rows = cursor.fetchall()
        conn.close()

        simulations = []
        for row in rows:
            simulations.append(SimulationRun(
                id=row['id'],
                strategy_name=row['strategy_name'],
                initial_capital=row['initial_capital'],
                simulation_days=row['simulation_days'],
                protocols_used=row['protocols_used'],
                total_return=row['total_return'],
                annualized_return=row['annualized_return'],
                max_drawdown=row['max_drawdown'],
                sharpe_ratio=row['sharpe_ratio'],
                final_value=row['final_value'],
                created_at=datetime.fromisoformat(row['created_at'])
            ))

        return simulations

    def delete_simulation(self, simulation_id: int):
        """
        Delete simulation and all its snapshots

        Args:
            simulation_id: Simulation ID to delete
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete snapshots first (foreign key constraint)
        cursor.execute("""
            DELETE FROM portfolio_snapshots WHERE simulation_id = ?
        """, (simulation_id,))

        # Delete simulation
        cursor.execute("""
            DELETE FROM simulation_runs WHERE id = ?
        """, (simulation_id,))

        conn.commit()
        conn.close()

    def save_historical_data(
        self,
        protocol: str,
        asset_symbol: str,
        chain: str,
        days_back: int,
        historical_data: List[dict]
    ) -> int:
        """
        Save historical market data to cache

        Args:
            protocol: Protocol name (e.g., 'aave-v3')
            asset_symbol: Asset symbol (e.g., 'USDC')
            chain: Chain name (e.g., 'Ethereum')
            days_back: Number of days of historical data
            historical_data: List of historical data points as dicts

        Returns:
            Cache ID
        """
        import json

        conn = self._get_connection()
        cursor = conn.cursor()

        # Convert historical data to JSON
        data_json = json.dumps(historical_data)

        # Check if cache already exists
        cursor.execute("""
            SELECT id FROM historical_data_cache
            WHERE protocol = ? AND asset_symbol = ? AND chain = ? AND days_back = ?
        """, (protocol, asset_symbol, chain, days_back))

        existing = cursor.fetchone()

        if existing:
            # Update existing cache
            cursor.execute("""
                UPDATE historical_data_cache
                SET data_json = ?, fetched_at = ?
                WHERE id = ?
            """, (data_json, datetime.now().isoformat(), existing['id']))

            cache_id = existing['id']
        else:
            # Insert new cache
            cursor.execute("""
                INSERT INTO historical_data_cache (
                    protocol, asset_symbol, chain, days_back, data_json, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                protocol,
                asset_symbol,
                chain,
                days_back,
                data_json,
                datetime.now().isoformat()
            ))

            cache_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return int(cache_id) # type: ignore

    def get_historical_data(
        self,
        protocol: str,
        asset_symbol: str,
        chain: str,
        days_back: int,
        max_age_hours: int = 24
    ) -> Optional[List[dict]]:
        """
        Get cached historical data if available and not stale

        Args:
            protocol: Protocol name
            asset_symbol: Asset symbol
            chain: Chain name
            days_back: Number of days
            max_age_hours: Maximum age of cache in hours (default 24)

        Returns:
            List of historical data points or None if not cached/stale
        """
        import json
        from datetime import timedelta

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data_json, fetched_at FROM historical_data_cache
            WHERE protocol = ? AND asset_symbol = ? AND chain = ? AND days_back = ?
        """, (protocol, asset_symbol, chain, days_back))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Check if cache is stale
        fetched_at = datetime.fromisoformat(row['fetched_at'])
        age = datetime.now() - fetched_at

        if age > timedelta(hours=max_age_hours):
            return None  # Cache is stale

        # Parse and return data
        return json.loads(row['data_json'])

    def clear_historical_cache(self, older_than_days: Optional[int] = None):
        """
        Clear historical data cache

        Args:
            older_than_days: Only clear cache older than this many days (None = clear all)
        """
        from datetime import timedelta

        conn = self._get_connection()
        cursor = conn.cursor()

        if older_than_days is not None:
            cutoff = datetime.now() - timedelta(days=older_than_days)
            cursor.execute("""
                DELETE FROM historical_data_cache
                WHERE fetched_at < ?
            """, (cutoff.isoformat(),))
        else:
            cursor.execute("DELETE FROM historical_data_cache")

        conn.commit()
        conn.close()
