"""Render semantic diagrams as editable Matplotlib vector artists."""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import to_rgb
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as ArtistPath

from scifig.diagrams._appearance import EDGE_STYLES
from scifig.diagrams.ir import CanonicalDiagram
from scifig.diagrams.layout import DiagramGeometry, EdgeGeometry
from scifig.diagrams.pipeline import ResolvedPresentation
from scifig.diagrams.specs import DiagramSpec
from scifig.diagrams.validation import check_diagram_visual  # noqa: F401 (compatibility)
from scifig.rendering.export import export_figure, save_figure
from scifig.styles import ResolvedStyle


@dataclass
class DiagramResult:
    """Editable diagram artists with the semantic spec and recorded layout."""

    figure: Figure
    ax: Axes
    spec: DiagramSpec
    style: ResolvedStyle
    layout: DiagramGeometry
    diagram: CanonicalDiagram | None = field(default=None, kw_only=True)
    diagnostics: list[str] = field(default_factory=list)
    node_artists: dict[str, FancyBboxPatch] = field(default_factory=dict)
    edge_artists: list[FancyArrowPatch] = field(default_factory=list)
    group_artists: dict[str, FancyBboxPatch] = field(default_factory=dict)

    @property
    def axes(self) -> list[Axes]:
        """Return the native Matplotlib axes."""
        return self.figure.axes

    def savefig(self, path: str | Path, *, dpi: int | None = None, **kwargs: Any) -> Path:
        """Save PDF, SVG or PNG through the common scoped exporter."""
        return save_figure(
            self.figure,
            path,
            self.style.rc,
            dpi=self.spec.export.dpi if dpi is None else dpi,
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
        """Export requested formats using the same defaults as scientific plots."""
        config = self.spec.export
        return export_figure(
            self.figure,
            directory if directory is not None else config.directory,
            stem=config.stem if stem is None else stem,
            formats=tuple(config.formats) if formats is None else formats,
            rc=self.style.rc,
            dpi=config.dpi if dpi is None else dpi,
        )

    def save_layout(self, path: str | Path) -> Path:
        """Record geometry, source spec and renderer versions as a JSON sidecar.

        The sidecar documents the actual layout; it is not an alternate input
        format. Keep the YAML/Python source and the recorded Graphviz version.
        """
        from scifig import __version__

        path = Path(path)
        if path.suffix.lower() != ".json":
            raise ValueError("Layout sidecar must have a .json extension.")
        saved_spec = self.spec.model_dump(mode="json")
        saved_spec["export"]["directory"] = os.path.relpath(self.spec.export.directory, path.parent)
        payload = {
            "schema_version": 1,
            **asdict(self.layout),
            "figure_size_inches": list(self.figure.get_size_inches()),
            "matplotlib_version": mpl.__version__,
            "scifig_version": __version__,
            "spec": saved_spec,
        }
        serialized = json.dumps(
            payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized + "\n", encoding="utf-8")
        return path


def validate_diagram_config(spec: DiagramSpec) -> list[str]:
    """Validate a spec without running a layout engine (compatibility entry point)."""
    from scifig.diagrams.pipeline import prepare_diagram

    return prepare_diagram(spec).diagnostics


def _path(edge: EdgeGeometry) -> ArtistPath:
    points = list(edge.points)
    codes = [ArtistPath.MOVETO] + [ArtistPath.CURVE4 if edge.curved else ArtistPath.LINETO] * (
        len(points) - 1
    )
    if edge.end_point is not None:
        points.append(edge.end_point)
        codes.append(ArtistPath.LINETO)
    return ArtistPath(points, codes)


def _wrapped_label(text: str, width: float, font: FontProperties, renderer: Any) -> str:
    """Wrap at word boundaries without changing quantitative or mathematical content."""
    if "$" in text:
        return text  # Do not break mathtext syntax across lines.
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}" if current else word
            pixels = renderer.get_text_width_height_descent(candidate, font, ismath=False)[0]
            if current and pixels > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return "\n".join(lines)


