"""Render semantic diagrams as editable Matplotlib vector artists."""

import json
import os
import warnings
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

from scifig.diagrams.layout import DiagramGeometry, EdgeGeometry, layout_diagram
from scifig.diagrams.specs import DiagramSpec, validate_diagram
from scifig.rendering.export import export_figure, save_figure
from scifig.rendering.matplotlib import FigureWarning
from scifig.styles import ResolvedStyle, resolve_style
from scifig.validation.visual import check_visual

_ROLE_COLORS = {
    "input": "#0072B2",
    "output": "#0072B2",
    "module": "#555555",
    "data": "#009E73",
    "store": "#009E73",
    "loss": "#D55E00",
    "operation": "#555555",
}
_EDGE_STYLES = {"data": "-", "gradient": "--", "control": ":", "feedback": "-."}


@dataclass
class DiagramResult:
    """Editable diagram artists with the semantic spec and recorded layout."""

    figure: Figure
    ax: Axes
    spec: DiagramSpec
    style: ResolvedStyle
    layout: DiagramGeometry
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


def _node_colors(spec: DiagramSpec, style: ResolvedStyle) -> dict[str, str]:
    if style.colors:
        return style.color_map(list(spec.nodes))
    return {
        key: "#555555" if style.palette == "grayscale" else _ROLE_COLORS[node.role]
        for key, node in spec.nodes.items()
    }


def validate_diagram_config(spec: DiagramSpec) -> list[str]:
    """Validate semantics and visual tokens without running a layout subprocess."""
    # Revalidate mutable models so later edits cannot bypass structural checks.
    checked = DiagramSpec.model_validate(spec.model_dump())
    style = resolve_style(checked.style)
    _node_colors(checked, style)
    return validate_diagram(checked)


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


