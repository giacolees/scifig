"""Semantic validation and statistical preparation of long-form data."""

import warnings

import numpy as np
import pandas as pd

from scifig.core.data import DataError
from scifig.core.specs import BoundsSpec, FigureSpec

_TYPES = {"learning_curve", "benchmark", "ablation", "distribution", "heatmap"}


def _category(frame: pd.DataFrame, column: str) -> None:
    """Normalize category identifiers without merging distinct values."""
    original = frame[column]
    if original.isna().any():
        raise DataError(f"{column}: missing category")
    converted = original.map(str)
    if converted.str.strip().eq("").any():
        raise DataError(f"{column}: missing category")
    # Distinct identifiers that stringify to the same name must not silently merge.
    identities = original.map(lambda x: (type(x).__name__, repr(x)))
    check = pd.DataFrame({"name": converted, "identity": identities})
    if check.groupby("name")["identity"].nunique().gt(1).any():
        raise DataError(f"{column}: category identifiers collide after conversion to strings")
    frame[column] = converted


def _numeric(frame: pd.DataFrame, column: str) -> None:
    """Convert one selected column to finite real numbers."""
    try:
        if frame[column].map(lambda x: isinstance(x, (bool, np.bool_))).any():
            raise ValueError("boolean is not numeric data")
        values = pd.to_numeric(frame[column], errors="raise")
        if np.iscomplexobj(values):
            raise ValueError("complex values are unsupported")
        values = values.astype(float)
        if not np.isfinite(values).all():
            raise ValueError("values must be finite and nonmissing")
        frame[column] = values
    except (ValueError, TypeError) as exc:
        raise DataError(f"{column}: expected finite numeric values ({exc})") from exc


def _check_order(order: list[str] | None, observed, name: str) -> None:
    """Require a complete, unique category ordering when supplied."""
    if order is not None and (len(order) != len(set(order)) or set(order) != set(observed)):
        raise DataError(f"{name} must contain each observed category exactly once")


