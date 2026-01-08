"""
Position dataclass
Represents a single position in a DeFi protocol
Tracks collateral, debt, and protocol-specific parameters
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    """
    Represents a position in a DeFi protocol

    Tracks:
    - Collateral deposited
    - Debt borrowed
    - Protocol and asset information
    - Risk parameters
    """

    # Identity
    protocol: str  # 'aave-v3', 'morpho', etc.
    asset_symbol: str  # 'USDC', 'WETH', etc.

    # Amounts
    collateral_amount: Decimal  # Amount deposited as collateral
    debt_amount: Decimal = Decimal('0')  # Amount borrowed

    # Risk Parameters (from protocol)
    ltv: Decimal = Decimal('0.80')  # Loan-to-Value ratio (80%)
    liquidation_threshold: Decimal = Decimal('0.85')  # Liquidation threshold (85%)

    # Rates (annual, as decimal: 0.05 = 5%)
    supply_apy: Decimal = Decimal('0.05')  # Interest earned on collateral
    borrow_apy: Decimal = Decimal('0.07')  # Interest paid on debt

    # Metadata
    opened_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Tracking
    total_interest_earned: Decimal = Decimal('0')
    total_interest_paid: Decimal = Decimal('0')

    def __post_init__(self):
        """Validate position after initialization"""
        if self.collateral_amount < 0:
            raise ValueError("Collateral amount cannot be negative")
        if self.debt_amount < 0:
            raise ValueError("Debt amount cannot be negative")
        if self.ltv < 0 or self.ltv > 1:
            raise ValueError("LTV must be between 0 and 1")
        if self.liquidation_threshold < 0 or self.liquidation_threshold > 1:
            raise ValueError("Liquidation threshold must be between 0 and 1")

    @property
    def health_factor(self) -> Decimal:
        """
        Calculate health factor for this position
        HF = (Collateral * Liquidation Threshold) / Debt

        HF > 1: Position is healthy
        HF < 1: Position can be liquidated
        HF = infinity: No debt (perfectly safe)

        Returns:
            Health factor as Decimal
        """
        if self.debt_amount == 0:
            return Decimal('Infinity')

        return (self.collateral_amount * self.liquidation_threshold) / self.debt_amount

    @property
    def current_ltv(self) -> Decimal:
        """
        Calculate current LTV (loan-to-value) ratio
        Current LTV = Debt / Collateral

        Returns:
            Current LTV as decimal (0.5 = 50%)
        """
        if self.collateral_amount == 0:
            return Decimal('0')

        return self.debt_amount / self.collateral_amount

    @property
    def max_borrowable(self) -> Decimal:
        """
        Calculate maximum amount that can be borrowed
        Max Borrow = Collateral * LTV

        Returns:
            Maximum borrowable amount
        """
        return self.collateral_amount * self.ltv

    @property
    def available_to_borrow(self) -> Decimal:
        """
        Calculate how much more can be borrowed

        Returns:
            Available borrowing capacity
        """
        return max(Decimal('0'), self.max_borrowable - self.debt_amount)

    @property
    def liquidation_price_drop(self) -> Optional[Decimal]:
        """
        Calculate how much the collateral price can drop before liquidation

        Returns:
            Percentage drop that triggers liquidation, or None if no debt
        """
        if self.debt_amount == 0:
            return None

        # Price can drop until: Collateral * (1 - drop) * LiqThreshold = Debt
        # Solving: drop = 1 - (Debt / (Collateral * LiqThreshold))
        liquidation_value = self.debt_amount / self.liquidation_threshold

        if liquidation_value >= self.collateral_amount:
            return Decimal('0')  # Already at or below liquidation

        drop_percentage = Decimal('1') - (liquidation_value / self.collateral_amount)
        return drop_percentage

    def accrue_interest(self, days: Decimal = Decimal('1')) -> tuple[Decimal, Decimal]:
        """
        Accrue interest for a period of time

        Args:
            days: Number of days to accrue interest

        Returns:
            Tuple of (interest_earned, interest_paid)
        """
        # Convert annual rate to daily rate
        daily_supply_rate = self.supply_apy / Decimal('365')
        daily_borrow_rate = self.borrow_apy / Decimal('365')

        # Calculate interest for the period
        interest_earned = self.collateral_amount * daily_supply_rate * days
        interest_paid = self.debt_amount * daily_borrow_rate * days

        # Update amounts
        self.collateral_amount += interest_earned
        self.debt_amount += interest_paid

        # Track totals
        self.total_interest_earned += interest_earned
        self.total_interest_paid += interest_paid

        # Update timestamp
        self.last_updated = datetime.now()

        return (interest_earned, interest_paid)

    def deposit(self, amount: Decimal):
        """
        Deposit additional collateral

        Args:
            amount: Amount to deposit
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        self.collateral_amount += amount
        self.last_updated = datetime.now()

    def withdraw(self, amount: Decimal):
        """
        Withdraw collateral (if health factor allows)

        Args:
            amount: Amount to withdraw

        Raises:
            ValueError: If withdrawal would cause unhealthy position
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if amount > self.collateral_amount:
            raise ValueError("Cannot withdraw more than collateral amount")

        # Check if withdrawal would make position unhealthy
        new_collateral = self.collateral_amount - amount
        if self.debt_amount > 0:
            new_hf = (new_collateral * self.liquidation_threshold) / self.debt_amount
            if new_hf < Decimal('1.0'):
                raise ValueError(f"Withdrawal would result in unhealthy position (HF={new_hf:.2f})")

        self.collateral_amount = new_collateral
        self.last_updated = datetime.now()

    def borrow(self, amount: Decimal):
        """
        Borrow against collateral

        Args:
            amount: Amount to borrow

        Raises:
            ValueError: If borrow exceeds available capacity
        """
        if amount <= 0:
            raise ValueError("Borrow amount must be positive")

        if amount > self.available_to_borrow:
            raise ValueError(f"Cannot borrow {amount}. Available: {self.available_to_borrow}")

        self.debt_amount += amount
        self.last_updated = datetime.now()

    def repay(self, amount: Decimal):
        """
        Repay debt

        Args:
            amount: Amount to repay
        """
        if amount <= 0:
            raise ValueError("Repay amount must be positive")

        if amount > self.debt_amount:
            # Allow overpayment, just repay everything
            amount = self.debt_amount

        self.debt_amount -= amount
        self.last_updated = datetime.now()

    def update_rates(self, supply_apy: Decimal, borrow_apy: Decimal):
        """
        Update interest rates

        Args:
            supply_apy: New supply APY
            borrow_apy: New borrow APY
        """
        self.supply_apy = supply_apy
        self.borrow_apy = borrow_apy
        self.last_updated = datetime.now()

    def get_net_apy(self) -> Decimal:
        """
        Calculate net APY considering both supply and borrow
        Net APY = Supply APY - (Debt/Collateral) * Borrow APY

        Returns:
            Net APY as decimal
        """
        if self.collateral_amount == 0:
            return Decimal('0')

        leverage = self.debt_amount / self.collateral_amount
        net_apy = self.supply_apy - (leverage * self.borrow_apy)

        return net_apy

    def to_dict(self) -> dict:
        """Convert position to dictionary for serialization"""
        return {
            'protocol': self.protocol,
            'asset_symbol': self.asset_symbol,
            'collateral_amount': float(self.collateral_amount),
            'debt_amount': float(self.debt_amount),
            'ltv': float(self.ltv),
            'liquidation_threshold': float(self.liquidation_threshold),
            'supply_apy': float(self.supply_apy),
            'borrow_apy': float(self.borrow_apy),
            'health_factor': float(self.health_factor) if self.health_factor != Decimal('Infinity') else None,
            'current_ltv': float(self.current_ltv),
            'net_apy': float(self.get_net_apy()),
            'total_interest_earned': float(self.total_interest_earned),
            'total_interest_paid': float(self.total_interest_paid),
            'opened_at': self.opened_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
        }

    def __repr__(self):
        hf_str = f"{self.health_factor:.2f}" if self.health_factor != Decimal('Infinity') else "∞"
        return (f"<Position {self.protocol}/{self.asset_symbol}: "
                f"Collateral=${self.collateral_amount:,.0f}, "
                f"Debt=${self.debt_amount:,.0f}, HF={hf_str}>")


if __name__ == "__main__":
    # Example usage
    print("Creating a position...")

    position = Position(
        protocol='aave-v3',
        asset_symbol='USDC',
        collateral_amount=Decimal('100000'),  # $100k
        ltv=Decimal('0.80'),
        liquidation_threshold=Decimal('0.85'),
        supply_apy=Decimal('0.05'),  # 5%
        borrow_apy=Decimal('0.07')  # 7%
    )

    print(f"\n{position}")
    print(f"Health Factor: {position.health_factor}")
    print(f"Max Borrowable: ${position.max_borrowable:,.2f}")
    print(f"Net APY: {position.get_net_apy() * 100:.2f}%")

    # Borrow
    print("\nBorrowing $50,000...")
    position.borrow(Decimal('50000'))
    print(f"{position}")
    print(f"Current LTV: {position.current_ltv * 100:.1f}%")
    print(f"Net APY: {position.get_net_apy() * 100:.2f}%")

    # Accrue interest for 30 days
    print("\nAccruing interest for 30 days...")
    earned, paid = position.accrue_interest(days=Decimal('30'))
    print(f"Interest earned: ${earned:,.2f}")
    print(f"Interest paid: ${paid:,.2f}")
    print(f"Net interest: ${earned - paid:,.2f}")
    print(f"\n{position}")
