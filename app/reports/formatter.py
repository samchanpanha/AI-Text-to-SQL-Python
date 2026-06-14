"""
Excel column formatting rules.

Detects column types from header names and applies appropriate formatting:
- Leading-zero columns (phone, zip, ssn, code, id): force text
- Currency columns (price, amount, cost, salary): 2 decimal places
- Rate columns (rate, tax, percentage, ratio): 4 decimal places
- Integer columns (quantity, count, stock): no decimals
- Float columns: auto-detect precision from first 100 sample rows

Usage:
    fmt = get_column_format("unit_price")
    # => {"number_format": "#,##0.00", "force_text": False}
"""

import re

# Columns that must be treated as text to preserve leading zeros
TEXT_COLUMN_PATTERNS = re.compile(
    r"^(phone|zip|postal|ssn|code|sku|id|account|ref|reference|serial)", re.IGNORECASE
)

# Currency columns → 2 decimal places
CURRENCY_PATTERNS = re.compile(
    r"(price|amount|cost|salary|wage|fee|budget|revenue|income|payment|total|subtotal)", re.IGNORECASE
)

# Rate columns → 4 decimal places
RATE_PATTERNS = re.compile(
    r"(rate|tax|percentage|ratio|interest|margin|discount|commission)", re.IGNORECASE
)

# Integer columns → no decimals
INTEGER_PATTERNS = re.compile(
    r"(quantity|count|stock|qty|units|number_of|num_|total_count|age|year|month|day)", re.IGNORECASE
)


def get_column_format(column_name: str) -> dict:
    """Determine Excel number format and text behavior for a column."""
    if TEXT_COLUMN_PATTERNS.search(column_name):
        return {"number_format": None, "force_text": True}

    if CURRENCY_PATTERNS.search(column_name):
        return {"number_format": "#,##0.00", "force_text": False}

    if RATE_PATTERNS.search(column_name):
        return {"number_format": "#,##0.0000", "force_text": False}

    if INTEGER_PATTERNS.search(column_name):
        return {"number_format": "#,##0", "force_text": False}

    # Default: auto-detect or plain
    return {"number_format": None, "force_text": False}


def detect_precision(values: list, sample_size: int = 100) -> int:
    """Detect max decimal places from a sample of values."""
    max_decimals = 0
    for val in values[:sample_size]:
        if isinstance(val, float):
            str_val = str(val)
            if "." in str_val:
                decimals = len(str_val.split(".")[1])
                max_decimals = max(max_decimals, decimals)
    return max_decimals