def _process_impl(frame: pd.DataFrame, spec: FigureSpec) -> tuple[pd.DataFrame, list[str]]:
    """Validate and prepare a fresh frame and collect diagnostics."""
    if spec.type not in _TYPES:
        raise DataError(f"unknown figure type: {spec.type}")
    if frame.empty:
        raise DataError("data is empty")
    if not frame.columns.is_unique:
        raise DataError("data has duplicate column names")
    if spec.type in {"ablation", "distribution", "heatmap"} and spec.group is not None:
        raise DataError(f"group is unsupported for {spec.type}")
    if spec.group_order is not None and spec.group is None:
        raise DataError("group_order requires a group column")
    if spec.row_order is not None and spec.type != "heatmap":
        raise DataError("row_order is only supported for heatmap")
    if spec.type == "heatmap" and spec.value is None:
        raise DataError("heatmap requires a value column")
    if spec.type != "heatmap" and spec.value is not None:
        raise DataError("value is only supported for heatmap")
    if spec.color_limits is not None and spec.type != "heatmap":
        raise DataError("color_limits is only supported for heatmap")
    if spec.type in {"benchmark", "ablation"} and spec.yscale == "log":
        raise DataError("bars cannot use log scale because their zero baseline is undefined")
    if spec.type in {"distribution", "heatmap"}:
        if spec.uncertainty is not None:
            raise DataError(f"uncertainty is unsupported for {spec.type}")
        if spec.aggregate != "none":
            raise DataError(f"aggregation is unsupported for {spec.type}")
    if isinstance(spec.uncertainty, BoundsSpec) and spec.aggregate != "none":
        raise DataError("provided bounds cannot be combined with aggregation")
    if isinstance(spec.uncertainty, str) and spec.aggregate == "median":
        raise DataError("sample uncertainty requires a mean, not a median")
    if spec.type != "learning_curve" and spec.xscale == "log":
        raise DataError("categorical x axis cannot use log scale")
    if spec.type == "heatmap" and spec.yscale == "log":
        raise DataError("categorical y axis cannot use log scale")

    needed = [spec.x, spec.y]
    needed += [x for x in (spec.group, spec.value) if x is not None]
    if isinstance(spec.uncertainty, BoundsSpec):
        needed += [spec.uncertainty.lower, spec.uncertainty.upper]
    missing = [name for name in needed if name not in frame.columns]
    if missing:
        raise DataError(f"missing columns: {', '.join(missing)}")
    if len(set(needed)) != len(needed):
        raise DataError("figure roles must use distinct columns")
    if {"_lower", "_upper"} & set(frame.columns):
        raise DataError("data columns _lower and _upper are reserved for uncertainty")
    df = frame.copy(deep=True)
    category_columns = [] if spec.type == "learning_curve" else [spec.x]
    if spec.type == "heatmap":
        category_columns.append(spec.y)
    if spec.group is not None:
        category_columns.append(spec.group)
    for column in category_columns:
        _category(df, column)
    for column in needed:
        if column not in category_columns:
            _numeric(df, column)
    if spec.type != "learning_curve":
        _check_order(spec.order, df[spec.x].unique(), "order")
    elif spec.order is not None:
        raise DataError("order is only supported for categorical x axes")
    if spec.type == "heatmap":
        _check_order(spec.row_order, df[spec.y].unique(), "row_order")
    if spec.group is not None:
        _check_order(spec.group_order, df[spec.group].unique(), "group_order")

    for axis in ("x", "y"):
        column = getattr(spec, axis)
        if getattr(spec, f"{axis}scale") == "log" and (df[column] <= 0).any():
            raise DataError(f"{axis} values must be positive on a log scale")
        limits = getattr(spec, f"{axis}lim")
        if limits is not None and getattr(spec, f"{axis}scale") == "log" and limits[0] <= 0:
            raise DataError(f"{axis} limits must be positive on a log scale")

    keys = [spec.x] + ([spec.y] if spec.type == "heatmap" else [])
    if spec.group is not None:
        keys.append(spec.group)
    counts = df.groupby(keys, sort=True, observed=True).size()
    if spec.type == "benchmark" and spec.group is not None:
        if len(counts) != df[spec.x].nunique() * df[spec.group].nunique():
            raise DataError("grouped benchmark requires every x/group combination")
    if spec.type == "heatmap":
        if counts.gt(1).any() or len(counts) != df[spec.x].nunique() * df[spec.y].nunique():
            raise DataError(
                "heatmap requires exactly one value per cell in a complete rectangular grid"
            )
    elif spec.type != "distribution":
        if isinstance(spec.uncertainty, BoundsSpec):
            if counts.gt(1).any():
                raise DataError("provided bounds require one row per cell")
            lower, upper = spec.uncertainty.lower, spec.uncertainty.upper
            if ((df[lower] > df[spec.y]) | (df[spec.y] > df[upper])).any():
                raise DataError("bounds must satisfy lower <= y <= upper")
            df["_lower"], df["_upper"] = df[lower], df[upper]
        elif isinstance(spec.uncertainty, str):
            if counts.lt(2).any():
                raise DataError("sample uncertainty requires at least two observations per cell")
            grouped = df.groupby(keys, sort=True, observed=True)[spec.y]
            means, std, n = grouped.mean(), grouped.std(), grouped.count()
            error = std if spec.uncertainty == "std" else std / np.sqrt(n)
            if spec.uncertainty == "ci95":
                error = error * 1.96
            df = means.rename(spec.y).to_frame()
            df["_lower"], df["_upper"] = means - error, means + error
            df = df.reset_index()
        elif spec.aggregate != "none":
            grouped = df.groupby(keys, sort=True, observed=True, as_index=False)[spec.y]
            df = grouped.mean() if spec.aggregate == "mean" else grouped.median()
        elif counts.gt(1).any():
            raise DataError("duplicate summary cells require explicit aggregation or uncertainty")

    numeric_output = [spec.y] if spec.type != "heatmap" else [spec.value]
    numeric_output += [c for c in ("_lower", "_upper") if c in df.columns]
    if not all(np.isfinite(df[c]).all() for c in numeric_output):
        raise DataError("aggregation or uncertainty produced nonfinite values")
    if spec.yscale == "log" and "_lower" in df and (df["_lower"] <= 0).any():
        raise DataError("uncertainty bounds must be positive on a log scale")

    diagnostics = []
    if isinstance(spec.uncertainty, str):
        diagnostics.append(
            "sample uncertainty assumes comparable independent observations; "
            "repeated measurements of the same unit may not be independent"
        )
    if spec.uncertainty == "ci95":
        diagnostics.append("ci95 uses a normal approximation")
    if spec.color_limits is not None:
        values = df[spec.value]
        if (values < spec.color_limits[0]).any() or (values > spec.color_limits[1]).any():
            diagnostics.append("color limits saturate heatmap values outside the specified range")
    for axis in ("x", "y"):
        limit = getattr(spec, f"{axis}lim")
        column = getattr(spec, axis)
        if limit is not None and column not in category_columns:
            values = df[column]
            if axis == "y" and "_lower" in df:
                values = pd.concat([values, df["_lower"], df["_upper"]])
            if (values < limit[0]).any() or (values > limit[1]).any():
                diagnostics.append(f"{axis} limits clip data or uncertainty")
        elif limit is not None and column in category_columns:
            count = df[column].nunique()
            start, stop = (0, count) if spec.type == "heatmap" else (-0.4, count - 0.6)
            if limit[0] > start or limit[1] < stop:
                diagnostics.append(f"{axis} limits may hide categorical marks")
    if (
        spec.type in {"benchmark", "ablation"}
        and spec.ylim
        and not (spec.ylim[0] <= 0 <= spec.ylim[1])
    ):
        diagnostics.append("bar axis excludes zero and may exaggerate differences")
    if spec.require_labels:
        required = {"x", "y"} | ({"colorbar"} if spec.type == "heatmap" else set())
        if any(not spec.labels.get(key, "").strip() for key in required):
            raise DataError(f"required labels missing: {sorted(required)}")
    if spec.require_units:
        required = {"value"} if spec.type == "heatmap" else {"y"}
        if spec.type == "learning_curve":
            required.add("x")
        if any(not spec.units.get(key, "").strip() for key in required):
            raise DataError(f"required units missing: {sorted(required)}")
    return df, diagnostics


def _process(frame: pd.DataFrame, spec: FigureSpec) -> tuple[pd.DataFrame, list[str]]:
    """Convert numerical overflow to an actionable validation error."""
    try:
        with warnings.catch_warnings(), np.errstate(over="raise", invalid="raise"):
            warnings.simplefilter("error", RuntimeWarning)
            return _process_impl(frame, spec)
    except (FloatingPointError, RuntimeWarning) as exc:
        raise DataError("aggregation or uncertainty produced nonfinite values") from exc


def validate_data(frame: pd.DataFrame, spec: FigureSpec) -> list[str]:
    """Raise DataError for invalid data; return nonfatal diagnostics."""
    return _process(frame, spec)[1]


def prepare_data(frame: pd.DataFrame, spec: FigureSpec) -> pd.DataFrame:
    """Return normalized and explicitly aggregated data without modifying input."""
    return _process(frame, spec)[0]
