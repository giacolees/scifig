"""Export figures with scoped backend settings and stable metadata."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import matplotlib as mpl
from matplotlib.figure import Figure

_FORMATS = {"pdf", "svg", "png"}


def _validate_dpi(dpi: int) -> None:
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi <= 0:
        raise ValueError("dpi must be a positive integer")


def _validated_rc(rc: dict[str, Any] | None) -> dict[str, Any]:
    """Validate all overrides before touching Matplotlib's global rcParams."""
    result = {}
    for key, value in (rc or {}).items():
        if key == "backend" or key not in mpl.rcParams.validate:
            raise ValueError(f"Unsupported rc parameter: {key}")
        try:
            result[key] = mpl.rcParams.validate[key](value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid rc parameter {key}: {value!r}") from exc
    return result


def save_figure(
    figure: Figure, path: str | Path, rc: dict | None = None, dpi: int = 300, **kwargs: Any
) -> Path:
    """Save one PDF, SVG, or PNG and return its path.

    Export settings are scoped to the save, including delayed backend settings.
    """
    path = Path(path)
    fmt = path.suffix.lower().lstrip(".")
    if fmt not in _FORMATS:
        raise ValueError(f"Unsupported export format: {fmt or '(none)'}")
    _validate_dpi(dpi)
    overrides = _validated_rc(rc)
    path.parent.mkdir(parents=True, exist_ok=True)
    settings = {
        "pdf.fonttype": 42,
        "svg.fonttype": "path",
        "svg.hashsalt": "scifig",
        "savefig.bbox": None,
    }
    settings.update(overrides)
    metadata = (
        {"CreationDate": None, "ModDate": None}
        if fmt == "pdf"
        else ({"Date": None} if fmt == "svg" else {})
    )
    metadata.update(kwargs.pop("metadata", {}) or {})
    with mpl.rc_context(settings):
        # Converge constrained layout using one renderer, then freeze it while
        # each output backend draws. Restore the engine for subsequent edits.
        engine = figure.get_layout_engine()
        if engine is not None:
            previous = None
            for _ in range(8):
                figure.canvas.draw()
                current = tuple(value for ax in figure.axes for value in ax.get_position().bounds)
                if previous is not None and all(
                    abs(a - b) < 1e-10 for a, b in zip(current, previous, strict=True)
                ):
                    break
                previous = current
            figure.set_layout_engine("none")
        try:
            figure.savefig(path, format=fmt, dpi=dpi, metadata=metadata, **kwargs)
        finally:
            if engine is not None:
                figure.set_layout_engine(engine)
    return path


def export_figure(
    figure: Figure,
    directory: str | Path,
    stem: str = "figure",
    formats: Sequence[str] = ("pdf", "svg", "png"),
    rc: dict | None = None,
    dpi: int = 300,
) -> list[Path]:
    """Export all requested formats after validating the entire request."""
    if not isinstance(stem, str) or not stem or stem in {".", ".."} or "/" in stem or "\\" in stem:
        raise ValueError("stem must be a nonempty basename")
    if isinstance(formats, str) or not formats or any(fmt not in _FORMATS for fmt in formats):
        raise ValueError("formats must be a nonempty sequence of pdf, svg, or png")
    if len(formats) != len(set(formats)):
        raise ValueError("formats must not contain duplicates")
    _validate_dpi(dpi)
    _validated_rc(rc)
    return [save_figure(figure, Path(directory) / f"{stem}.{fmt}", rc, dpi) for fmt in formats]
