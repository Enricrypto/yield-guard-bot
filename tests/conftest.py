# tests/conftest.py
from src.database.db import SimulationRun, PortfolioSnapshot, DatabaseManager
from datetime import datetime
from decimal import Decimal
import pytest

 # adjust based on your db session helper

@pytest.fixture
def db_manager():
    manager = DatabaseManager(db_path=":memory:")  # Use in-memory DB for testing
    manager.init_db()
    return manager

@pytest.fixture
def sample_simulation():
    from src.database.db import SimulationRun
    return SimulationRun(
        strategy_name="Test Strategy",
        initial_capital=1000,
        simulation_days=10,
        protocols_used="Aave,Compound",
        total_return=50,
        annualized_return=200,
        max_drawdown=5,
        sharpe_ratio=1.2,
        final_value=1050,
        created_at=datetime.now()
    )

@pytest.fixture
def sample_simulation_id(db_manager, sample_simulation):
    """Insert sample simulation into DB and return its ID."""
    sim_id = db_manager.save_simulation_run(sample_simulation)
    return sim_id

@pytest.fixture
def small_capital():
    """Return a Decimal small capital amount for treasury tests."""
    return Decimal('1000015')  # includes buffer for gas

@pytest.fixture
def medium_capital():
    return Decimal('333349')  # for moderate treasury tests

@pytest.fixture
def large_capital():
    return Decimal('1000015')  # for aggressive treasury tests
