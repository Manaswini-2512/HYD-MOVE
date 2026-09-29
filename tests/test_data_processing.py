"""Tests for foundational data loading, cleaning, and analysis helpers."""

from pathlib import Path

import pandas as pd
import pytest

from src.analysis.outliers import detect_iqr_outliers
from src.data.cleaning import handle_missing_values, remove_duplicates
from src.data.ingestion import load_table


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_SAMPLE = PROJECT_ROOT / "data" / "raw" / "synthetic_traffic_sample.csv"


def test_load_synthetic_tabular_dataset() -> None:
    """The documented synthetic fixture loads with its expected columns."""
    data = load_table(SYNTHETIC_SAMPLE)

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 4
    assert {"timestamp", "location", "traffic_volume"}.issubset(data.columns)


def test_load_table_rejects_missing_file(tmp_path: Path) -> None:
    """A missing dataset path raises a useful filesystem error."""
    with pytest.raises(FileNotFoundError):
        load_table(tmp_path / "missing.csv")


def test_remove_duplicates_preserves_input() -> None:
    """Duplicate rows are removed without mutating the input frame."""
    data = pd.DataFrame({"value": [1, 1, 2]})

    cleaned = remove_duplicates(data)

    assert len(cleaned) == 2
    assert len(data) == 3


def test_handle_missing_values_drop_and_fill() -> None:
    """Missing-value strategies return cleaned copies."""
    data = pd.DataFrame({"volume": [10.0, None], "location": ["A", "B"]})

    dropped = handle_missing_values(data)
    filled = handle_missing_values(data, strategy="fill", fill_value=0)

    assert len(dropped) == 1
    assert filled["volume"].isna().sum() == 0
    assert data["volume"].isna().sum() == 1


def test_detect_iqr_outlier() -> None:
    """The IQR rule flags an extreme value and leaves inliers unmarked."""
    values = pd.Series([10, 11, 12, 13, 14, 100])

    result = detect_iqr_outliers(values)

    assert result.tolist() == [False, False, False, False, False, True]