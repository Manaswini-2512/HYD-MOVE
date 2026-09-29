"""Basic data-quality checks and cleaning helpers."""

from collections.abc import Sequence

import pandas as pd


def missing_value_counts(data: pd.DataFrame) -> pd.Series:
    """Return the number of missing values in each column."""
    return data.isna().sum()


def find_duplicates(
    data: pd.DataFrame, subset: Sequence[str] | None = None
) -> pd.Series:
    """Return a Boolean mask identifying duplicate rows."""
    return data.duplicated(subset=subset, keep="first")


def remove_duplicates(
    data: pd.DataFrame, subset: Sequence[str] | None = None
) -> pd.DataFrame:
    """Return a copy of the data with duplicate rows removed."""
    return data.drop_duplicates(subset=subset).copy()


def handle_missing_values(
    data: pd.DataFrame,
    strategy: str = "drop",
    fill_value: object | None = None,
) -> pd.DataFrame:
    """Return a copy with missing values dropped or filled.

    Args:
        data: DataFrame to process; the input is never modified.
        strategy: Either ``"drop"`` to remove rows with missing values or
            ``"fill"`` to replace missing values with ``fill_value``.
        fill_value: Scalar used when ``strategy="fill"``.

    Raises:
        ValueError: If the strategy is unsupported or a fill value is absent.
    """
    if strategy == "drop":
        return data.dropna().copy()
    if strategy == "fill":
        if fill_value is None:
            raise ValueError("fill_value is required when strategy='fill'")
        return data.fillna(fill_value)
    raise ValueError("strategy must be either 'drop' or 'fill'")


def validate_dataframe(
    data: pd.DataFrame, required_columns: Sequence[str] = ()
) -> None:
    """Validate that a DataFrame has rows and the required columns.

    Raises:
        ValueError: If the DataFrame is empty or required columns are missing.
    """
    if data.empty:
        raise ValueError("DataFrame must contain at least one row")

    missing_columns = set(required_columns).difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"DataFrame is missing required columns: {missing}")