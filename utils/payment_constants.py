"""
Payment Module Constants
=========================
Shared constants for school-year months and payment statuses.
"""

# School year months in chronological order (September -> June)
SCHOOL_MONTHS = [
    "Septembre", "Octobre", "Novembre", "Décembre",
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
]

# Maps each school-year month to a (calendar_month_number, year_offset)
# year_offset 0 = start_year (e.g. 2025), 1 = end_year (e.g. 2026)
MONTH_CALENDAR_MAP = {
    "Septembre": (9, 0),
    "Octobre": (10, 0),
    "Novembre": (11, 0),
    "Décembre": (12, 0),
    "Janvier": (1, 1),
    "Février": (2, 1),
    "Mars": (3, 1),
    "Avril": (4, 1),
    "Mai": (5, 1),
    "Juin": (6, 1),
}

# Status values stored in month_status.status
STATUS_PAYE = "PAYE"
STATUS_UNPAID = "UNPAID"
STATUS_NAN = "NAN"

# Display labels & colors for statuses
STATUS_LABELS = {
    STATUS_PAYE: "Payé",
    STATUS_UNPAID: "Non payé",
    STATUS_NAN: "Non inscrit",
}

STATUS_COLORS = {
    STATUS_PAYE: "#22C55E",     # green
    STATUS_UNPAID: "#EF4444",   # red
    STATUS_NAN: "#94A3B8",      # gray
}

# Payment types
PAYMENT_TYPES = ["Inscription", "Mensualité", "Transport"]


def calendar_month_number(month_name: str) -> int:
    """Return the calendar month number (1-12) for a school-year month name."""
    return MONTH_CALENDAR_MAP.get(month_name, (0, 0))[0]


def parse_month_value(value) -> str:
    """
    Convert a raw Excel cell value for a month column into one of
    STATUS_PAYE, STATUS_UNPAID, STATUS_NAN.
    """
    import pandas as pd

    if value is None:
        return STATUS_UNPAID
    if isinstance(value, float) and pd.isna(value):
        return STATUS_UNPAID

    text = str(value).strip().upper()
    if text in ("", "NONE", "NAN") and not isinstance(value, str):
        return STATUS_UNPAID
    if text == "NAN":
        return STATUS_NAN
    if text in ("PAYÉ", "PAYE", "PAID", "OUI", "YES"):
        return STATUS_PAYE
    if text == "":
        return STATUS_UNPAID
    # Any other unrecognized value defaults to unpaid
    return STATUS_UNPAID
