"""Time period value object module."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterator, Tuple


@dataclass(frozen=True)
class TimePeriod:
    """Value object representing a time period."""

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        """Validate time period after initialization."""
        if self.start_date > self.end_date:
            raise ValueError(
                f"Start date ({self.start_date}) cannot be after end date ({self.end_date})"
            )

    @property
    def days(self) -> int:
        """Get number of days in the period."""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_single_day(self) -> bool:
        """Check if period is a single day."""
        return self.start_date == self.end_date

    def contains(self, date_to_check: date) -> bool:
        """Check if a date is within the period.

        Args:
            date_to_check: Date to check

        Returns:
            True if date is within period
        """
        return self.start_date <= date_to_check <= self.end_date

    def overlaps(self, other: "TimePeriod") -> bool:
        """Check if this period overlaps with another.

        Args:
            other: Another time period

        Returns:
            True if periods overlap
        """
        return not (
            self.end_date < other.start_date or self.start_date > other.end_date
        )

    def merge(self, other: "TimePeriod") -> "TimePeriod":
        """Merge with another period.

        Args:
            other: Another time period

        Returns:
            New period covering both periods

        Raises:
            ValueError: If periods don't overlap or are not adjacent
        """
        if not self.overlaps(other) and not self._is_adjacent(other):
            raise ValueError("Periods must overlap or be adjacent to merge")

        return TimePeriod(
            start_date=min(self.start_date, other.start_date),
            end_date=max(self.end_date, other.end_date),
        )

    def _is_adjacent(self, other: "TimePeriod") -> bool:
        """Check if periods are adjacent (one day apart)."""
        return (
            self.end_date + timedelta(days=1) == other.start_date
            or other.end_date + timedelta(days=1) == self.start_date
        )

    def split_by_months(self) -> Iterator["TimePeriod"]:
        """Split period into monthly periods.

        Yields:
            TimePeriod for each month
        """
        current = self.start_date
        while current <= self.end_date:
            # Find last day of current month
            if current.month == 12:
                month_end = date(current.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)

            # Ensure we don't go past end_date
            period_end = min(month_end, self.end_date)

            yield TimePeriod(current, period_end)

            # Move to first day of next month
            current = period_end + timedelta(days=1)

    def to_datetime_range(self) -> Tuple[datetime, datetime]:
        """Convert to datetime range (start of start_date to end of end_date).

        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        start_datetime = datetime.combine(self.start_date, datetime.min.time())
        end_datetime = datetime.combine(self.end_date, datetime.max.time())
        return start_datetime, end_datetime

    @classmethod
    def from_strings(cls, start: str, end: str) -> "TimePeriod":
        """Create TimePeriod from date strings.

        Args:
            start: Start date string (YYYY-MM-DD)
            end: End date string (YYYY-MM-DD)

        Returns:
            TimePeriod instance
        """
        return cls(
            start_date=date.fromisoformat(start),
            end_date=date.fromisoformat(end),
        )

    @classmethod
    def last_n_days(cls, days: int, from_date: date | None = None) -> "TimePeriod":
        """Create period for last N days.

        Args:
            days: Number of days
            from_date: Reference date (defaults to today)

        Returns:
            TimePeriod instance
        """
        if days < 1:
            raise ValueError("Days must be positive")

        end = from_date or date.today()
        start = end - timedelta(days=days - 1)
        return cls(start_date=start, end_date=end)

    @classmethod
    def current_month(cls) -> "TimePeriod":
        """Create period for current month."""
        today = date.today()
        start = date(today.year, today.month, 1)
        return cls(start_date=start, end_date=today)

    @classmethod
    def current_year(cls) -> "TimePeriod":
        """Create period for current year."""
        today = date.today()
        start = date(today.year, 1, 1)
        return cls(start_date=start, end_date=today)

    def __str__(self) -> str:
        """String representation."""
        if self.is_single_day:
            return str(self.start_date)
        return f"{self.start_date} to {self.end_date}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"TimePeriod(start_date={self.start_date!r}, end_date={self.end_date!r})"