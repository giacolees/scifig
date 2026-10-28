"""Produce diagram geometry in points, using manual positions or Graphviz."""

import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from typing import Protocol

from scifig.diagrams.ir import CanonicalDiagram
from scifig.diagrams.specs import DiagramSpec, Port

Point = tuple[float, float]
Bounds = tuple[float, float, float, float]


@dataclass
class NodeGeometry:
    """Node center and size in points."""

    center: Point
    size: Point


@dataclass
class EdgeGeometry:
    """A polyline or cubic spline, with an optional separate arrow tip."""

    points: list[Point]
    label_position: Point | None = None
    curved: bool = False
    end_point: Point | None = None


@dataclass
class GroupGeometry:
    """Group bounds in points."""

    bounds: Bounds


@dataclass
class DiagramGeometry:
    """Complete diagram geometry in point coordinates."""

    nodes: dict[str, NodeGeometry]
    edges: list[EdgeGeometry]
    groups: dict[str, GroupGeometry]
    bounds: Bounds
    engine: str
    engine_version: str | None = None


def _bounds(nodes: list[NodeGeometry], padding: float = 0) -> Bounds:
    return (
        min(n.center[0] - n.size[0] / 2 for n in nodes) - padding,
        min(n.center[1] - n.size[1] / 2 for n in nodes) - padding,
        max(n.center[0] + n.size[0] / 2 for n in nodes) + padding,
        max(n.center[1] + n.size[1] / 2 for n in nodes) + padding,
    )


def _port(node: NodeGeometry, other: Point, port: Port | None) -> Point:
    x, y = node.center
    w, h = node.size[0] / 2, node.size[1] / 2
    if port:
        dx, dy = {"n": (0, h), "s": (0, -h), "e": (w, 0), "w": (-w, 0)}[port]
        return x + dx, y + dy
    dx, dy = other[0] - x, other[1] - y
    if dx == 0 and dy == 0:
        return x + w, y
    scale = min(w / abs(dx) if dx else math.inf, h / abs(dy) if dy else math.inf)
    return x + dx * scale, y + dy * scale


def _manual(spec: CanonicalDiagram) -> DiagramGeometry:
    nodes = {
        key: NodeGeometry(tuple(v * 72 for v in node.position), tuple(v * 72 for v in node.size))
        for key in spec.nodes
        if (node := spec.layout.nodes[key]).position is not None
    }
    edges = []
    for edge in spec.edges:
        source, target = nodes[edge.source], nodes[edge.target]
        if edge.source == edge.target:
            start = _port(source, target.center, edge.source_port or "n")
            end = _port(target, source.center, edge.target_port or "e")
            # Route the loop outside the node, even for explicitly coincident ports.
            x, y = source.center
            w, h = source.size[0] / 2, source.size[1] / 2
            corner = (x + w + 36, y + h + 36)
            points = [start, (start[0], corner[1]), corner, end]
            edges.append(EdgeGeometry(points, corner, curved=True))
        else:
            start = _port(source, target.center, edge.source_port)
            end = _port(target, source.center, edge.target_port)
            edges.append(
                EdgeGeometry([start, end], ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2))
            )
    groups = {}
    for key, group in spec.groups.items():
        x0, y0, x1, y1 = _bounds([nodes[n] for n in group.nodes], 14)
        groups[key] = GroupGeometry((x0, y0, x1, y1 + 8))
    bounds = _bounds(list(nodes.values()))
    for group in groups.values():
        a, b, c, d = group.bounds
        bounds = (min(bounds[0], a), min(bounds[1], b), max(bounds[2], c), max(bounds[3], d))
    for edge in edges:
        points = edge.points + ([edge.label_position] if edge.label_position is not None else [])
        for x, y in points:
            bounds = (min(bounds[0], x), min(bounds[1], y), max(bounds[2], x), max(bounds[3], y))
    return DiagramGeometry(nodes, edges, groups, bounds, "manual")


def _quote(value: str) -> str:
    # Quoted DOT strings interpret backslash escapes; double them to keep user text literal.
    return json.dumps(value.replace("\\", "\\\\"), ensure_ascii=False)