def _draw(
    result: DiagramResult, diagram: CanonicalDiagram, presentation: ResolvedPresentation
) -> None:
    geometry, ax = result.layout, result.ax
    colors = presentation.node_colors
    appearance = presentation.appearance
    base_size = float(result.style.rc["font.size"])
    for group_id, group in diagram.groups.items():
        x0, y0, x1, y1 = geometry.groups[group_id].bounds
        patch = FancyBboxPatch(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            boxstyle="round,pad=0,rounding_size=5",
            facecolor=appearance.group_fill,
            edgecolor=appearance.group_border,
            linewidth=appearance.group_linewidth,
            linestyle="--" if group.role == "training" else "-",
            zorder=0,
            gid=f"group:{group_id}",
        )
        ax.add_patch(patch)
        result.group_artists[group_id] = patch
        ax.text(
            x0 + 6,
            y1 - 5,
            diagram.presentation.group_labels[group_id],
            ha="left",
            va="top",
            fontsize=base_size * 0.9,
            color=appearance.secondary_text,
            zorder=4,
            gid=f"group-label:{group_id}",
        )
    for i, (edge, route) in enumerate(zip(diagram.edges, geometry.edges, strict=True)):
        arrow = FancyArrowPatch(
            path=_path(route),
            arrowstyle="-|>",
            mutation_scale=appearance.arrow_size,
            linewidth=appearance.edge_linewidth,
            color=appearance.edge_color,
            linestyle=EDGE_STYLES[edge.kind],
            zorder=1,
            clip_on=False,
            gid=f"edge:{i}",
        )
        ax.add_patch(arrow)
        result.edge_artists.append(arrow)
        label = diagram.presentation.edge_labels[i]
        if label:
            position = route.label_position or tuple(np.mean(route.points, axis=0))
            ax.annotate(
                label,
                xy=position,
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=base_size * 0.85,
                zorder=4,
                bbox={"facecolor": appearance.label_background, "edgecolor": "none", "pad": 1},
                gid=f"edge-label:{i}",
            )
    # Compute physical available text width after equal-aspect axes adjustment.
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    font = FontProperties(family=result.style.rc["font.family"], size=base_size)
    for node_id, node in diagram.nodes.items():
        box = geometry.nodes[node_id]
        x, y = box.center
        w, h = box.size
        rgb = np.array(to_rgb(colors[node_id]))
        face = tuple(appearance.node_tint * rgb + (1 - appearance.node_tint))
        patch = FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=3",
            facecolor=face,
            edgecolor=colors[node_id],
            linewidth=appearance.node_linewidth,
            linestyle="--" if node.frozen else "-",
            zorder=3,
            gid=f"node:{node_id}",
        )
        ax.add_patch(patch)
        result.node_artists[node_id] = patch
        pixel_width = (
            ax.transData.transform((x + w / 2, y))[0] - ax.transData.transform((x - w / 2, y))[0]
        )
        label = _wrapped_label(
            diagram.presentation.node_labels[node_id], max(1, pixel_width - 10), font, renderer
        )
        details = []
        if node.shape is not None:
            details.append(" × ".join(map(str, node.shape)) if node.shape else "scalar")
        if node.frozen:
            details.append("frozen")
        if details:
            detail_size = max(6, base_size * 0.8)
            label_height = base_size * 1.2 * (label.count("\n") + 1)
            detail_height = detail_size * 1.2 * len(details)
            ax.annotate(
                label,
                xy=(x, y),
                xytext=(0, (detail_height + 2) / 2),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=base_size,
                zorder=4,
                gid=f"node-label:{node_id}",
            )
            ax.annotate(
                "\n".join(details),
                xy=(x, y),
                xytext=(0, -(label_height + 2) / 2),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=detail_size,
                color=appearance.secondary_text,
                zorder=4,
                gid=f"node-detail:{node_id}",
            )
        else:
            ax.text(
                x,
                y,
                label,
                ha="center",
                va="center",
                fontsize=base_size,
                zorder=4,
                gid=f"node-label:{node_id}",
            )
    kinds = [kind for kind in EDGE_STYLES if any(e.kind == kind for e in diagram.edges)]
    if any(kind != "data" for kind in kinds):
        handles = [
            Line2D(
                [0],
                [0],
                color=appearance.edge_color,
                linestyle=EDGE_STYLES[kind],
                linewidth=appearance.edge_linewidth,
                label=kind.capitalize(),
            )
            for kind in kinds
        ]
        ax.figure.legend(
            handles=handles,
            loc="lower center",
            ncols=len(kinds),
            frameon=False,
            fontsize=base_size * 0.85,
        )


def render_geometry(
    spec: DiagramSpec,
    diagram: CanonicalDiagram,
    geometry: DiagramGeometry,
    presentation: ResolvedPresentation,
) -> DiagramResult:
    """Draw canonical content and validated point geometry with resolved visual tokens.

    ``spec`` is retained only for result/export compatibility. Pipeline callers
    validate geometry before entering this implementation.
    """
    style = presentation.style
    title = diagram.presentation.title
    with mpl.rc_context(style.rc):
        figure = Figure(figsize=style.figsize, layout="none")
        FigureCanvasAgg(figure)
        ax = figure.add_axes((0.035, 0.12, 0.93, 0.74 if title else 0.83))
        x0, y0, x1, y1 = geometry.bounds
        pad = max(10, min(x1 - x0, y1 - y0) * 0.08)
        ax.set(xlim=(x0 - pad, x1 + pad), ylim=(y0 - pad, y1 + pad), aspect="equal")
        ax.set_axis_off()
        if title:
            figure.suptitle(title, y=0.97, fontsize=style.rc["axes.titlesize"])
        result = DiagramResult(figure, ax, spec, style, geometry, diagram=diagram)
        _draw(result, diagram, presentation)
    return result


def render_diagram(spec: DiagramSpec, *, geometry: DiagramGeometry | None = None) -> DiagramResult:
    """Render a spec; optionally use supplied geometry without invoking an engine."""
    from scifig.diagrams.pipeline import render_diagram as run_pipeline

    return run_pipeline(spec, geometry=geometry)
