"""Interquartile-range based outlier detection."""

import pandas as pd


def iqr_bounds(values: pd.Series, multiplier: float = 1.5) -> tuple[float, float]:
    """Calculate lower and upper outlier bounds using the IQR rule.

    Missing values are ignored when calculating quartiles.
    """
    if multiplier < 0:
        raise ValueError("multiplier must be non-negative")
    numeric = pd.to_numeric(values, errors="raise").dropna()
    if numeric.empty:
        raise ValueError("At least one non-missing numeric value is required")

    first_quartile = numeric.quantile(0.25)
    third_quartile = numeric.quantile(0.75)
    spread = third_quartile - first_quartile
    return (
        float(first_quartile - multiplier * spread),
        float(third_quartile + multiplier * spread),
    )


def detect_iqr_outliers(
    values: pd.Series, multiplier: float = 1.5
) -> pd.Series:
    """Return a Boolean mask marking values outside the IQR bounds."""
    lower_bound, upper_bound = iqr_bounds(values, multiplier)
    return values.lt(lower_bound) | values.gt(upper_bound)