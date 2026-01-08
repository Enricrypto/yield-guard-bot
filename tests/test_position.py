"""
Unit tests for Position class
Tests deposit, borrowing, interest accrual, and health factor calculations
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.simulator.position import Position


class TestPositionBasics:
    """Test basic position functionality"""

    def test_create_position(self):
        """Test creating a new position"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.80'),
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        assert position.protocol == 'aave-v3'
        assert position.asset_symbol == 'USDC'
        assert position.collateral_amount == Decimal('10000')
        assert position.debt_amount == Decimal('0')
        assert position.ltv == Decimal('0.80')
        assert position.liquidation_threshold == Decimal('0.85')

    def test_position_no_borrow(self):
        """Test position without borrowing (conservative strategy)"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0'),  # No borrowing
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        assert position.debt_amount == Decimal('0')
        assert position.current_ltv == Decimal('0')
        assert position.health_factor == Decimal('Infinity')

    def test_position_with_borrow(self):
        """Test position with borrowing"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.70'),  # Borrow 70%
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # Should automatically borrow 70% of collateral
        assert position.debt_amount == Decimal('7000')
        assert position.current_ltv == Decimal('0.70')

        # Health factor = (collateral * liq_threshold) / debt
        # HF = (10000 * 0.85) / 7000 = 1.214...
        assert position.health_factor > Decimal('1.2')
        assert position.health_factor < Decimal('1.3')


class TestHealthFactor:
    """Test health factor calculations"""

    def test_health_factor_no_debt(self):
        """Test health factor with no debt"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0'),
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        assert position.health_factor == Decimal('Infinity')

    def test_health_factor_safe(self):
        """Test safe health factor (HF > 1.5)"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.50'),  # Conservative 50% LTV
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # HF = (10000 * 0.85) / 5000 = 1.7
        assert position.health_factor == Decimal('1.7')
        # Safe - health factor well above 1.0
        assert position.health_factor > Decimal('1.5')

    def test_health_factor_at_risk(self):
        """Test health factor at liquidation risk (HF < 1.1)"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.80'),  # Aggressive 80% LTV
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # HF = (10000 * 0.85) / 8000 = 1.0625
        assert position.health_factor < Decimal('1.1')
        # At risk - health factor close to liquidation threshold
        assert position.health_factor < Decimal('1.2')


class TestInterestAccrual:
    """Test interest accrual over time"""

    def test_accrue_interest_no_borrow(self):
        """Test interest accrual for lending-only position"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0'),  # No borrowing
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),  # 5% APY
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # Accrue interest for 1 day
        earned, paid = position.accrue_interest(days=Decimal('1'))

        # Daily rate = 5% / 365 = 0.0137%
        # Earnings = 10000 * 0.05 / 365 ≈ 1.37
        assert earned > Decimal('1.3')
        assert earned < Decimal('1.4')
        assert paid == Decimal('0')

        # Check collateral increased
        assert position.collateral_amount > Decimal('10000')

    def test_accrue_interest_with_borrow(self):
        """Test interest accrual for leveraged position"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.70'),  # Borrow 7000
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),  # 5% APY
            borrow_apy=Decimal('0.07'),  # 7% APY
            opened_at=datetime.now()
        )

        initial_debt = position.debt_amount

        # Accrue interest for 1 day
        earned, paid = position.accrue_interest(days=Decimal('1'))

        # Supply earnings = 10000 * 0.05 / 365 ≈ 1.37
        assert earned > Decimal('1.3')
        assert earned < Decimal('1.4')

        # Borrow costs = 7000 * 0.07 / 365 ≈ 1.34
        assert paid > Decimal('1.3')
        assert paid < Decimal('1.4')

        # Net = earned - paid ≈ 0.03
        net = earned - paid
        assert net > Decimal('0')
        assert net < Decimal('0.1')

        # Debt should increase
        assert position.debt_amount > initial_debt

    def test_accrue_interest_multiple_days(self):
        """Test interest accrual over multiple days"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0'),
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # Accrue interest for 30 days
        earned, paid = position.accrue_interest(days=Decimal('30'))

        # Expected earnings = 10000 * 0.05 * (30/365) ≈ 41.10
        assert earned > Decimal('40')
        assert earned < Decimal('42')

        # Collateral should be ~10041
        assert position.collateral_amount > Decimal('10040')
        assert position.collateral_amount < Decimal('10042')


class TestRateUpdates:
    """Test updating interest rates"""

    def test_update_rates(self):
        """Test updating supply and borrow rates"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.50'),
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # Update rates
        position.update_rates(
            supply_apy=Decimal('0.06'),  # Increased to 6%
            borrow_apy=Decimal('0.08')   # Increased to 8%
        )

        assert position.supply_apy == Decimal('0.06')
        assert position.borrow_apy == Decimal('0.08')


class TestBorrowing:
    """Test borrowing functionality"""

    def test_borrow(self):
        """Test borrowing against collateral"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0'),  # Start with no borrowing
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        assert position.debt_amount == Decimal('0')

        # Borrow 5000
        position.borrow(Decimal('5000'))

        assert position.debt_amount == Decimal('5000')
        assert position.current_ltv == Decimal('0.50')

        # Health factor = (10000 * 0.85) / 5000 = 1.7
        assert position.health_factor == Decimal('1.7')

    def test_borrow_exceeds_ltv(self):
        """Test borrowing more than allowed by LTV"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.80'),  # Max LTV 80%
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # Already borrowed 8000 (80%)
        assert position.debt_amount == Decimal('8000')

        # Try to borrow more - should raise error
        with pytest.raises(ValueError, match="exceeds maximum LTV"):
            position.borrow(Decimal('1000'))

    def test_repay(self):
        """Test repaying debt"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.60'),
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        assert position.debt_amount == Decimal('6000')

        # Repay 2000
        position.repay(Decimal('2000'))

        assert position.debt_amount == Decimal('4000')
        assert position.current_ltv == Decimal('0.40')

        # Health factor improved
        assert position.health_factor > Decimal('2')

    def test_repay_too_much(self):
        """Test repaying more than debt"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.50'),
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        # Try to repay more than debt
        with pytest.raises(ValueError, match="exceeds debt"):
            position.repay(Decimal('10000'))


class TestPositionSerialization:
    """Test position to_dict conversion"""

    def test_to_dict(self):
        """Test converting position to dictionary"""
        position = Position(
            protocol='aave-v3',
            asset_symbol='USDC',
            collateral_amount=Decimal('10000'),
            ltv=Decimal('0.70'),
            liquidation_threshold=Decimal('0.85'),
            supply_apy=Decimal('0.05'),
            borrow_apy=Decimal('0.07'),
            opened_at=datetime.now()
        )

        data = position.to_dict()

        assert data['protocol'] == 'aave-v3'
        assert data['asset_symbol'] == 'USDC'
        assert data['collateral_amount'] == 10000.0
        assert data['debt_amount'] == 7000.0
        assert data['supply_apy'] == 5.0  # Converted to percentage
        assert data['borrow_apy'] == 7.0
        assert data['current_ltv'] == 70.0
        assert 'health_factor' in data
        assert 'opened_at' in data


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
