"""Load supported tabular input without mutating caller data."""

import csv
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeAlias

import pandas as pd


class DataError(ValueError):
    """Input data cannot be interpreted as a valid figure table."""


DataSource: TypeAlias = pd.DataFrame | Mapping[str, Any] | list[dict[str, Any]] | str | Path


def load_data(data: DataSource) -> pd.DataFrame:
    """Load a table without silently skipping rows or coercing category identifiers.

    CSV/TSV cells stay strings until the semantic layer converts selected numeric
    fields. This preserves identifiers such as ``001`` and literal ``NA``.
    """
    try:
        if isinstance(data, pd.DataFrame):
            return data.copy(deep=True)
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.suffix.lower() not in {".csv", ".tsv"}:
                raise DataError("data file must be CSV or TSV")
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(
                    stream, delimiter="\t" if path.suffix.lower() == ".tsv" else ",", strict=True
                )
                header = next(reader, None)
                if not header or any(not name.strip() for name in header):
                    raise DataError("data file requires a nonempty header")
                if len(header) != len(set(header)):
                    raise DataError("data file has duplicate column names")
                rows = []
                for row in reader:
                    if len(row) != len(header):
                        raise DataError(
                            f"malformed data row ending at line {reader.line_num}: "
                            f"expected {len(header)} fields, got {len(row)}"
                        )
                    rows.append(row)
            return pd.DataFrame(rows, columns=header)
        if isinstance(data, (Mapping, list)):
            return pd.DataFrame(data).copy(deep=True)
        raise DataError("data must be a DataFrame, mapping, list of records, CSV or TSV path")
    except (OSError, ValueError, TypeError, csv.Error, UnicodeError) as exc:
        if isinstance(exc, DataError):
            raise
        raise DataError(f"cannot load data: {exc}") from exc
