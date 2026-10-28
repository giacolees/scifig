"""Reproducible, publication-oriented scientific figures.

Convenience functions and declarative specs use :func:`render` identically.
"""

from typing import Any

from scifig import templates as _templates  # noqa: F401 (register built-ins)
from scifig.core.data import DataError, DataSource
from scifig.core.registry import list_templates as _list_plot_templates
from scifig.core.registry import register_template
from scifig.core.specs import (
    AnnotationSpec,
    BoundsSpec,
    ExportSpec,
    FigureSpec,
    StyleSpec,
    load_spec,
)
from scifig.diagrams.rendering import DiagramResult
from scifig.diagrams.specs import DiagramSpec, EdgeSpec, GroupSpec, NodeSpec
from scifig.diagrams.templates import list_diagram_templates, load_diagram_template
from scifig.rendering.matplotlib import FigureResult, FigureWarning, render, validate
from scifig.styles import list_styles

__version__ = "0.2.0"
__all__ = [
    "AnnotationSpec",
    "BoundsSpec",
    "DataError",
    "ExportSpec",
    "DiagramSpec",
    "DiagramResult",
    "NodeSpec",
    "EdgeSpec",
    "GroupSpec",
    "FigureResult",
    "FigureSpec",
    "FigureWarning",
    "StyleSpec",
    "ablation",
    "architecture",
    "benchmark",
    "distribution",
    "heatmap",
    "learning_curve",
    "list_diagram_templates",
    "list_styles",
    "list_templates",
    "load_spec",
    "load_diagram_template",
    "register_template",
    "render",
    "validate",
]


def list_templates() -> list[str]:
    """List the scientific plot templates and the architecture diagram family."""
    return sorted([*_list_plot_templates(), "architecture"])


def architecture(
    nodes: dict[str, NodeSpec | dict[str, Any]],
    edges: list[EdgeSpec | dict[str, Any]] | None = None,
    **kwargs: Any,
) -> DiagramResult:
    """Draw nodes and connections with manual positions or optional Graphviz layout.

    Sizes and manual positions use nominal inches; the whole layout fits the
    requested canvas while typography retains its final point size.
    """
    return render(DiagramSpec(nodes=nodes, edges=[] if edges is None else edges, **kwargs))


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
