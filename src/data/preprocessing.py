"""Small, non-destructive feature preparation utilities."""

from collections.abc import Sequence

import pandas as pd


def prepare_features(
    data: pd.DataFrame,
    datetime_columns: Sequence[str] = (),
    categorical_columns: Sequence[str] = (),
    drop_columns: Sequence[str] = (),
) -> pd.DataFrame:
    """Return a prepared copy with selected types converted and columns dropped.

    Invalid datetime values are coerced to ``NaT`` for explicit downstream
    missing-value handling. The input DataFrame is not modified.
    """
    prepared = data.drop(columns=list(drop_columns)).copy()
    for column in datetime_columns:
        prepared[column] = pd.to_datetime(prepared[column], errors="coerce")
    for column in categorical_columns:
        prepared[column] = prepared[column].astype("category")
    return prepared