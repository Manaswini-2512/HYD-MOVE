"""Descriptive statistics and frequency summaries."""

import pandas as pd


def descriptive_statistics(
    data: pd.DataFrame, columns: list[str] | None = None
) -> pd.DataFrame:
    """Summarize descriptive statistics for selected or all columns."""
    selected = data if columns is None else data.loc[:, columns]
    return selected.describe(include="all")


def frequency_summary(values: pd.Series, dropna: bool = False) -> pd.Series:
    """Return value frequencies, including missing values by default."""
    return values.value_counts(dropna=dropna, sort=True)