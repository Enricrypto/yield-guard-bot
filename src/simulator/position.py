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

    # Share Price Index (Yearn-style accounting)
    # Represents value of 1 share over time
    # Initial deposit gets shares at index 1.0
    # Index increases with yield accrual
    share_price_index: Decimal = Decimal('1.0')
    initial_shares: Decimal = Decimal('0')  # Number of shares minted at deposit
    days_since_last_harvest: int = 0  # Track time until next harvest
    pending_yield: Decimal = Decimal('0')  # Unrealized yield before harvest

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

        # Initialize shares: at index 1.0, collateral_amount = shares
        # This mimics depositing into a vault at share price = 1.0
        if self.initial_shares == Decimal('0') and self.collateral_amount > 0:
            self.initial_shares = self.collateral_amount / self.share_price_index

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

    def accrue_yield(self, days: Decimal = Decimal('1')) -> Decimal:
        """
        Accrue yield to pending (unrealized) before harvest
        This mimics how real vaults accumulate yield between harvests

        Args:
            days: Number of days to accrue

        Returns:
            Net yield accrued (supply - borrow interest)
        """
        # Convert annual rate to daily rate
        daily_supply_rate = self.supply_apy / Decimal('365')
        daily_borrow_rate = self.borrow_apy / Decimal('365')

        # Calculate yield based on current share value
        current_value = self.initial_shares * self.share_price_index
        interest_earned = current_value * daily_supply_rate * days
        interest_paid = self.debt_amount * daily_borrow_rate * days

        # Net yield accrued
        net_yield = interest_earned - interest_paid

        # Add to pending (unrealized) yield
        self.pending_yield += net_yield

        # Track days since last harvest
        self.days_since_last_harvest += int(days)

        # Update timestamp
        self.last_updated = datetime.now()

        return net_yield

    def harvest(self) -> Decimal:
        """
        Harvest pending yield - crystallizes unrealized gains into index
        This is a discrete event that happens every N days (like real protocols)

        Returns:
            Amount of yield harvested
        """
        if self.pending_yield <= 0:
            return Decimal('0')

        # Current total value (shares * index)
        current_value = self.initial_shares * self.share_price_index

        # New value after harvest
        new_value = current_value + self.pending_yield

        # Update share price index
        # index_new = (old_value + yield) / shares
        self.share_price_index = new_value / self.initial_shares

        # Track total interest
        if self.pending_yield > 0:
            self.total_interest_earned += self.pending_yield
        else:
            self.total_interest_paid += abs(self.pending_yield)

        # Reset pending yield and harvest counter
        harvested_amount = self.pending_yield
        self.pending_yield = Decimal('0')
        self.days_since_last_harvest = 0

        # Update collateral amount to match new index * shares
        self.collateral_amount = self.initial_shares * self.share_price_index

        self.last_updated = datetime.now()

        return harvested_amount

    def accrue_interest(self, days: Decimal = Decimal('1')) -> tuple[Decimal, Decimal]:
        """
        DEPRECATED: Use accrue_yield() + harvest() for index-based accounting
        Kept for backward compatibility

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

    def update_risk_parameters(self, ltv: Optional[Decimal] = None, liquidation_threshold: Optional[Decimal] = None):
        """
        Update risk parameters (LTV and/or liquidation threshold)
        This reflects protocol governance changes over time

        Args:
            ltv: New LTV ratio (optional)
            liquidation_threshold: New liquidation threshold (optional)
        """
        if ltv is not None:
            self.ltv = ltv
        if liquidation_threshold is not None:
            self.liquidation_threshold = liquidation_threshold
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

    @property
    def realized_yield(self) -> Decimal:
        """
        Get realized yield (harvested gains reflected in index)
        Realized Yield = (current_index - 1.0) * initial_shares
        """
        return (self.share_price_index - Decimal('1.0')) * self.initial_shares

    @property
    def unrealized_yield(self) -> Decimal:
        """
        Get unrealized yield (pending harvest)
        """
        return self.pending_yield

    @property
    def total_yield(self) -> Decimal:
        """
        Get total yield (realized + unrealized)
        """
        return self.realized_yield + self.unrealized_yield

    def get_index_return(self) -> Decimal:
        """
        Get return based on share price index
        This is the true TWR (Time-Weighted Return)

        Returns:
            Decimal return as fraction (0.05 = 5%)
        """
        return self.share_price_index - Decimal('1.0')

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
            # Index-based fields
            'share_price_index': float(self.share_price_index),
            'initial_shares': float(self.initial_shares),
            'realized_yield': float(self.realized_yield),
            'unrealized_yield': float(self.unrealized_yield),
            'total_yield': float(self.total_yield),
            'index_return': float(self.get_index_return()),
            'days_since_last_harvest': self.days_since_last_harvest,
            # Timestamps
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
