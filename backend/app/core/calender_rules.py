from datetime import date

# Sunday is treated as the weekend by default.
WEEKEND_WEEKDAYS = frozenset({6})  # 6 == Sunday

# Day types that count as working days.
WORKING_DAY_TYPES = frozenset({"WORKING_DAY"})

# Day types that count as holidays / non-working days.
HOLIDAY_DAY_TYPES = frozenset({"SCHOOL_HOLIDAY", "EXAM_HOLIDAY", "VACATION"})


def resolve_day_type(d: date, calendar_entry) -> str:
    """Resolve the effective day type for a date.

    Default behaviour (Part 3 — "Sunday = holiday"):
      * An explicit calendar entry always wins (admin override).
      * With no entry, Sundays default to a holiday and every other
        day defaults to a working day.

    This means admins never have to create a calendar entry for every
    Sunday; Sundays are holidays unless explicitly marked WORKING_DAY.
    """
    if calendar_entry is not None:
        return calendar_entry.day_type
    if d.weekday() in WEEKEND_WEEKDAYS:
        return "HOLIDAY"
    return "WORKING_DAY"


def is_working_day(d: date, calendar_entry) -> bool:
    """Return True when attendance/payroll should treat `d` as a working day."""
    return resolve_day_type(d, calendar_entry) in WORKING_DAY_TYPES
