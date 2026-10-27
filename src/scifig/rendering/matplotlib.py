"""One shared pipeline for Python, YAML, CLI, and agent-created specifications."""

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib as mpl
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.legend import Legend

from scifig.core.data import load_data
from scifig.core.registry import get_data_family, get_template
from scifig.core.specs import FigureSpec
from scifig.diagrams.specs import DiagramSpec
from scifig.rendering.export import export_figure, save_figure
from scifig.styles import ResolvedStyle, resolve_style
from scifig.validation.semantic import prepare_data, validate_data
from scifig.validation.visual import check_visual

if TYPE_CHECKING:
    from scifig.diagrams.rendering import DiagramResult


class FigureWarning(UserWarning):
    """A nonfatal scientific caveat or visual issue requiring human review."""


@dataclass
class FigureResult:
    """Editable native artists plus the specification and review diagnostics."""

    figure: Figure
    ax: Axes
    spec: FigureSpec
    style: ResolvedStyle
    diagnostics: list[str] = field(default_factory=list)

    @property
    def axes(self) -> list[Axes]:
        """All native axes, including a heatmap's colorbar axes."""
        return self.figure.axes

    def savefig(self, path: str | Path, *, dpi: int | None = None, **kwargs: Any) -> Path:
        """Save PDF/SVG/PNG while restoring the figure's scoped backend settings."""
        return save_figure(
            self.figure,
            path,
            rc=self.style.rc,
            dpi=dpi if dpi is not None else self.spec.export.dpi,
            **kwargs,
        )

    def export(
        self,
        directory: str | Path | None = None,
        *,
        stem: str | None = None,
        formats: tuple[str, ...] | list[str] | None = None,
        dpi: int | None = None,
    ) -> list[Path]:
        """Export every requested format using specification defaults."""
        config = self.spec.export
        return export_figure(
            self.figure,
            directory if directory is not None else config.directory,
            stem=stem if stem is not None else config.stem,
            formats=tuple(formats) if formats is not None else tuple(config.formats),
            rc=self.style.rc,
            dpi=dpi if dpi is not None else config.dpi,
        )


def _prepare(spec: FigureSpec, data: Any = None) -> tuple[pd.DataFrame, list[str], ResolvedStyle]:
    family = get_data_family(spec.type)
    contract = spec.model_copy(update={"type": family})
    if data is None and spec.data is None:
        raise ValueError("Provide data as a table or set the specification's data path.")
    frame = load_data(data if data is not None else spec.data)
    diagnostics = validate_data(frame, contract)
    prepared = prepare_data(frame, contract)
    style = resolve_style(spec.style)
    outside_locations = {
        "outside upper left",
        "outside upper center",
        "outside upper right",
        "outside lower left",
        "outside lower center",
        "outside lower right",
        "outside left upper",
        "outside left lower",
        "outside right upper",
        "outside right lower",
    }
    if spec.legend_loc not in Legend.codes and spec.legend_loc not in outside_locations:
        raise ValueError(f"Unknown legend_loc {spec.legend_loc!r}; use a Matplotlib location name.")
    if spec.cmap not in mpl.colormaps:
        raise ValueError(f"Unknown colormap: {spec.cmap!r}")
    if family != "heatmap":
        if family in {"ablation", "distribution"}:
            names = sorted(prepared[spec.x].unique())
        elif spec.group:
            names = sorted(prepared[spec.group].unique())
        else:
            names = [spec.y]
        style.color_map(names)
    return prepared, diagnostics, style


def _capture_messages(records: list[warnings.WarningMessage], diagnostics: list[str]) -> list[str]:
    return list(dict.fromkeys([*diagnostics, *(str(record.message) for record in records)]))


def validate(spec: FigureSpec | DiagramSpec | dict[str, Any], data: Any = None) -> list[str]:
    """Validate data and configuration without rendering; return scientific caveats."""
    spec = _coerce_spec(spec)
    if isinstance(spec, DiagramSpec):
        from scifig.diagrams.rendering import validate_diagram_config

        if data is not None:
            raise ValueError("Diagrams define nodes and edges; tabular data is unsupported.")
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            diagnostics = validate_diagram_config(spec)
        return _capture_messages(records, diagnostics)
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        _, diagnostics, _ = _prepare(spec, data)
    return _capture_messages(records, diagnostics)


def _axis_label(spec: FigureSpec, axis: str) -> str:
    label = spec.labels.get(axis, getattr(spec, axis))
    if unit := spec.units.get(axis):
        label += f" ({unit})"
    return label


def _coerce_spec(spec: FigureSpec | DiagramSpec | dict[str, Any]) -> FigureSpec | DiagramSpec:
    if isinstance(spec, (FigureSpec, DiagramSpec)):
        return spec
    if isinstance(spec, dict) and (spec.get("type") == "architecture" or "nodes" in spec):
        return DiagramSpec.model_validate(spec)
    return FigureSpec.model_validate(spec)


def render(
    spec: FigureSpec | DiagramSpec | dict[str, Any], data: Any = None
) -> "FigureResult | DiagramResult":
    """Render a validated spec headlessly without changing the caller's rcParams."""
    spec = _coerce_spec(spec)
    if isinstance(spec, DiagramSpec):
        from scifig.diagrams.rendering import render_diagram

        if data is not None:
            raise ValueError("Diagrams define nodes and edges; tabular data is unsupported.")
        return render_diagram(spec)
    # A copy protects caller configuration against edits through the result.
    spec = spec.model_copy(deep=True)
    if isinstance(data, (str, Path)):
        spec.data = Path(data).resolve()
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        prepared, diagnostics, style = _prepare(spec, data)
        with mpl.rc_context(style.rc):
            figure = Figure(figsize=style.figsize, layout="constrained")
            FigureCanvasAgg(figure)
            ax = figure.add_subplot()
            ax.set_xscale(spec.xscale)
            ax.set_yscale(spec.yscale)
            get_template(spec.type)(ax, prepared, spec, style)
            ax.set_xlabel(_axis_label(spec, "x"))
            ax.set_ylabel(_axis_label(spec, "y"))
            ax.set_title(spec.labels.get("title", ""))
            if spec.xlim is not None:
                ax.set_xlim(spec.xlim)
            if spec.ylim is not None:
                ax.set_ylim(spec.ylim)
            handles, labels = ax.get_legend_handles_labels()
            if spec.legend and handles and spec.group is not None:
                legend_target = figure if spec.legend_loc.startswith("outside ") else ax
                legend_target.legend(
                    handles,
                    labels,
                    loc=spec.legend_loc,
                    title=spec.labels.get("legend"),
                    ncols=spec.legend_columns,
                )
            for annotation in spec.annotations:
                ax.annotate(
                    annotation.text,
                    xy=(annotation.x, annotation.y),
                    xycoords=annotation.coords,
                )
            diagnostics.extend(check_visual(figure))
    diagnostics = _capture_messages(records, diagnostics)
    for message in diagnostics:
        warnings.warn(message, FigureWarning, stacklevel=2)
    return FigureResult(figure, ax, spec, style, diagnostics)
