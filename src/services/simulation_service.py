"""
Simulation Service Layer
Handles CRUD operations for SimulationRun
"""

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from src.models import SimulationRun


class SimulationService:
    """Service for managing simulation runs"""

    @staticmethod
    def create_simulation(
        db: Session,
        strategy_id: int,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float
    ) -> SimulationRun:
        """Create a new simulation run"""
        simulation = SimulationRun(
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            status="pending"
        )
        db.add(simulation)
        db.commit()
        db.refresh(simulation)
        return simulation

    @staticmethod
    def get_simulation_by_id(db: Session, simulation_id: int) -> Optional[SimulationRun]:
        """Get simulation by ID"""
        return db.query(SimulationRun).filter(SimulationRun.id == simulation_id).first()

    @staticmethod
    def get_simulations_by_strategy(
        db: Session,
        strategy_id: int,
        status: Optional[str] = None
    ) -> List[SimulationRun]:
        """Get all simulations for a strategy"""
        query = db.query(SimulationRun).filter(SimulationRun.strategy_id == strategy_id)
        if status:
            query = query.filter(SimulationRun.status == status)
        return query.order_by(SimulationRun.created_at.desc()).all()

    @staticmethod
    def get_all_simulations(db: Session, status: Optional[str] = None) -> List[SimulationRun]:
        """Get all simulations"""
        query = db.query(SimulationRun)
        if status:
            query = query.filter(SimulationRun.status == status)
        return query.order_by(SimulationRun.created_at.desc()).all()

    @staticmethod
    def update_simulation_status(
        db: Session,
        simulation_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[SimulationRun]:
        """Update simulation status"""
        simulation = SimulationService.get_simulation_by_id(db, simulation_id)
        if not simulation:
            return None

        simulation.status = status  # type: ignore[assignment]
        if error_message:
            simulation.error_message = error_message  # type: ignore[assignment]
        if status == "completed":
            simulation.completed_at = datetime.utcnow()  # type: ignore[assignment]

        db.commit()
        db.refresh(simulation)
        return simulation

    @staticmethod
    def update_simulation_results(
        db: Session,
        simulation_id: int,
        final_value: float,
        total_return: float,
        total_return_amount: float,
        max_drawdown: float,
        sharpe_ratio: Optional[float] = None,
        volatility: Optional[float] = None,
        win_rate: Optional[float] = None,
        avg_daily_return: Optional[float] = None,
        best_day: Optional[float] = None,
        worst_day: Optional[float] = None,
        execution_time: Optional[float] = None,
        metrics: Optional[Dict] = None
    ) -> Optional[SimulationRun]:
        """Update simulation with results"""
        simulation = SimulationService.get_simulation_by_id(db, simulation_id)
        if not simulation:
            return None

        simulation.final_value = final_value  # type: ignore[assignment]
        simulation.total_return = total_return  # type: ignore[assignment]
        simulation.total_return_amount = total_return_amount  # type: ignore[assignment]
        simulation.max_drawdown = max_drawdown  # type: ignore[assignment]
        simulation.sharpe_ratio = sharpe_ratio  # type: ignore[assignment]
        simulation.volatility = volatility  # type: ignore[assignment]
        simulation.win_rate = win_rate  # type: ignore[assignment]
        simulation.avg_daily_return = avg_daily_return  # type: ignore[assignment]
        simulation.best_day = best_day  # type: ignore[assignment]
        simulation.worst_day = worst_day  # type: ignore[assignment]
        simulation.execution_time = execution_time  # type: ignore[assignment]
        simulation.metrics = metrics  # type: ignore[assignment]
        simulation.status = "completed"  # type: ignore[assignment]
        simulation.completed_at = datetime.utcnow()  # type: ignore[assignment]

        db.commit()
        db.refresh(simulation)
        return simulation

    @staticmethod
    def delete_simulation(db: Session, simulation_id: int) -> bool:
        """Delete a simulation"""
        simulation = SimulationService.get_simulation_by_id(db, simulation_id)
        if not simulation:
            return False

        db.delete(simulation)
        db.commit()
        return True

    @staticmethod
    def get_best_simulation_for_strategy(
        db: Session,
        strategy_id: int
    ) -> Optional[SimulationRun]:
        """Get the best performing simulation for a strategy"""
        return db.query(SimulationRun).filter(
            SimulationRun.strategy_id == strategy_id,
            SimulationRun.status == "completed"
        ).order_by(SimulationRun.total_return.desc()).first()
