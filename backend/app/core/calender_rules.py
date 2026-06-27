from datetime import date

WEEKEND = 6  # Sunday

def is_working_day(d: date, holidays: set[date]) -> bool:
    if d in holidays:
        return False
    if d.weekday() == WEEKEND:
        return False
    return True