"""Utilities for loading tabular data from local files."""

from pathlib import Path

import pandas as pd


def load_table(path: str | Path) -> pd.DataFrame:
    """Load a CSV or TSV file into a DataFrame.

    Args:
        path: Path to a local CSV or TSV file.

    Returns:
        The file contents as a pandas DataFrame.

    Raises:
        FileNotFoundError: If the path does not point to an existing file.
        ValueError: If the file extension is not supported.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Dataset file does not exist: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix == ".tsv":
        return pd.read_csv(file_path, sep="\t")
    raise ValueError(f"Unsupported tabular file type: {suffix or '(no extension)'}")