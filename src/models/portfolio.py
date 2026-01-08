from sqlalchemy import Column, Integer, Float, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)

    # Date tracking
    date = Column(DateTime, nullable=False, index=True)

    # Portfolio Values
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)

    # Daily Performance
    daily_return = Column(Float, nullable=True)  # %
    daily_return_amount = Column(Float, nullable=True)  # $ amount
    cumulative_return = Column(Float, nullable=True)  # % from start

    # Risk Metrics
    drawdown = Column(Float, nullable=True)  # % from peak
    volatility = Column(Float, nullable=True)  # Rolling volatility

    # Protocol Breakdown
    protocol_allocations = Column(JSON, nullable=True)  # {protocol: value}
    asset_allocations = Column(JSON, nullable=True)  # {asset: value}

    # Yield/Returns
    daily_yield = Column(Float, nullable=True)  # Yield earned today
    cumulative_yield = Column(Float, nullable=True)  # Total yield earned

    # Events
    rebalanced = Column(Integer, default=0)  # 1 if rebalanced this day
    notes = Column(JSON, nullable=True)  # Any special events or notes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Ensure one record per simulation per day
    __table_args__ = (
        UniqueConstraint('simulation_id', 'date', name='unique_simulation_date'),
    )

    def __repr__(self):
        return f"<PortfolioHistory(simulation_id={self.simulation_id}, date={self.date}, total_value={self.total_value})>"
