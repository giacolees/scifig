"""Reproducible, publication-oriented scientific figures.

Convenience functions and declarative specs use :func:`render` identically.
"""

from typing import Any

from scifig import templates as _templates  # noqa: F401 (register built-ins)
from scifig.core.data import DataError, DataSource
from scifig.core.registry import list_templates, register_template
from scifig.core.specs import (
    AnnotationSpec,
    BoundsSpec,
    ExportSpec,
    FigureSpec,
    StyleSpec,
    load_spec,
)
from scifig.rendering.matplotlib import FigureResult, FigureWarning, render, validate
from scifig.styles import list_styles

__version__ = "0.1.0"
__all__ = [
    "AnnotationSpec",
    "BoundsSpec",
    "DataError",
    "ExportSpec",
    "FigureResult",
    "FigureSpec",
    "FigureWarning",
    "StyleSpec",
    "ablation",
    "benchmark",
    "distribution",
    "heatmap",
    "learning_curve",
    "list_styles",
    "list_templates",
    "load_spec",
    "register_template",
    "render",
    "validate",
]


def _plot(kind: str, data: DataSource, x: str, y: str, **kwargs: Any) -> FigureResult:
    spec = FigureSpec(type=kind, x=x, y=y, **kwargs)
    return render(spec, data)


def learning_curve(
    data: DataSource, x: str, y: str, group: str | None = None, **kwargs: Any
) -> FigureResult:
    """Plot numeric trajectories; uncertainty explicitly requests mean and bands.

    ``std`` uses sample SD; ``sem`` uses SD/sqrt(n); ``ci95`` uses 1.96*SEM.
    Alternatively provide ``uncertainty={"lower": "lo", "upper": "hi"}``.
    All other keyword arguments are fields of :class:`FigureSpec`.
    """
    return _plot("learning_curve", data, x, y, group=group, **kwargs)


def benchmark(
    data: DataSource, x: str, y: str, group: str | None = None, **kwargs: Any
) -> FigureResult:
    """Compare categorical benchmarks using grouped bars and optional uncertainty."""
    return _plot("benchmark", data, x, y, group=group, **kwargs)


def ablation(data: DataSource, x: str, y: str, **kwargs: Any) -> FigureResult:
    """Compare named ablation settings in a caller-specified or sorted order."""
    return _plot("ablation", data, x, y, **kwargs)


def distribution(data: DataSource, x: str, y: str, **kwargs: Any) -> FigureResult:
    """Show raw observations over Tukey boxplots; whiskers are not confidence intervals."""
    return _plot("distribution", data, x, y, **kwargs)


def heatmap(data: DataSource, x: str, y: str, value: str, **kwargs: Any) -> FigureResult:
    """Plot one numeric value per cell of a complete rectangular categorical grid."""
    return _plot("heatmap", data, x, y, value=value, **kwargs)
