from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategy_configs.id"), nullable=False)

    # Simulation Parameters
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)

    # Results
    final_value = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)  # %
    total_return_amount = Column(Float, nullable=True)  # $ amount
    max_drawdown = Column(Float, nullable=True)  # %
    sharpe_ratio = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)  # Standard deviation

    # Performance Metrics
    win_rate = Column(Float, nullable=True)  # % of profitable periods
    avg_daily_return = Column(Float, nullable=True)
    best_day = Column(Float, nullable=True)
    worst_day = Column(Float, nullable=True)

    # Execution Details
    status = Column(String, default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # seconds

    # Additional Data
    metrics = Column(JSON, nullable=True)  # Store additional metrics

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SimulationRun(id={self.id}, strategy_id={self.strategy_id}, status={self.status})>"