def _draw(result: DiagramResult) -> None:
    spec, geometry, ax = result.spec, result.layout, result.ax
    colors = _node_colors(spec, result.style)
    base_size = float(result.style.rc["font.size"])
    for group_id, group in spec.groups.items():
        x0, y0, x1, y1 = geometry.groups[group_id].bounds
        patch = FancyBboxPatch(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            boxstyle="round,pad=0,rounding_size=5",
            facecolor="#F7F8FA",
            edgecolor="#888888",
            linewidth=0.7,
            linestyle="--" if group.role == "training" else "-",
            zorder=0,
            gid=f"group:{group_id}",
        )
        ax.add_patch(patch)
        result.group_artists[group_id] = patch
        ax.text(
            x0 + 6,
            y1 - 5,
            group.label,
            ha="left",
            va="top",
            fontsize=base_size * 0.9,
            color="#555555",
            zorder=4,
            gid=f"group-label:{group_id}",
        )
    for i, (edge, route) in enumerate(zip(spec.edges, geometry.edges, strict=True)):
        arrow = FancyArrowPatch(
            path=_path(route),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=0.9,
            color="#444444",
            linestyle=_EDGE_STYLES[edge.kind],
            zorder=1,
            clip_on=False,
            gid=f"edge:{i}",
        )
        ax.add_patch(arrow)
        result.edge_artists.append(arrow)
        if edge.label:
            position = route.label_position or tuple(np.mean(route.points, axis=0))
            ax.annotate(
                edge.label,
                xy=position,
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=base_size * 0.85,
                zorder=4,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
                gid=f"edge-label:{i}",
            )
    # Compute physical available text width after equal-aspect axes adjustment.
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    font = FontProperties(family=result.style.rc["font.family"], size=base_size)
    for node_id, node in spec.nodes.items():
        box = geometry.nodes[node_id]
        x, y = box.center
        w, h = box.size
        rgb = np.array(to_rgb(colors[node_id]))
        face = tuple(0.08 * rgb + 0.92)
        patch = FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=3",
            facecolor=face,
            edgecolor=colors[node_id],
            linewidth=0.8,
            linestyle="--" if node.frozen else "-",
            zorder=3,
            gid=f"node:{node_id}",
        )
        ax.add_patch(patch)
        result.node_artists[node_id] = patch
        pixel_width = (
            ax.transData.transform((x + w / 2, y))[0] - ax.transData.transform((x - w / 2, y))[0]
        )
        label = _wrapped_label(node.label, max(1, pixel_width - 10), font, renderer)
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
                color="#555555",
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
    kinds = [kind for kind in _EDGE_STYLES if any(e.kind == kind for e in spec.edges)]
    if any(kind != "data" for kind in kinds):
        handles = [
            Line2D(
                [0],
                [0],
                color="#444444",
                linestyle=_EDGE_STYLES[kind],
                linewidth=0.9,
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


def _samples(edge: EdgeGeometry) -> np.ndarray:
    if not edge.curved:
        return np.concatenate(
            [np.linspace(a, b, 24) for a, b in zip(edge.points, edge.points[1:], strict=False)]
        )
    samples = []
    t = np.linspace(0, 1, 24)[:, None]
    for i in range(0, len(edge.points) - 1, 3):
        a, b, c, d = np.asarray(edge.points[i : i + 4])
        samples.append(
            (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t**2 * c + t**3 * d
        )
    return np.concatenate(samples)


def check_diagram_visual(result: DiagramResult) -> list[str]:
    """Check rendered labels, node overlaps and routes through unrelated nodes.

    These are geometry heuristics; they do not verify architecture semantics.
    """
    diagnostics = check_visual(result.figure)
    renderer = result.figure.canvas.get_renderer()
    boxes = {key: artist.get_window_extent(renderer) for key, artist in result.node_artists.items()}
    names = list(boxes)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if boxes[a].overlaps(boxes[b]):
                diagnostics.append(f"Nodes {a!r} and {b!r} overlap; adjust positions or spacing.")
    for text in result.ax.texts:
        gid = text.get_gid() or ""
        if gid.startswith(("node-label:", "node-detail:")):
            node_id = gid.split(":", 1)[1]
            label_box = text.get_window_extent(renderer)
            node_box = boxes[node_id]
            if (
                label_box.x0 < node_box.x0 + 2
                or label_box.x1 > node_box.x1 - 2
                or label_box.y0 < node_box.y0 + 2
                or label_box.y1 > node_box.y1 - 2
            ):
                diagnostics.append(
                    f"Node {node_id!r}: label does not fit; "
                    "increase node size or figure dimensions."
                )
        elif gid.startswith("edge-label:"):
            label_box = text.get_window_extent(renderer)
            if any(label_box.overlaps(box) for box in boxes.values()):
                diagnostics.append("An edge label overlaps a node; adjust spacing or its route.")
        elif gid.startswith("group-label:"):
            group_id = gid.split(":", 1)[1]
            group_box = result.group_artists[group_id].get_window_extent(renderer)
            label_box = text.get_window_extent(renderer)
            if label_box.x1 > group_box.x1 - 2 or label_box.y0 < group_box.y0 + 2:
                diagnostics.append(f"Group {group_id!r}: label does not fit its boundary.")
            if any(label_box.overlaps(box) for box in boxes.values()):
                diagnostics.append(f"Group {group_id!r}: label overlaps a node.")
    text_by_gid = {text.get_gid(): text for text in result.ax.texts}
    for node_id in result.spec.nodes:
        main = text_by_gid.get(f"node-label:{node_id}")
        detail = text_by_gid.get(f"node-detail:{node_id}")
        if (
            main is not None
            and detail is not None
            and main.get_window_extent(renderer).overlaps(detail.get_window_extent(renderer))
        ):
            diagnostics.append(f"Node {node_id!r}: title and detail labels overlap.")
    memberships = {
        node: group_id for group_id, group in result.spec.groups.items() for node in group.nodes
    }
    for group_id, group_artist in result.group_artists.items():
        group_box = group_artist.get_window_extent(renderer)
        for node_id, node_box in boxes.items():
            if memberships.get(node_id) != group_id and node_box.overlaps(group_box):
                diagnostics.append(f"Group {group_id!r} overlaps unrelated node {node_id!r}.")
    for edge, route in zip(result.spec.edges, result.layout.edges, strict=True):
        samples = _samples(route)
        for node_id, node in result.layout.nodes.items():
            if node_id in {edge.source, edge.target} and edge.source != edge.target:
                continue
            x, y = node.center
            w, h = node.size
            inside = (
                (samples[:, 0] > x - w / 2 + 1)
                & (samples[:, 0] < x + w / 2 - 1)
                & (samples[:, 1] > y - h / 2 + 1)
                & (samples[:, 1] < y + h / 2 - 1)
            )
            if inside.any():
                diagnostics.append(
                    f"Edge {edge.source!r} → {edge.target!r} crosses node {node_id!r}; reroute it."
                )
    return list(dict.fromkeys(diagnostics))


def render_diagram(spec: DiagramSpec) -> DiagramResult:
    """Render one architecture using shared styles and vector export machinery."""
    spec = DiagramSpec.model_validate(spec.model_dump())
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        diagnostics = validate_diagram_config(spec)
        style = resolve_style(spec.style)
        geometry = layout_diagram(spec)
        with mpl.rc_context(style.rc):
            figure = Figure(figsize=style.figsize, layout="none")
            FigureCanvasAgg(figure)
            ax = figure.add_axes((0.035, 0.12, 0.93, 0.74 if spec.title else 0.83))
            x0, y0, x1, y1 = geometry.bounds
            pad = max(10, min(x1 - x0, y1 - y0) * 0.08)
            ax.set(xlim=(x0 - pad, x1 + pad), ylim=(y0 - pad, y1 + pad), aspect="equal")
            ax.set_axis_off()
            if spec.title:
                figure.suptitle(spec.title, y=0.97, fontsize=style.rc["axes.titlesize"])
            result = DiagramResult(figure, ax, spec, style, geometry)
            _draw(result)
            diagnostics.extend(check_diagram_visual(result))
    diagnostics.extend(str(record.message) for record in records)
    result.diagnostics = list(dict.fromkeys(diagnostics))
    for message in result.diagnostics:
        warnings.warn(message, FigureWarning, stacklevel=2)
    return result
