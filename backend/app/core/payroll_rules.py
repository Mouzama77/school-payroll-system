from typing import Dict


def calculate_daily_salary(base_salary: float, working_days: int) -> float:
    """Return the salary earned per working day."""
    return base_salary / working_days


def calculate_deductions(
    present: int,
    absent: int,
    half_day: int,
    daily_salary: float,
) -> Dict[str, float]:
    """Calculate deductions based on attendance.

    Returns a dict with keys ``absent_deductions``, ``half_day_deductions``
    and ``total_deductions``.
    """
    absent_deductions = absent * daily_salary
    half_day_deductions = half_day * daily_salary * 0.5
    total_deductions = absent_deductions + half_day_deductions
    return {
        "absent_deductions": absent_deductions,
        "half_day_deductions": half_day_deductions,
        "total_deductions": total_deductions,
    }


def calculate_net_salary(base_salary: float, deductions: float) -> float:
    """Return net salary after subtracting total deductions."""
    return base_salary - deductions


def calculate_payroll(
    base_salary: float,
    present: int,
    absent: int,
    half_day: int,
    working_days: int,
) -> Dict[str, float | int]:
    """Orchestrate payroll calculation using the pure rule functions.

    The returned dictionary mirrors the structure previously produced by the
    service layer's ``_calculate_amounts`` helper.
    """
    daily = calculate_daily_salary(base_salary, working_days)
    ded = calculate_deductions(
        present=present,
        absent=absent,
        half_day=half_day,
        daily_salary=daily,
    )
    net = calculate_net_salary(base_salary, ded["total_deductions"])
    return {
        "total_present": present,
        "total_absent": absent,
        "total_half_days": half_day,
        "daily_salary": round(daily, 2),
        "absent_deductions": round(ded["absent_deductions"], 2),
        "half_day_deductions": round(ded["half_day_deductions"], 2),
        "total_deductions": round(ded["total_deductions"], 2),
        "net_salary": round(net, 2),
    }
