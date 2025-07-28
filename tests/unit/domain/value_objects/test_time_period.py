"""Unit tests for TimePeriod value object."""
import pytest
from datetime import date, datetime, timedelta
from typing import List

from app.domain.value_objects.time_period import TimePeriod


class TestTimePeriod:
    """Test cases for TimePeriod value object."""
    
    # Initialization tests
    def test_init_valid_period(self):
        """Test initialization with valid period."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)
        period = TimePeriod(start_date=start, end_date=end)
        assert period.start_date == start
        assert period.end_date == end
    
    def test_init_single_day_period(self):
        """Test initialization with single day period."""
        single_day = date(2023, 6, 15)
        period = TimePeriod(start_date=single_day, end_date=single_day)
        assert period.start_date == single_day
        assert period.end_date == single_day
        assert period.is_single_day
    
    def test_init_invalid_period_start_after_end(self):
        """Test initialization with start date after end date."""
        start = date(2023, 2, 1)
        end = date(2023, 1, 1)
        with pytest.raises(ValueError, match="Start date.*cannot be after end date"):
            TimePeriod(start_date=start, end_date=end)
    
    def test_frozen_dataclass(self):
        """Test that TimePeriod is immutable (frozen)."""
        period = TimePeriod(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31)
        )
        with pytest.raises(AttributeError):
            period.start_date = date(2023, 2, 1)
    
    # Property tests
    def test_days_property(self):
        """Test days property calculation."""
        # Single day
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 1))
        assert period1.days == 1
        
        # Multiple days
        period2 = TimePeriod(date(2023, 1, 1), date(2023, 1, 10))
        assert period2.days == 10
        
        # Full month
        period3 = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        assert period3.days == 31
        
        # Across months
        period4 = TimePeriod(date(2023, 1, 15), date(2023, 2, 15))
        assert period4.days == 32
    
    def test_is_single_day_property(self):
        """Test is_single_day property."""
        # Single day
        single = TimePeriod(date(2023, 5, 20), date(2023, 5, 20))
        assert single.is_single_day is True
        
        # Multiple days
        multiple = TimePeriod(date(2023, 5, 20), date(2023, 5, 21))
        assert multiple.is_single_day is False
    
    # Contains method tests
    def test_contains_date_within_period(self):
        """Test contains method with date within period."""
        period = TimePeriod(date(2023, 1, 10), date(2023, 1, 20))
        
        # Start date
        assert period.contains(date(2023, 1, 10)) is True
        # End date
        assert period.contains(date(2023, 1, 20)) is True
        # Middle date
        assert period.contains(date(2023, 1, 15)) is True
    
    def test_contains_date_outside_period(self):
        """Test contains method with date outside period."""
        period = TimePeriod(date(2023, 1, 10), date(2023, 1, 20))
        
        # Before start
        assert period.contains(date(2023, 1, 9)) is False
        # After end
        assert period.contains(date(2023, 1, 21)) is False
        # Way outside
        assert period.contains(date(2022, 12, 1)) is False
    
    def test_contains_single_day_period(self):
        """Test contains method for single day period."""
        period = TimePeriod(date(2023, 7, 4), date(2023, 7, 4))
        
        assert period.contains(date(2023, 7, 4)) is True
        assert period.contains(date(2023, 7, 3)) is False
        assert period.contains(date(2023, 7, 5)) is False
    
    # Overlaps method tests
    def test_overlaps_fully_overlapping(self):
        """Test overlaps with fully overlapping periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        period2 = TimePeriod(date(2023, 1, 10), date(2023, 1, 20))
        
        assert period1.overlaps(period2) is True
        assert period2.overlaps(period1) is True
    
    def test_overlaps_partially_overlapping(self):
        """Test overlaps with partially overlapping periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 15))
        period2 = TimePeriod(date(2023, 1, 10), date(2023, 1, 25))
        
        assert period1.overlaps(period2) is True
        assert period2.overlaps(period1) is True
    
    def test_overlaps_edge_case_same_boundary(self):
        """Test overlaps when periods share a boundary."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 15))
        period2 = TimePeriod(date(2023, 1, 15), date(2023, 1, 31))
        
        assert period1.overlaps(period2) is True
        assert period2.overlaps(period1) is True
    
    def test_overlaps_non_overlapping(self):
        """Test overlaps with non-overlapping periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 10))
        period2 = TimePeriod(date(2023, 1, 15), date(2023, 1, 25))
        
        assert period1.overlaps(period2) is False
        assert period2.overlaps(period1) is False
    
    def test_overlaps_adjacent_periods(self):
        """Test overlaps with adjacent periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 10))
        period2 = TimePeriod(date(2023, 1, 11), date(2023, 1, 20))
        
        assert period1.overlaps(period2) is False
        assert period2.overlaps(period1) is False
    
    # Merge method tests
    def test_merge_overlapping_periods(self):
        """Test merging overlapping periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 15))
        period2 = TimePeriod(date(2023, 1, 10), date(2023, 1, 25))
        
        merged = period1.merge(period2)
        assert merged.start_date == date(2023, 1, 1)
        assert merged.end_date == date(2023, 1, 25)
    
    def test_merge_adjacent_periods(self):
        """Test merging adjacent periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 10))
        period2 = TimePeriod(date(2023, 1, 11), date(2023, 1, 20))
        
        merged = period1.merge(period2)
        assert merged.start_date == date(2023, 1, 1)
        assert merged.end_date == date(2023, 1, 20)
    
    def test_merge_same_periods(self):
        """Test merging identical periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        period2 = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        
        merged = period1.merge(period2)
        assert merged.start_date == date(2023, 1, 1)
        assert merged.end_date == date(2023, 1, 31)
    
    def test_merge_non_overlapping_non_adjacent(self):
        """Test merge fails with non-overlapping, non-adjacent periods."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 10))
        period2 = TimePeriod(date(2023, 1, 15), date(2023, 1, 25))
        
        with pytest.raises(ValueError, match="Periods must overlap or be adjacent"):
            period1.merge(period2)
    
    def test_merge_reverse_order(self):
        """Test merge works regardless of period order."""
        period1 = TimePeriod(date(2023, 1, 20), date(2023, 1, 31))
        period2 = TimePeriod(date(2023, 1, 1), date(2023, 1, 10))
        
        # Adjacent periods
        period3 = TimePeriod(date(2023, 1, 11), date(2023, 1, 19))
        
        # Merge 1 and 3 (adjacent)
        merged1 = period1.merge(period3)
        assert merged1.start_date == date(2023, 1, 11)
        assert merged1.end_date == date(2023, 1, 31)
        
        # Then merge with 2
        merged2 = merged1.merge(period2)
        assert merged2.start_date == date(2023, 1, 1)
        assert merged2.end_date == date(2023, 1, 31)
    
    # Split by months tests
    def test_split_by_months_single_month(self):
        """Test split_by_months for period within single month."""
        period = TimePeriod(date(2023, 1, 10), date(2023, 1, 25))
        splits = list(period.split_by_months())
        
        assert len(splits) == 1
        assert splits[0].start_date == date(2023, 1, 10)
        assert splits[0].end_date == date(2023, 1, 25)
    
    def test_split_by_months_multiple_months(self):
        """Test split_by_months for period spanning multiple months."""
        period = TimePeriod(date(2023, 1, 15), date(2023, 3, 20))
        splits = list(period.split_by_months())
        
        assert len(splits) == 3
        # January part
        assert splits[0].start_date == date(2023, 1, 15)
        assert splits[0].end_date == date(2023, 1, 31)
        # February part
        assert splits[1].start_date == date(2023, 2, 1)
        assert splits[1].end_date == date(2023, 2, 28)
        # March part
        assert splits[2].start_date == date(2023, 3, 1)
        assert splits[2].end_date == date(2023, 3, 20)
    
    def test_split_by_months_year_boundary(self):
        """Test split_by_months across year boundary."""
        period = TimePeriod(date(2022, 12, 15), date(2023, 1, 15))
        splits = list(period.split_by_months())
        
        assert len(splits) == 2
        # December 2022
        assert splits[0].start_date == date(2022, 12, 15)
        assert splits[0].end_date == date(2022, 12, 31)
        # January 2023
        assert splits[1].start_date == date(2023, 1, 1)
        assert splits[1].end_date == date(2023, 1, 15)
    
    def test_split_by_months_leap_year(self):
        """Test split_by_months handles leap year correctly."""
        period = TimePeriod(date(2024, 2, 15), date(2024, 3, 15))
        splits = list(period.split_by_months())
        
        assert len(splits) == 2
        # February 2024 (leap year)
        assert splits[0].start_date == date(2024, 2, 15)
        assert splits[0].end_date == date(2024, 2, 29)
        # March 2024
        assert splits[1].start_date == date(2024, 3, 1)
        assert splits[1].end_date == date(2024, 3, 15)
    
    # Datetime range tests
    def test_to_datetime_range(self):
        """Test conversion to datetime range."""
        period = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        start_dt, end_dt = period.to_datetime_range()
        
        # Start should be beginning of day
        assert start_dt == datetime(2023, 1, 1, 0, 0, 0, 0)
        # End should be end of day
        assert end_dt == datetime(2023, 1, 31, 23, 59, 59, 999999)
    
    def test_to_datetime_range_single_day(self):
        """Test datetime range for single day period."""
        period = TimePeriod(date(2023, 6, 15), date(2023, 6, 15))
        start_dt, end_dt = period.to_datetime_range()
        
        assert start_dt.date() == date(2023, 6, 15)
        assert end_dt.date() == date(2023, 6, 15)
        assert start_dt.time() == datetime.min.time()
        assert end_dt.time() == datetime.max.time()
    
    # Class method tests
    def test_from_strings_valid(self):
        """Test creating TimePeriod from valid date strings."""
        period = TimePeriod.from_strings("2023-01-01", "2023-01-31")
        assert period.start_date == date(2023, 1, 1)
        assert period.end_date == date(2023, 1, 31)
    
    def test_from_strings_invalid_format(self):
        """Test from_strings with invalid date format."""
        with pytest.raises(ValueError):
            TimePeriod.from_strings("01/01/2023", "31/01/2023")
        
        with pytest.raises(ValueError):
            TimePeriod.from_strings("2023-1-1", "2023-1-31")  # Missing leading zeros
    
    def test_from_strings_invalid_dates(self):
        """Test from_strings with invalid date values."""
        with pytest.raises(ValueError):
            TimePeriod.from_strings("2023-02-30", "2023-03-01")  # Feb 30 doesn't exist
    
    def test_last_n_days_default_from_date(self):
        """Test last_n_days with default from_date (today)."""
        # We can't test exact dates since today changes, but we can test the logic
        period = TimePeriod.last_n_days(7)
        assert period.days == 7
        assert period.end_date == date.today()
        assert period.start_date == date.today() - timedelta(days=6)
    
    def test_last_n_days_custom_from_date(self):
        """Test last_n_days with custom from_date."""
        from_date = date(2023, 1, 15)
        period = TimePeriod.last_n_days(10, from_date)
        
        assert period.days == 10
        assert period.end_date == date(2023, 1, 15)
        assert period.start_date == date(2023, 1, 6)
    
    def test_last_n_days_single_day(self):
        """Test last_n_days for single day."""
        from_date = date(2023, 1, 15)
        period = TimePeriod.last_n_days(1, from_date)
        
        assert period.days == 1
        assert period.start_date == period.end_date == from_date
    
    def test_last_n_days_invalid(self):
        """Test last_n_days with invalid input."""
        with pytest.raises(ValueError, match="Days must be positive"):
            TimePeriod.last_n_days(0)
        
        with pytest.raises(ValueError, match="Days must be positive"):
            TimePeriod.last_n_days(-5)
    
    def test_current_month(self):
        """Test current_month class method."""
        period = TimePeriod.current_month()
        today = date.today()
        
        assert period.start_date == date(today.year, today.month, 1)
        assert period.end_date == today
    
    def test_current_year(self):
        """Test current_year class method."""
        period = TimePeriod.current_year()
        today = date.today()
        
        assert period.start_date == date(today.year, 1, 1)
        assert period.end_date == today
    
    # String representation tests
    def test_str_single_day(self):
        """Test string representation for single day."""
        period = TimePeriod(date(2023, 1, 15), date(2023, 1, 15))
        assert str(period) == "2023-01-15"
    
    def test_str_multiple_days(self):
        """Test string representation for multiple days."""
        period = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        assert str(period) == "2023-01-01 to 2023-01-31"
    
    def test_repr(self):
        """Test developer representation."""
        period = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        expected = "TimePeriod(start_date=datetime.date(2023, 1, 1), end_date=datetime.date(2023, 1, 31))"
        assert repr(period) == expected
    
    # Edge cases and integration tests
    def test_hash_and_equality(self):
        """Test that TimePeriod can be used in sets and as dict keys."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        period2 = TimePeriod(date(2023, 1, 1), date(2023, 1, 31))
        period3 = TimePeriod(date(2023, 2, 1), date(2023, 2, 28))
        
        # Equality
        assert period1 == period2
        assert period1 != period3
        
        # Hash consistency
        assert hash(period1) == hash(period2)
        
        # Can be used in set
        period_set = {period1, period2, period3}
        assert len(period_set) == 2  # period1 and period2 are duplicates
        
        # Can be used as dict key
        period_dict = {period1: "January", period3: "February"}
        assert period_dict[period2] == "January"  # period2 equals period1
    
    def test_is_adjacent_helper(self):
        """Test the _is_adjacent helper method."""
        period1 = TimePeriod(date(2023, 1, 1), date(2023, 1, 10))
        period2 = TimePeriod(date(2023, 1, 11), date(2023, 1, 20))
        period3 = TimePeriod(date(2023, 1, 12), date(2023, 1, 20))
        
        # Adjacent periods
        assert period1._is_adjacent(period2) is True
        assert period2._is_adjacent(period1) is True
        
        # Non-adjacent periods
        assert period1._is_adjacent(period3) is False
        assert period3._is_adjacent(period1) is False
    
    def test_complex_period_operations(self):
        """Test complex combinations of period operations."""
        # Create periods for each quarter of 2023
        q1 = TimePeriod(date(2023, 1, 1), date(2023, 3, 31))
        q2 = TimePeriod(date(2023, 4, 1), date(2023, 6, 30))
        q3 = TimePeriod(date(2023, 7, 1), date(2023, 9, 30))
        q4 = TimePeriod(date(2023, 10, 1), date(2023, 12, 31))
        
        # Merge adjacent quarters
        h1 = q1.merge(q2)  # First half
        h2 = q3.merge(q4)  # Second half
        
        # Merge halves into full year
        full_year = h1.merge(h2)
        assert full_year.start_date == date(2023, 1, 1)
        assert full_year.end_date == date(2023, 12, 31)
        assert full_year.days == 365
        
        # Split by months and verify count
        monthly_periods = list(full_year.split_by_months())
        assert len(monthly_periods) == 12
        
        # Verify all months are covered
        for i, month_period in enumerate(monthly_periods, 1):
            assert month_period.start_date.month == i