def _dot(spec: CanonicalDiagram) -> tuple[str, dict[str, str], dict[str, str]]:
    ids = {name: f"n{i}" for i, name in enumerate(spec.nodes)}
    group_ids = {name: f"cluster_{i}" for i, name in enumerate(spec.groups)}
    lines = [
        "digraph G {",
        f"rankdir={'LR' if spec.layout.direction == 'left_to_right' else 'TB'};",
        'graph [nodesep=0.4, ranksep=0.55, pad=0.15, fontname="DejaVu Sans", fontsize=9];',
        'node [shape=box, fixedsize=true, fontname="DejaVu Sans", fontsize=9];',
    ]
    for name in spec.nodes:
        node = spec.layout.nodes[name]
        label = _quote(spec.presentation.node_labels[name])
        lines.append(f"{ids[name]} [label={label}, width={node.size[0]}, height={node.size[1]}];")
    for name, group in spec.groups.items():
        lines.append(
            f"subgraph {group_ids[name]} {{ label={_quote(spec.presentation.group_labels[name])}; "
            'fontname="DejaVu Sans"; fontsize=9; margin=14;'
        )
        lines.extend(f"{ids[node]};" for node in group.nodes)
        lines.append("}")
    for i, edge in enumerate(spec.edges):
        source = ids[edge.source] + (f":{edge.source_port}" if edge.source_port else "")
        target = ids[edge.target] + (f":{edge.target_port}" if edge.target_port else "")
        label = _quote(spec.presentation.edge_labels[i])
        lines.append(f'{source} -> {target} [scifig_index="{i}", label={label}];')
    lines.append("}")
    return "\n".join(lines), ids, group_ids


def _pair(value: str) -> Point:
    x, y = value.split(",")
    return float(x), float(y)


def _graphviz(spec: CanonicalDiagram) -> DiagramGeometry:
    executable = shutil.which("dot")
    if executable is None:
        raise RuntimeError("Graphviz 'dot' is unavailable; install Graphviz or use manual layout")
    dot, ids, group_ids = _dot(spec)
    try:
        result = subprocess.run(
            [executable, "-Tjson0"],
            input=dot,
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        version = subprocess.run(
            [executable, "-V"], text=True, capture_output=True, timeout=10, check=True
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Graphviz layout timed out after 10 seconds") from exc
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        raise RuntimeError(f"Graphviz layout failed: {detail}") from exc
    try:
        data = json.loads(result.stdout)
        objects = {obj["name"]: obj for obj in data.get("objects", [])}
        nodes = {
            name: NodeGeometry(
                _pair(objects[internal]["pos"]),
                (float(objects[internal]["width"]) * 72, float(objects[internal]["height"]) * 72),
            )
            for name, internal in ids.items()
        }
        groups = {
            name: GroupGeometry(tuple(float(v) for v in objects[internal]["bb"].split(",")))
            for name, internal in group_ids.items()
        }
        edges: list[EdgeGeometry | None] = [None] * len(spec.edges)
        for edge in data.get("edges", []):
            index = int(edge["scifig_index"])
            if index < 0 or index >= len(edges) or edges[index] is not None:
                raise ValueError("invalid edge index")
            tokens = edge["pos"].split()
            end = next((_pair(token[2:]) for token in tokens if token.startswith("e,")), None)
            points = [_pair(token) for token in tokens if not token.startswith(("e,", "s,"))]
            if len(points) < 4 or (len(points) - 1) % 3:
                raise ValueError("invalid spline points")
            edges[index] = EdgeGeometry(
                points, _pair(edge["lp"]) if "lp" in edge else None, True, end
            )
        if any(edge is None for edge in edges):
            raise ValueError("missing edge geometry")
        bounds = tuple(float(v) for v in data["bb"].split(","))
        if len(bounds) != 4:
            raise ValueError("invalid bounding box")
        return DiagramGeometry(
            nodes, edges, groups, bounds, "graphviz", (version.stderr or version.stdout).strip()
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Graphviz returned invalid layout data: {exc}") from exc


class LayoutEngine(Protocol):
    """Map validated canonical input to point geometry.

    Adapters implement layout only. Use pipeline.layout_canonical (or layout_ir)
    to revalidate mutable inputs and check returned geometry before consumption.
    """

    def layout(self, diagram: CanonicalDiagram) -> DiagramGeometry: ...


class ManualLayoutEngine:
    def layout(self, diagram: CanonicalDiagram) -> DiagramGeometry:
        return _manual(diagram)


class GraphvizLayoutEngine:
    def layout(self, diagram: CanonicalDiagram) -> DiagramGeometry:
        return _graphviz(diagram)


def get_layout_engine(name: str) -> LayoutEngine:
    """Select a supported layout engine."""
    if name == "manual":
        return ManualLayoutEngine()
    if name == "graphviz":
        return GraphvizLayoutEngine()
    raise ValueError(f"unsupported layout engine: {name}")


def layout_ir(diagram: CanonicalDiagram) -> DiagramGeometry:
    """Compatibility entry point for canonical layout orchestration."""
    from scifig.diagrams.pipeline import layout_canonical

    return layout_canonical(diagram)


def layout_diagram(spec: DiagramSpec) -> DiagramGeometry:
    """Lay out a spec through the canonical pipeline, returning point geometry."""
    from scifig.diagrams.pipeline import layout_diagram as run_pipeline

    return run_pipeline(spec)
