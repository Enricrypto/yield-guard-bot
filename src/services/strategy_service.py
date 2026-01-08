"""
Strategy Service Layer
Handles CRUD operations for StrategyConfig
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.models import StrategyConfig


class StrategyService:
    """Service for managing strategy configurations"""

    @staticmethod
    def create_strategy(
        db: Session,
        name: str,
        risk_level: str,
        allocation_percentage: float,
        protocols: List[str],
        description: Optional[str] = None,
        rebalance_threshold: float = 5.0,
        asset_preferences: Optional[List[str]] = None,
        max_drawdown: float = 20.0,
        stop_loss_threshold: Optional[float] = None
    ) -> StrategyConfig:
        """Create a new strategy configuration"""
        strategy = StrategyConfig(
            name=name,
            description=description,
            risk_level=risk_level,
            allocation_percentage=allocation_percentage,
            rebalance_threshold=rebalance_threshold,
            protocols=protocols,
            asset_preferences=asset_preferences,
            max_drawdown=max_drawdown,
            stop_loss_threshold=stop_loss_threshold
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def get_strategy_by_id(db: Session, strategy_id: int) -> Optional[StrategyConfig]:
        """Get strategy by ID"""
        return db.query(StrategyConfig).filter(StrategyConfig.id == strategy_id).first()

    @staticmethod
    def get_strategy_by_name(db: Session, name: str) -> Optional[StrategyConfig]:
        """Get strategy by name"""
        return db.query(StrategyConfig).filter(StrategyConfig.name == name).first()

    @staticmethod
    def get_all_strategies(db: Session, active_only: bool = True) -> List[StrategyConfig]:
        """Get all strategies"""
        query = db.query(StrategyConfig)
        if active_only:
            query = query.filter(StrategyConfig.is_active == 1)
        return query.all()

    @staticmethod
    def get_strategies_by_risk_level(db: Session, risk_level: str) -> List[StrategyConfig]:
        """Get strategies by risk level"""
        return db.query(StrategyConfig).filter(
            StrategyConfig.risk_level == risk_level,
            StrategyConfig.is_active == 1
        ).all()

    @staticmethod
    def update_strategy(
        db: Session,
        strategy_id: int,
        **kwargs
    ) -> Optional[StrategyConfig]:
        """Update strategy configuration"""
        strategy = StrategyService.get_strategy_by_id(db, strategy_id)
        if not strategy:
            return None

        for key, value in kwargs.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)

        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def deactivate_strategy(db: Session, strategy_id: int) -> bool:
        """Deactivate a strategy (soft delete)"""
        strategy = StrategyService.get_strategy_by_id(db, strategy_id)
        if not strategy:
            return False

        strategy.is_active = 0  # type: ignore[assignment]
        db.commit()
        return True

    @staticmethod
    def activate_strategy(db: Session, strategy_id: int) -> bool:
        """Activate a strategy"""
        strategy = StrategyService.get_strategy_by_id(db, strategy_id)
        if not strategy:
            return False

        strategy.is_active = 1  # type: ignore[assignment]
        db.commit()
        return True

    @staticmethod
    def delete_strategy(db: Session, strategy_id: int) -> bool:
        """Permanently delete a strategy"""
        strategy = StrategyService.get_strategy_by_id(db, strategy_id)
        if not strategy:
            return False

        db.delete(strategy)
        db.commit()
        return True
