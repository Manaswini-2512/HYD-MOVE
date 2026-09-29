"""Utilities for loading local tabular data and GTFS ZIP feeds."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
from zipfile import ZipFile

from pandas.errors import EmptyDataError
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


GTFS_REQUIRED_FILES = (
    "agency.txt",
    "routes.txt",
    "stops.txt",
    "trips.txt",
    "stop_times.txt",
)
GTFS_OPTIONAL_FILES = (
    "calendar.txt",
    "calendar_dates.txt",
    "shapes.txt",
    "fare_attributes.txt",
    "fare_rules.txt",
    "frequencies.txt",
    "transfers.txt",
    "feed_info.txt",
    "translations.txt",
    "pathways.txt",
    "levels.txt",
    "attributions.txt",
)


@dataclass(frozen=True)
class GTFSFeed:
    """Tables and file-presence metadata read from a GTFS ZIP archive."""

    source_path: Path
    tables: dict[str, pd.DataFrame]
    available_files: tuple[str, ...]
    missing_required_files: tuple[str, ...]
    missing_optional_files: tuple[str, ...]


def _discover_gtfs_members(archive: ZipFile) -> dict[str, str]:
    """Map canonical GTFS TXT filenames to their archive member paths."""
    members: dict[str, str] = {}
    for member in archive.namelist():
        if member.endswith("/"):
            continue
        filename = PurePosixPath(member).name.lower()
        if not filename.endswith(".txt"):
            continue
        if filename in members:
            raise ValueError(f"GTFS archive contains duplicate filename: {filename}")
        members[filename] = member
    return members


def discover_gtfs_files(path: str | Path) -> dict[str, str]:
    """Inspect a ZIP archive and map GTFS TXT filenames to member paths.

    Nested archive directories are supported. Contents are not extracted.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"GTFS archive does not exist: {file_path}")
    with ZipFile(file_path) as archive:
        return _discover_gtfs_members(archive)


def validate_required_gtfs_files(available_files: Iterable[str]) -> tuple[str, ...]:
    """Return the required GTFS filenames absent from an archive listing."""
    present = {PurePosixPath(name).name.lower() for name in available_files}
    return tuple(name for name in GTFS_REQUIRED_FILES if name not in present)


def load_gtfs_zip(path: str | Path) -> GTFSFeed:
    """Read all TXT tables in a GTFS ZIP into string-valued DataFrames.

    Keeping fields as strings preserves identifiers and leading zeroes.
    Required and optional file absences are returned as metadata. The source
    archive is read directly without extraction or modification.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"GTFS archive does not exist: {file_path}")

    with ZipFile(file_path) as archive:
        members = _discover_gtfs_members(archive)
        tables: dict[str, pd.DataFrame] = {}
        for filename, member in sorted(members.items()):
            table_name = PurePosixPath(filename).stem
            with archive.open(member) as stream:
                try:
                    tables[table_name] = pd.read_csv(
                        stream, dtype=str, keep_default_na=False
                    )
                except EmptyDataError:
                    tables[table_name] = pd.DataFrame()

    available_files = tuple(sorted(members))
    missing_required = validate_required_gtfs_files(available_files)
    missing_optional = tuple(
        filename for filename in GTFS_OPTIONAL_FILES if filename not in members
    )
    return GTFSFeed(
        source_path=file_path,
        tables=tables,
        available_files=available_files,
        missing_required_files=missing_required,
        missing_optional_files=missing_optional,
    )