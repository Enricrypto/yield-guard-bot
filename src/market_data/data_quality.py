"""
Data Quality and Integrity Module
Ensures fetched data is fresh, accurate, and properly smoothed
Addresses issues with oracle trust, staleness, and rate volatility
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
import statistics


@dataclass
class DataQualityMetrics:
    """Metrics for assessing data quality"""
    is_stale: bool
    staleness_seconds: float
    confidence_score: float  # 0.0 to 1.0
    anomaly_detected: bool
    smoothed_value: Optional[Decimal] = None
    raw_value: Optional[Decimal] = None
    volatility: Optional[Decimal] = None


class DataQualityChecker:
    """
    Checks data quality and prevents simulation from using stale/unreliable data

    Implements:
    1. Staleness checks - ensures data is recent
    2. Anomaly detection - flags suspicious spikes
    3. Confidence scoring - quantifies data reliability
    4. Rate smoothing - averages volatile protocol rates
    """

    def __init__(
        self,
        max_staleness_seconds: int = 3600,  # 1 hour default
        spike_threshold: Decimal = Decimal('3.0'),  # 3x spike = anomaly
        smoothing_window: int = 7  # 7-day average for rates
    ):
        """
        Initialize data quality checker

        Args:
            max_staleness_seconds: Max age before data considered stale
            spike_threshold: Multiple above mean to flag as spike
            smoothing_window: Number of periods to smooth over
        """
        self.max_staleness_seconds = max_staleness_seconds
        self.spike_threshold = spike_threshold
        self.smoothing_window = smoothing_window

    def check_staleness(
        self,
        timestamp: datetime,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, float]:
        """
        Check if data is stale

        Args:
            timestamp: Timestamp of data
            current_time: Current time (defaults to now)

        Returns:
            Tuple of (is_stale, age_in_seconds)
        """
        if current_time is None:
            current_time = datetime.now()

        age = (current_time - timestamp).total_seconds()
        is_stale = age > self.max_staleness_seconds

        return is_stale, age

    def detect_anomaly(
        self,
        value: Decimal,
        historical_values: List[Decimal]
    ) -> bool:
        """
        Detect if value is anomalous compared to history

        Uses simple spike detection:
        - If value > mean + (spike_threshold * std_dev), flag as anomaly

        Args:
            value: Current value to check
            historical_values: Historical values for comparison

        Returns:
            True if anomaly detected
        """
        if not historical_values or len(historical_values) < 2:
            return False

        try:
            mean = Decimal(str(statistics.mean([float(v) for v in historical_values])))
            std_dev = Decimal(str(statistics.stdev([float(v) for v in historical_values])))

            # Upper bound for acceptable values
            upper_bound = mean + (self.spike_threshold * std_dev)

            # Check if current value is a spike
            if value > upper_bound:
                return True

            # Also check for unrealistic drops (more than 90% drop)
            if value < mean * Decimal('0.1') and mean > Decimal('0.01'):
                return True

            return False

        except (ValueError, statistics.StatisticsError):
            # Not enough data or invalid data
            return False

    def calculate_confidence(
        self,
        is_stale: bool,
        staleness_seconds: float,
        anomaly_detected: bool,
        data_points_available: int
    ) -> Decimal:
        """
        Calculate confidence score for data

        Confidence factors:
        - Freshness (0-40 points): Fresh data scores higher
        - No anomalies (0-30 points): Clean data scores higher
        - Data availability (0-30 points): More historical data = higher confidence

        Args:
            is_stale: Whether data is stale
            staleness_seconds: Age of data in seconds
            anomaly_detected: Whether anomaly was detected
            data_points_available: Number of historical data points

        Returns:
            Confidence score from 0.0 to 1.0
        """
        score = Decimal('0')

        # Freshness score (0-40 points)
        if not is_stale:
            # Exponential decay based on age
            age_factor = Decimal(str(staleness_seconds / self.max_staleness_seconds))
            freshness_score = Decimal('40') * (Decimal('1') - age_factor)
            score += freshness_score
        else:
            # Stale data gets 0 points
            score += Decimal('0')

        # Anomaly score (0-30 points)
        if not anomaly_detected:
            score += Decimal('30')

        # Data availability score (0-30 points)
        # More data points = higher confidence
        if data_points_available >= 30:
            score += Decimal('30')
        elif data_points_available >= 7:
            score += Decimal('30') * (Decimal(str(data_points_available)) / Decimal('30'))
        else:
            score += Decimal('10')

        # Normalize to 0.0-1.0
        return score / Decimal('100')

    def smooth_rate(
        self,
        current_value: Decimal,
        historical_values: List[Decimal]
    ) -> Decimal:
        """
        Smooth volatile protocol rates using moving average

        Args:
            current_value: Current rate value
            historical_values: Historical rate values

        Returns:
            Smoothed rate value
        """
        if not historical_values:
            return current_value

        # Use exponential moving average (EMA) for smoothing
        # EMA gives more weight to recent values
        alpha = Decimal('2') / (Decimal(str(self.smoothing_window)) + Decimal('1'))

        # Start with most recent historical value
        ema = historical_values[-1] if historical_values else current_value

        # Calculate EMA
        for value in historical_values[-self.smoothing_window:]:
            ema = alpha * value + (Decimal('1') - alpha) * ema

        # Final EMA with current value
        smoothed = alpha * current_value + (Decimal('1') - alpha) * ema

        return smoothed

    def assess_data_quality(
        self,
        value: Decimal,
        timestamp: datetime,
        historical_values: List[Decimal],
        current_time: Optional[datetime] = None
    ) -> DataQualityMetrics:
        """
        Comprehensive data quality assessment

        Args:
            value: Current value to assess
            timestamp: Timestamp of current value
            historical_values: Historical values for context
            current_time: Current time (defaults to now)

        Returns:
            DataQualityMetrics with full assessment
        """
        # Check staleness
        is_stale, staleness_seconds = self.check_staleness(timestamp, current_time)

        # Detect anomalies
        anomaly_detected = self.detect_anomaly(value, historical_values)

        # Calculate confidence
        confidence = self.calculate_confidence(
            is_stale,
            staleness_seconds,
            anomaly_detected,
            len(historical_values)
        )

        # Smooth the rate
        smoothed_value = self.smooth_rate(value, historical_values)

        # Calculate volatility if enough data
        volatility = None
        if len(historical_values) >= 2:
            try:
                volatility = Decimal(str(statistics.stdev([float(v) for v in historical_values])))
            except statistics.StatisticsError:
                volatility = Decimal('0')

        return DataQualityMetrics(
            is_stale=is_stale,
            staleness_seconds=staleness_seconds,
            confidence_score=float(confidence),
            anomaly_detected=anomaly_detected,
            smoothed_value=smoothed_value,
            raw_value=value,
            volatility=volatility
        )


class RateSmoother:
    """
    Specialized class for smoothing protocol APY rates

    Protocol APYs are noisy due to:
    - Utilization rate fluctuations
    - Governance changes
    - Oracle price updates
    - Market conditions

    This smoother provides stable rates for realistic simulations.
    """

    def __init__(self, window_size: int = 7, cap_max_change: Decimal = Decimal('0.50')):
        """
        Initialize rate smoother

        Args:
            window_size: Number of periods to average
            cap_max_change: Maximum allowed change per period (0.50 = 50%)
        """
        self.window_size = window_size
        self.cap_max_change = cap_max_change

    def smooth_simple_moving_average(
        self,
        rates: List[Decimal]
    ) -> List[Decimal]:
        """
        Apply simple moving average smoothing

        Args:
            rates: List of raw rates

        Returns:
            List of smoothed rates
        """
        if len(rates) < self.window_size:
            # Not enough data, return original
            return rates

        smoothed = []
        for i in range(len(rates)):
            if i < self.window_size - 1:
                # Not enough history yet, use what we have
                window = rates[:i+1]
            else:
                # Use full window
                window = rates[i-self.window_size+1:i+1]

            avg = sum(window) / len(window)
            smoothed.append(avg)

        return smoothed

    def cap_rate_changes(
        self,
        rates: List[Decimal]
    ) -> List[Decimal]:
        """
        Cap maximum rate change per period

        Prevents unrealistic jumps that don't reflect real protocol behavior

        Args:
            rates: List of rates

        Returns:
            List of capped rates
        """
        if len(rates) < 2:
            return rates

        capped = [rates[0]]

        for i in range(1, len(rates)):
            prev_rate = capped[-1]
            curr_rate = rates[i]

            # Calculate change
            if prev_rate > 0:
                change = (curr_rate - prev_rate) / prev_rate
            else:
                change = Decimal('0')

            # Cap the change
            if abs(change) > self.cap_max_change:
                # Apply capped change
                if change > 0:
                    capped_rate = prev_rate * (Decimal('1') + self.cap_max_change)
                else:
                    capped_rate = prev_rate * (Decimal('1') - self.cap_max_change)

                capped.append(capped_rate)
            else:
                capped.append(curr_rate)

        return capped

    def smooth_and_cap(
        self,
        rates: List[Decimal]
    ) -> List[Decimal]:
        """
        Apply both smoothing and capping

        Args:
            rates: List of raw rates

        Returns:
            List of smoothed and capped rates
        """
        # First smooth with moving average
        smoothed = self.smooth_simple_moving_average(rates)

        # Then cap changes
        capped = self.cap_rate_changes(smoothed)

        return capped


if __name__ == "__main__":
    # Example usage
    print("Data Quality Checker Example\n" + "="*50)

    checker = DataQualityChecker()

    # Simulate historical APY data
    historical_rates = [
        Decimal('0.05'), Decimal('0.051'), Decimal('0.049'),
        Decimal('0.052'), Decimal('0.050'), Decimal('0.048'),
        Decimal('0.051')
    ]

    # Current rate with spike
    current_rate = Decimal('0.15')  # Suspicious spike
    current_timestamp = datetime.now()

    # Assess quality
    quality = checker.assess_data_quality(
        current_rate,
        current_timestamp,
        historical_rates
    )

    print(f"Raw Value: {quality.raw_value}")
    print(f"Smoothed Value: {quality.smoothed_value}")
    print(f"Is Stale: {quality.is_stale}")
    print(f"Anomaly Detected: {quality.anomaly_detected}")
    print(f"Confidence Score: {quality.confidence_score:.2f}")
    print(f"Volatility: {quality.volatility}\n")

    # Test rate smoother
    print("="*50)
    print("Rate Smoother Example\n")

    smoother = RateSmoother()

    # Simulate volatile rates
    volatile_rates = [
        Decimal('0.05'), Decimal('0.08'), Decimal('0.04'),
        Decimal('0.12'), Decimal('0.03'), Decimal('0.09'),
        Decimal('0.06'), Decimal('0.15'), Decimal('0.02')
    ]

    smoothed_rates = smoother.smooth_and_cap(volatile_rates)

    print("Original Rates:")
    for i, rate in enumerate(volatile_rates):
        print(f"  Day {i+1}: {rate*100:.2f}%")

    print("\nSmoothed & Capped Rates:")
    for i, rate in enumerate(smoothed_rates):
        print(f"  Day {i+1}: {rate*100:.2f}%")
