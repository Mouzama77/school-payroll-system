"""Unit tests for PayrollService._calculate_amounts — Task 24.

Validates Design Properties 1 and 2:
  Property 1 (Net Salary Formula Invariant):
    net_salary = round(base - (absent * daily) - (half_days * daily * 0.5), 2)
  Property 2 (Daily Salary Precision):
    daily_salary = round(base / working_days, 2)
"""

import pytest

from app.services.payroll_service import PayrollService

# ── Helpers ────────────────────────────────────────────────────────────────────

def calc(base, absent=0, half_days=0, working_days=30):
    """Thin wrapper so tests stay readable."""
    return PayrollService._calculate_amounts(
        base_salary=base,
        total_present=0,  # not used in formula
        total_absent=absent,
        total_half_days=half_days,
        working_days=working_days,
    )


# ── Task 24.2 — Integer and float salaries ─────────────────────────────────────

class TestDailySalaryPrecision:
    """Design Property 2: daily_salary = round(base / working_days, 2)."""

    def test_integer_salary_divisible(self):
        r = calc(30000, working_days=30)
        assert r["daily_salary"] == 1000.00

    def test_integer_salary_not_divisible(self):
        # 1000 / 30 = 33.3333... → rounds to 33.33
        r = calc(1000, working_days=30)
        assert r["daily_salary"] == 33.33

    def test_float_salary(self):
        # 1200000.00 / 30 = 40000.00
        r = calc(1200000.0, working_days=30)
        assert r["daily_salary"] == 40000.00

    def test_float_salary_with_remainder(self):
        # 100.01 / 30 = 3.3336... → rounds to 3.33
        r = calc(100.01, working_days=30)
        assert r["daily_salary"] == 3.33

    def test_academic_calendar_working_days(self):
        # When academic calendar provides 20 working days
        r = calc(1200000.0, working_days=20)
        assert r["daily_salary"] == 60000.00


class TestAbsentDeductions:
    """Design Property 1: absent_deductions = round(total_absent * daily_salary, 2)."""

    def test_no_absences(self):
        r = calc(30000)
        assert r["absent_deductions"] == 0.00

    def test_one_absent(self):
        # daily = 30000/30 = 1000; absent_ded = 1 * 1000 = 1000
        r = calc(30000, absent=1)
        assert r["absent_deductions"] == 1000.00

    def test_multiple_absences(self):
        # daily = 1200000/30 = 40000; absent_ded = 3 * 40000 = 120000
        r = calc(1200000, absent=3)
        assert r["absent_deductions"] == 120000.00

    def test_all_days_absent(self):
        # 30 absences; daily = 1000; absent_ded = 30 * 1000 = 30000
        r = calc(30000, absent=30)
        assert r["absent_deductions"] == 30000.00
        assert r["net_salary"] == 0.00

    def test_absent_deduction_rounding(self):
        # service: absent_ded = round(2 * (1000/30), 2) = round(66.666, 2) = 66.67
        r = calc(1000, absent=2)
        assert r["absent_deductions"] == round(2 * (1000 / 30), 2)


class TestHalfDayDeductions:
    """Design Property 1: half_day_deductions = round(total_half_days * daily * 0.5, 2)."""

    def test_no_half_days(self):
        r = calc(30000)
        assert r["half_day_deductions"] == 0.00

    def test_one_half_day(self):
        # daily = 40000; half_day = 0.5 * 40000 = 20000
        r = calc(1200000, half_days=1)
        assert r["half_day_deductions"] == 20000.00

    def test_multiple_half_days(self):
        # daily = 40000; half_day = 0.5 * 40000 * 3 = 60000
        r = calc(1200000, half_days=3)
        assert r["half_day_deductions"] == 60000.00

    def test_half_day_rounding(self):
        # service: half_ded = round(0.5 * (1000/30), 2) = round(16.666, 2) = 16.67
        r = calc(1000, half_days=1)
        assert r["half_day_deductions"] == round(0.5 * (1000 / 30), 2)


class TestNetSalaryFormula:
    """Design Property 1: net_salary = round(base - absent_ded - half_day_ded, 2)."""

    def test_no_deductions(self):
        r = calc(30000)
        assert r["net_salary"] == 30000.00

    def test_absent_only(self):
        # net = 1200000 - 3*40000 = 1200000 - 120000 = 1080000
        r = calc(1200000, absent=3)
        assert r["net_salary"] == 1080000.00

    def test_half_days_only(self):
        # net = 1200000 - 1*40000*0.5 = 1200000 - 20000 = 1180000
        r = calc(1200000, half_days=1)
        assert r["net_salary"] == 1180000.00

    def test_combined_deductions(self):
        # Task 17 scenario: 3 absent + 1 half-day, salary=1200000, daily=40000
        # absent_ded = 120000, half_ded = 20000, net = 1060000
        r = calc(1200000, absent=3, half_days=1)
        assert r["absent_deductions"] == 120000.00
        assert r["half_day_deductions"] == 20000.00
        assert r["net_salary"] == 1060000.00

    def test_all_days_absent_net_zero(self):
        # 30 absences from 30 working days → net = 0
        r = calc(30000, absent=30)
        assert r["net_salary"] == 0.00

    def test_salary_not_divisible_by_30(self):
        """Edge case: salary not evenly divisible by 30 — all values still rounded.

        The service computes: absent_deductions = round(absent * (base/working_days), 2)
        — it does NOT first round daily_salary then multiply.
        Only the final per-field result is rounded to 2dp.
        """
        r = calc(100, absent=2)
        daily_raw = 100 / 30
        expected_daily = round(daily_raw, 2)
        expected_absent_ded = round(2 * daily_raw, 2)
        expected_net = round(100 - 2 * daily_raw, 2)
        assert r["daily_salary"] == expected_daily
        assert r["absent_deductions"] == expected_absent_ded
        assert r["net_salary"] == expected_net

    def test_all_values_rounded_to_2dp(self):
        """Every returned monetary value must be rounded to exactly 2 decimal places."""
        r = calc(99999.99, absent=7, half_days=3)
        for key in ("daily_salary", "absent_deductions", "half_day_deductions",
                    "total_deductions", "net_salary"):
            val = r[key]
            assert val == round(val, 2), f"{key}={val} is not rounded to 2dp"
