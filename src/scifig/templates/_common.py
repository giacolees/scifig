"""Small shared helpers for category order and uncertainty endpoints."""

import numpy as np
import pandas as pd


def categories(frame: pd.DataFrame, column: str, order: list[str] | None = None) -> list[str]:
    """Resolve deterministic category ordering (already validated)."""
    return order if order is not None else sorted(frame[column].astype(str).unique())


def errors(frame: pd.DataFrame, y: str) -> np.ndarray | None:
    """Return asymmetric error-bar lengths when absolute endpoints are available."""
    if "_lower" not in frame:
        return None
    return np.stack([frame[y] - frame["_lower"], frame["_upper"] - frame[y]])
