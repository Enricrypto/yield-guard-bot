"""
Portfolio Service Layer
Handles CRUD operations for PortfolioHistory
"""

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models import PortfolioHistory


class PortfolioService:
    """Service for managing portfolio history"""

    @staticmethod
    def create_portfolio_record(
        db: Session,
        simulation_id: int,
        date: datetime,
        total_value: float,
        cash_balance: float,
        invested_value: float,
        daily_return: Optional[float] = None,
        daily_return_amount: Optional[float] = None,
        cumulative_return: Optional[float] = None,
        drawdown: Optional[float] = None,
        volatility: Optional[float] = None,
        protocol_allocations: Optional[Dict] = None,
        asset_allocations: Optional[Dict] = None,
        daily_yield: Optional[float] = None,
        cumulative_yield: Optional[float] = None,
        rebalanced: int = 0,
        notes: Optional[Dict] = None
    ) -> PortfolioHistory:
        """Create a new portfolio history record"""
        record = PortfolioHistory(
            simulation_id=simulation_id,
            date=date,
            total_value=total_value,
            cash_balance=cash_balance,
            invested_value=invested_value,
            daily_return=daily_return,
            daily_return_amount=daily_return_amount,
            cumulative_return=cumulative_return,
            drawdown=drawdown,
            volatility=volatility,
            protocol_allocations=protocol_allocations,
            asset_allocations=asset_allocations,
            daily_yield=daily_yield,
            cumulative_yield=cumulative_yield,
            rebalanced=rebalanced,
            notes=notes
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_portfolio_history(
        db: Session,
        simulation_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PortfolioHistory]:
        """Get portfolio history for a simulation"""
        query = db.query(PortfolioHistory).filter(
            PortfolioHistory.simulation_id == simulation_id
        )

        if start_date:
            query = query.filter(PortfolioHistory.date >= start_date)
        if end_date:
            query = query.filter(PortfolioHistory.date <= end_date)

        return query.order_by(PortfolioHistory.date.asc()).all()

    @staticmethod
    def get_portfolio_record_by_date(
        db: Session,
        simulation_id: int,
        date: datetime
    ) -> Optional[PortfolioHistory]:
        """Get portfolio record for a specific date"""
        return db.query(PortfolioHistory).filter(
            PortfolioHistory.simulation_id == simulation_id,
            PortfolioHistory.date == date
        ).first()

    @staticmethod
    def get_latest_portfolio_record(
        db: Session,
        simulation_id: int
    ) -> Optional[PortfolioHistory]:
        """Get the most recent portfolio record"""
        return db.query(PortfolioHistory).filter(
            PortfolioHistory.simulation_id == simulation_id
        ).order_by(PortfolioHistory.date.desc()).first()

    @staticmethod
    def update_portfolio_record(
        db: Session,
        record_id: int,
        **kwargs
    ) -> Optional[PortfolioHistory]:
        """Update a portfolio record"""
        record = db.query(PortfolioHistory).filter(PortfolioHistory.id == record_id).first()
        if not record:
            return None

        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_portfolio_history(db: Session, simulation_id: int) -> bool:
        """Delete all portfolio history for a simulation"""
        records = db.query(PortfolioHistory).filter(
            PortfolioHistory.simulation_id == simulation_id
        ).all()

        if not records:
            return False

        for record in records:
            db.delete(record)

        db.commit()
        return True

    @staticmethod
    def get_portfolio_stats(db: Session, simulation_id: int) -> Dict:
        """Get aggregate statistics for portfolio history"""
        records = PortfolioService.get_portfolio_history(db, simulation_id)

        if not records:
            return {}

        total_values = [r.total_value for r in records]
        daily_returns = [r.daily_return for r in records if r.daily_return is not None]

        stats = {
            "record_count": len(records),
            "start_date": records[0].date,
            "end_date": records[-1].date,
            "initial_value": records[0].total_value,
            "final_value": records[-1].total_value,
            "max_value": max(total_values),
            "min_value": min(total_values),
            "avg_daily_return": sum(daily_returns) / len(daily_returns) if daily_returns else 0,
            "rebalance_count": sum(1 for r in records if r.rebalanced == 1)  # type: ignore[arg-type]
        }

        return stats

    @staticmethod
    def get_rebalance_dates(db: Session, simulation_id: int) -> List[datetime]:
        """Get all dates when portfolio was rebalanced"""
        records = db.query(PortfolioHistory).filter(
            PortfolioHistory.simulation_id == simulation_id,
            PortfolioHistory.rebalanced == 1
        ).order_by(PortfolioHistory.date.asc()).all()

        return [record.date for record in records]  # type: ignore[return-value]

    @staticmethod
    def bulk_create_portfolio_records(
        db: Session,
        records: List[PortfolioHistory]
    ) -> bool:
        """Bulk insert portfolio records for performance"""
        try:
            db.bulk_save_objects(records)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
