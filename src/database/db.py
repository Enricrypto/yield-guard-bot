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

        # Create indices for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_simulation_runs_created_at
            ON simulation_runs(created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_simulation_id
            ON portfolio_snapshots(simulation_id)
        """)

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
                max_drawdown, sharpe_ratio, final_value, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                total_debt, overall_health_factor, cumulative_yield, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.simulation_id,
            snapshot.day,
            snapshot.net_value,
            snapshot.total_collateral,
            snapshot.total_debt,
            snapshot.overall_health_factor,
            snapshot.cumulative_yield,
            snapshot.timestamp
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
