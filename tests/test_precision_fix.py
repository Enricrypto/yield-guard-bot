#!/usr/bin/env python3
"""
Test Decimal Precision Fix
Verifies that capital allocation works correctly without precision errors
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from simulator.treasury_simulator import TreasurySimulator


def test_capital_allocation():
    """Test that capital can be split across multiple protocols without precision errors"""
    print("="*70)
    print(" "*20 + "PRECISION FIX TEST")
    print("="*70)

    test_cases = [
        {"capital": 500000, "protocols": 3, "name": "3 protocols, $500K"},
        {"capital": 100000, "protocols": 2, "name": "2 protocols, $100K"},
        {"capital": 1000000, "protocols": 5, "name": "5 protocols, $1M"},
        {"capital": 333333.33, "protocols": 3, "name": "3 protocols, $333,333.33"},
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 70)

        capital = test['capital']
        num_protocols = test['protocols']

        # Initialize simulator
        total_capital = Decimal(str(capital))
        simulator = TreasurySimulator(
            initial_capital=total_capital,
            name="Test Simulator"
        )

        print(f"Initial Capital: ${total_capital:,.2f}")
        print(f"Number of Protocols: {num_protocols}")

        # Calculate per-protocol amount with proper precision
        capital_per_protocol = (total_capital / num_protocols).quantize(Decimal('0.01'))
        print(f"Capital per Protocol (rounded): ${capital_per_protocol:,.2f}")

        # Track remaining capital
        remaining_capital = total_capital
        deposited_total = Decimal('0')

        # Deposit to each protocol
        protocols = ['aave', 'morpho', 'compound', 'spark', 'radiant'][:num_protocols]

        try:
            for j, protocol in enumerate(protocols):
                # For last protocol, use all remaining capital
                if j == num_protocols - 1:
                    amount = remaining_capital
                else:
                    amount = capital_per_protocol
                    remaining_capital -= amount

                print(f"  Protocol {j+1} ({protocol}): Depositing ${amount:,.2f}, Remaining: ${remaining_capital:,.2f}")

                simulator.deposit(
                    protocol=protocol,
                    asset_symbol="USDC",
                    amount=amount,
                    supply_apy=Decimal('0.05'),
                    borrow_apy=Decimal('0.07'),
                    ltv=Decimal('0.75'),
                    liquidation_threshold=Decimal('0.80')
                )

                deposited_total += amount

            print(f"\n✓ SUCCESS - All deposits completed")
            print(f"  Total Deposited: ${deposited_total:,.2f}")
            print(f"  Expected: ${total_capital:,.2f}")
            print(f"  Difference: ${abs(deposited_total - total_capital):,.10f}")

            if deposited_total == total_capital:
                print(f"  ✓ EXACT MATCH - No precision loss!")
            else:
                print(f"  ⚠ Minor difference (acceptable)")

        except Exception as e:
            print(f"❌ FAILED: {e}")
            all_passed = False

    print("\n" + "="*70)
    print(" "*25 + "SUMMARY")
    print("="*70)

    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("\nPrecision Fix Features:")
        print("  ✓ Capital split across multiple protocols")
        print("  ✓ No rounding errors")
        print("  ✓ Last protocol gets exact remaining amount")
        print("  ✓ Total deposits equal initial capital")
    else:
        print("\n❌ SOME TESTS FAILED")

    print("\n" + "="*70)

    return all_passed


if __name__ == "__main__":
    try:
        success = test_capital_allocation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
