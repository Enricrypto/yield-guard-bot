"""
Treasury Simulator
Core simulation engine for portfolio management across DeFi protocols
Simulates deposits, borrowing, interest accrual, and portfolio rebalancing
"""

from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import copy

from .position import Position


@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time"""
    timestamp: datetime

    # Portfolio values
    total_collateral: Decimal
    total_debt: Decimal
    net_value: Decimal  # Collateral - Debt

    # Risk metrics
    overall_health_factor: Decimal
    weighted_ltv: Decimal

    # Performance
    daily_yield: Decimal
    cumulative_yield: Decimal
    daily_return_pct: Decimal

    # Positions
    num_positions: int
    positions: List[Dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert snapshot to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_collateral': float(self.total_collateral),
            'total_debt': float(self.total_debt),
            'net_value': float(self.net_value),
            'overall_health_factor': float(self.overall_health_factor) if self.overall_health_factor != Decimal('Infinity') else None,
            'weighted_ltv': float(self.weighted_ltv),
            'daily_yield': float(self.daily_yield),
            'cumulative_yield': float(self.cumulative_yield),
            'daily_return_pct': float(self.daily_return_pct),
            'num_positions': self.num_positions,
            'positions': self.positions
        }


class TreasurySimulator:
    """
    Simulates a treasury managing positions across multiple DeFi protocols

    Core functions:
    - deposit(): Add capital to protocols
    - get_total_collateral(): Sum all collateral
    - get_total_debt(): Sum all debt
    - calculate_health_factor(): Calculate overall HF
    - step(): Simulate one time period
    - run_simulation(): Run multi-day simulation
    """

    def __init__(
        self,
        initial_capital: Decimal,
        name: str = "Treasury",
        min_health_factor: Decimal = Decimal('1.5')
    ):
        """
        Initialize treasury simulator

        Args:
            initial_capital: Starting capital
            name: Treasury name
            min_health_factor: Minimum acceptable health factor
        """
        self.name = name
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        self.min_health_factor = min_health_factor

        # Positions
        self.positions: List[Position] = []

        # History tracking
        self.history: List[PortfolioSnapshot] = []
        self.cumulative_yield = Decimal('0')

        # Cost tracking
        self.total_gas_fees = Decimal('0')
        self.total_protocol_fees = Decimal('0')
        self.total_slippage = Decimal('0')
        self.num_transactions = 0

        # Metadata
        self.created_at = datetime.now()
        self.current_date = datetime.now()

    def _calculate_transaction_costs(
        self,
        transaction_type: str,
        amount: Decimal,
        protocol: str
    ) -> Dict[str, Decimal]:
        """
        Calculate realistic transaction costs for stablecoin operations

        Args:
            transaction_type: 'deposit', 'withdraw', 'borrow', 'repay', or 'rebalance'
            amount: Transaction amount in USD
            protocol: Protocol name

        Returns:
            Dictionary with gas_fee, protocol_fee, slippage, total_cost
        """
        # Gas fees (in USD) - Ethereum mainnet estimates for stablecoin operations
        # These are realistic 2025 estimates based on moderate gas prices
        gas_fees = {
            'deposit': Decimal('15.00'),      # ~$15 for ERC20 approve + deposit
            'withdraw': Decimal('12.00'),     # ~$12 for withdraw
            'borrow': Decimal('18.00'),       # ~$18 for borrow (more complex)
            'repay': Decimal('15.00'),        # ~$15 for ERC20 approve + repay
            'rebalance': Decimal('25.00')     # ~$25 for withdraw + deposit combo
        }

        # Protocol fees (percentage of amount)
        # Most lending protocols charge 0-0.1% for deposits/withdrawals
        protocol_fee_rates = {
            'aave-v3': Decimal('0.0009'),      # 0.09%
            'compound-v3': Decimal('0.0000'),  # 0% (Compound doesn't charge deposit fees)
            'morpho-v1': Decimal('0.0005')     # 0.05%
        }

        # Stablecoin slippage (very minimal for stablecoins)
        # Only applies to large transactions or during market stress
        # For lending markets, slippage is near zero
        slippage_rate = Decimal('0.0001')  # 0.01% - minimal for stablecoins

        gas_fee = gas_fees.get(transaction_type, Decimal('15.00'))
        protocol_fee_rate = protocol_fee_rates.get(protocol, Decimal('0.0005'))

        protocol_fee = amount * protocol_fee_rate
        slippage = amount * slippage_rate if amount > Decimal('10000') else Decimal('0')  # Only for large txs

        total_cost = gas_fee + protocol_fee + slippage

        return {
            'gas_fee': gas_fee,
            'protocol_fee': protocol_fee,
            'slippage': slippage,
            'total_cost': total_cost
        }

    def deposit(
        self,
        protocol: str,
        asset_symbol: str,
        amount: Decimal,
        supply_apy: Decimal,
        borrow_apy: Decimal,
        ltv: Decimal = Decimal('0.80'),
        liquidation_threshold: Decimal = Decimal('0.85')
    ) -> Position:
        """
        Deposit capital into a protocol

        Args:
            protocol: Protocol name
            asset_symbol: Asset to deposit
            amount: Amount to deposit
            supply_apy: Current supply APY
            borrow_apy: Current borrow APY
            ltv: Loan-to-value ratio
            liquidation_threshold: Liquidation threshold

        Returns:
            Created Position object

        Raises:
            ValueError: If insufficient capital
        """
        if amount > self.available_capital:
            raise ValueError(f"Insufficient capital. Available: {self.available_capital}, Requested: {amount}")

        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        # Calculate transaction costs
        costs = self._calculate_transaction_costs('deposit', amount, protocol)

        # Deduct costs from available capital
        self.available_capital -= costs['total_cost']
        self.total_gas_fees += costs['gas_fee']
        self.total_protocol_fees += costs['protocol_fee']
        self.total_slippage += costs['slippage']
        self.num_transactions += 1

        # Actual amount deposited after fees
        net_amount = amount - costs['protocol_fee'] - costs['slippage']

        # Create position
        position = Position(
            protocol=protocol,
            asset_symbol=asset_symbol,
            collateral_amount=net_amount,  # Deposit net amount after protocol fees & slippage
            ltv=ltv,
            liquidation_threshold=liquidation_threshold,
            supply_apy=supply_apy,
            borrow_apy=borrow_apy,
            opened_at=self.current_date
        )

        self.positions.append(position)
        self.available_capital -= amount  # Deduct principal

        return position

    def get_total_collateral(self) -> Decimal:
        """
        Sum all collateral across positions

        Returns:
            Total collateral amount
        """
        return sum((pos.collateral_amount for pos in self.positions), Decimal('0'))

    def get_total_debt(self) -> Decimal:
        """
        Sum all debt across positions

        Returns:
            Total debt amount
        """
        return sum((pos.debt_amount for pos in self.positions), Decimal('0'))

    def get_net_value(self) -> Decimal:
        """
        Calculate net portfolio value (Collateral - Debt + Available Capital)

        Returns:
            Net value
        """
        return self.get_total_collateral() - self.get_total_debt() + self.available_capital

    def calculate_health_factor(self) -> Decimal:
        """
        Calculate overall portfolio health factor
        HF = (Total Collateral * Weighted Avg Liq Threshold) / Total Debt

        Returns:
            Overall health factor
        """
        total_debt = self.get_total_debt()

        if total_debt == 0:
            return Decimal('Infinity')

        # Calculate weighted average liquidation threshold
        weighted_liq_threshold = Decimal('0')
        total_collateral = Decimal('0')

        for pos in self.positions:
            weighted_liq_threshold += pos.collateral_amount * pos.liquidation_threshold
            total_collateral += pos.collateral_amount

        if total_collateral == 0:
            return Decimal('Infinity')

        avg_liq_threshold = weighted_liq_threshold / total_collateral

        health_factor = (total_collateral * avg_liq_threshold) / total_debt

        return health_factor

    def get_weighted_ltv(self) -> Decimal:
        """
        Calculate weighted average LTV across all positions

        Returns:
            Weighted LTV
        """
        total_collateral = self.get_total_collateral()

        if total_collateral == 0:
            return Decimal('0')

        weighted_ltv = sum(
            pos.current_ltv * pos.collateral_amount
            for pos in self.positions
        ) / total_collateral

        return weighted_ltv

    def step(
        self,
        days: Decimal = Decimal('1'),
        market_data: Optional[Dict[str, Dict]] = None
    ) -> PortfolioSnapshot:
        """
        Simulate one time step

        Args:
            days: Number of days to simulate
            market_data: Optional market data for updating rates and risk parameters
                        Format: {protocol: {asset: {
                            'supply_apy': X,
                            'borrow_apy': Y,
                            'ltv': Z (optional),
                            'liquidation_threshold': W (optional)
                        }}}

        Returns:
            Portfolio snapshot after step
        """
        # Update rates and risk parameters if market data provided
        if market_data:
            for position in self.positions:
                protocol_data = market_data.get(position.protocol, {})
                asset_data = protocol_data.get(position.asset_symbol, {})

                # Update interest rates
                if 'supply_apy' in asset_data and 'borrow_apy' in asset_data:
                    position.update_rates(
                        supply_apy=asset_data['supply_apy'],
                        borrow_apy=asset_data['borrow_apy']
                    )

                # Update risk parameters if provided
                if 'ltv' in asset_data or 'liquidation_threshold' in asset_data:
                    position.update_risk_parameters(
                        ltv=asset_data.get('ltv'),
                        liquidation_threshold=asset_data.get('liquidation_threshold')
                    )

        # Accrue interest on all positions
        total_earned = Decimal('0')
        total_paid = Decimal('0')

        for position in self.positions:
            earned, paid = position.accrue_interest(days=days)
            total_earned += earned
            total_paid += paid

        daily_yield = total_earned - total_paid
        self.cumulative_yield += daily_yield

        # Calculate portfolio metrics
        total_collateral = self.get_total_collateral()
        total_debt = self.get_total_debt()
        net_value = self.get_net_value()
        health_factor = self.calculate_health_factor()
        weighted_ltv = self.get_weighted_ltv()

        # Calculate returns
        if len(self.history) > 0:
            prev_value = self.history[-1].net_value
            daily_return_pct = ((net_value - prev_value) / prev_value) if prev_value > 0 else Decimal('0')
        else:
            prev_value = self.initial_capital
            daily_return_pct = ((net_value - prev_value) / prev_value) if prev_value > 0 else Decimal('0')

        # Create snapshot
        snapshot = PortfolioSnapshot(
            timestamp=self.current_date,
            total_collateral=total_collateral,
            total_debt=total_debt,
            net_value=net_value,
            overall_health_factor=health_factor,
            weighted_ltv=weighted_ltv,
            daily_yield=daily_yield,
            cumulative_yield=self.cumulative_yield,
            daily_return_pct=daily_return_pct * Decimal('100'),  # Convert to percentage
            num_positions=len(self.positions),
            positions=[pos.to_dict() for pos in self.positions]
        )

        self.history.append(snapshot)

        # Advance time
        self.current_date += timedelta(days=float(days))

        return snapshot

    def run_simulation(
        self,
        days: int,
        market_data_generator=None,
        daily_callback=None
    ) -> List[PortfolioSnapshot]:
        """
        Run multi-day simulation

        Args:
            days: Number of days to simulate
            market_data_generator: Optional generator for market data
                                  Should return dict for each day
            daily_callback: Optional callback function called each day

        Returns:
            List of portfolio snapshots
        """
        snapshots = []

        for day in range(days):
            # Get market data for this day if generator provided
            market_data = None
            if market_data_generator:
                market_data = market_data_generator(day)

            # Simulate one day
            snapshot = self.step(days=Decimal('1'), market_data=market_data)
            snapshots.append(snapshot)

            # Call callback if provided
            if daily_callback:
                daily_callback(day, snapshot)

        return snapshots

    def rebalance(
        self,
        target_positions: List[Dict],
        close_existing: bool = False
    ):
        """
        Rebalance portfolio to target allocations

        Args:
            target_positions: List of target position specifications
            close_existing: Whether to close existing positions first
        """
        if close_existing:
            # Close all positions
            for position in self.positions:
                self.available_capital += position.collateral_amount - position.debt_amount

            self.positions.clear()

        # Open new positions based on targets
        for target in target_positions:
            self.deposit(
                protocol=target['protocol'],
                asset_symbol=target['asset_symbol'],
                amount=target['amount'],
                supply_apy=target.get('supply_apy', Decimal('0.05')),
                borrow_apy=target.get('borrow_apy', Decimal('0.07')),
                ltv=target.get('ltv', Decimal('0.80')),
                liquidation_threshold=target.get('liquidation_threshold', Decimal('0.85'))
            )

    def get_portfolio_summary(self) -> Dict:
        """
        Get comprehensive portfolio summary

        Returns:
            Dictionary with portfolio statistics
        """
        total_collateral = self.get_total_collateral()
        total_debt = self.get_total_debt()
        net_value = self.get_net_value()

        return {
            'name': self.name,
            'initial_capital': float(self.initial_capital),
            'available_capital': float(self.available_capital),
            'total_collateral': float(total_collateral),
            'total_debt': float(total_debt),
            'net_value': float(net_value),
            'health_factor': float(self.calculate_health_factor()) if self.calculate_health_factor() != Decimal('Infinity') else None,
            'weighted_ltv': float(self.get_weighted_ltv()),
            'cumulative_yield': float(self.cumulative_yield),
            'total_return_pct': float((net_value - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0,
            'num_positions': len(self.positions),
            'positions': [pos.to_dict() for pos in self.positions],
            'simulation_days': len(self.history),
            'created_at': self.created_at.isoformat(),
            'current_date': self.current_date.isoformat()
        }

    def __repr__(self):
        return (f"<TreasurySimulator '{self.name}': "
                f"Value=${self.get_net_value():,.0f}, "
                f"Positions={len(self.positions)}, "
                f"HF={self.calculate_health_factor():.2f}>")


if __name__ == "__main__":
    # Example usage
    print("Creating Treasury Simulator...")

    treasury = TreasurySimulator(
        initial_capital=Decimal('1000000'),  # $1M
        name="Test Treasury",
        min_health_factor=Decimal('1.5')
    )

    print(f"\n{treasury}")
    print(f"Initial capital: ${treasury.initial_capital:,.0f}")

    # Deposit into Aave
    print("\nDepositing $500k into Aave USDC...")
    pos1 = treasury.deposit(
        protocol='aave-v3',
        asset_symbol='USDC',
        amount=Decimal('500000'),
        supply_apy=Decimal('0.05'),
        borrow_apy=Decimal('0.07'),
        ltv=Decimal('0.80'),
        liquidation_threshold=Decimal('0.85')
    )
    print(f"Created: {pos1}")

    # Deposit into Morpho
    print("\nDepositing $300k into Morpho USDC...")
    pos2 = treasury.deposit(
        protocol='morpho',
        asset_symbol='USDC',
        amount=Decimal('300000'),
        supply_apy=Decimal('0.06'),  # Morpho has better rate
        borrow_apy=Decimal('0.075'),
        ltv=Decimal('0.80'),
        liquidation_threshold=Decimal('0.85')
    )
    print(f"Created: {pos2}")

    print(f"\n{treasury}")
    print(f"Total collateral: ${treasury.get_total_collateral():,.0f}")
    print(f"Available capital: ${treasury.available_capital:,.0f}")
    print(f"Health factor: {treasury.calculate_health_factor()}")

    # Simulate 30 days
    print("\nSimulating 30 days...")
    snapshots = treasury.run_simulation(days=30)

    final_snapshot = snapshots[-1]
    print(f"\nFinal state after 30 days:")
    print(f"  Net value: ${final_snapshot.net_value:,.2f}")
    print(f"  Cumulative yield: ${final_snapshot.cumulative_yield:,.2f}")
    print(f"  Total return: {(final_snapshot.net_value - treasury.initial_capital) / treasury.initial_capital * 100:.2f}%")
    print(f"  Health factor: {final_snapshot.overall_health_factor:.2f}")

    # Get summary
    summary = treasury.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(f"  Positions: {summary['num_positions']}")
    print(f"  Total Value: ${summary['net_value']:,.2f}")
    print(f"  Total Return: {summary['total_return_pct']:.2f}%")
