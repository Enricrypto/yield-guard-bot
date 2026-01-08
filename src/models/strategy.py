from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from .base import Base


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)

    # Strategy Parameters
    risk_level = Column(String, nullable=False)  # 'low', 'medium', 'high'
    allocation_percentage = Column(Float, nullable=False)  # % of portfolio
    rebalance_threshold = Column(Float, default=5.0)  # % deviation before rebalance

    # Protocol Configuration
    protocols = Column(JSON, nullable=False)  # List of DeFi protocols to use
    asset_preferences = Column(JSON, nullable=True)  # Preferred assets/tokens

    # Risk Management
    max_drawdown = Column(Float, default=20.0)  # Maximum acceptable loss %
    stop_loss_threshold = Column(Float, nullable=True)  # Auto-exit threshold

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive

    def __repr__(self):
        return f"<StrategyConfig(name={self.name}, risk_level={self.risk_level})>"
