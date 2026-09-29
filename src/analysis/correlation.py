"""Correlation matrix utilities for numeric features."""

import pandas as pd


def correlation_matrix(
    data: pd.DataFrame,
    method: str = "pearson",
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Calculate a correlation matrix for selected numeric columns.

    Raises:
        ValueError: If the method is unsupported or no numeric columns exist.
    """
    if method not in {"pearson", "kendall", "spearman"}:
        raise ValueError("method must be 'pearson', 'kendall', or 'spearman'")

    selected = data if columns is None else data.loc[:, columns]
    numeric = selected.select_dtypes(include="number")
    if numeric.empty:
        raise ValueError("At least one numeric column is required")
    return numeric.corr(method=method)