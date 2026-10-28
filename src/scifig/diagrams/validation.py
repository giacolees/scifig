"""Geometry contracts and rendered relationship diagnostics for diagrams."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from scifig.diagrams.layout import DiagramGeometry, EdgeGeometry
from scifig.validation.visual import check_visual

if TYPE_CHECKING:
    from scifig.diagrams.ir import CanonicalDiagram
    from scifig.diagrams.rendering import DiagramResult


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
    from scifig.diagrams.ir import diagram_to_ir

    diagram = result.diagram if result.diagram is not None else diagram_to_ir(result.spec)
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
    for node_id in diagram.nodes:
        main = text_by_gid.get(f"node-label:{node_id}")
        detail = text_by_gid.get(f"node-detail:{node_id}")
        if (
            main is not None
            and detail is not None
            and main.get_window_extent(renderer).overlaps(detail.get_window_extent(renderer))
        ):
            diagnostics.append(f"Node {node_id!r}: title and detail labels overlap.")
    memberships = {
        node: group_id for group_id, group in diagram.groups.items() for node in group.nodes
    }
    for group_id, group_artist in result.group_artists.items():
        group_box = group_artist.get_window_extent(renderer)
        for node_id, node_box in boxes.items():
            if memberships.get(node_id) != group_id and node_box.overlaps(group_box):
                diagnostics.append(f"Group {group_id!r} overlaps unrelated node {node_id!r}.")
    for edge, route in zip(diagram.edges, result.layout.edges, strict=True):
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


def validate_geometry(diagram: CanonicalDiagram, geometry: DiagramGeometry) -> None:
    """Reject malformed layout output before any Matplotlib artists are created.

    Bounds and all coordinates use points. A 0.1 point containment tolerance
    accommodates Graphviz's rounded JSON widths and bounding boxes.
    """

    def fail(detail: str) -> None:
        raise RuntimeError(f"layout returned invalid geometry: {detail}")

    def values(value: object, length: int, name: str) -> tuple[float, ...]:
        if not isinstance(value, (list, tuple)) or len(value) != length:
            fail(f"{name} must have {length} coordinates")
        if any(
            isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
            for item in value
        ):
            fail(f"{name} has non-finite or non-numeric coordinates")
        return tuple(value)

    def bounds(value: object, name: str) -> tuple[float, ...]:
        box = values(value, 4, name)
        if box[0] >= box[2] or box[1] >= box[3]:
            fail(f"{name} must have positive width and height")
        return box

    if not isinstance(geometry, DiagramGeometry):
        fail("expected DiagramGeometry")
    if not isinstance(geometry.nodes, dict) or set(geometry.nodes) != set(diagram.nodes):
        fail("node coverage must exactly match canonical IDs")
    if not isinstance(geometry.groups, dict) or set(geometry.groups) != set(diagram.groups):
        fail("group coverage must exactly match canonical IDs")
    if not isinstance(geometry.edges, list) or len(geometry.edges) != len(diagram.edges):
        fail("edge count must match canonical order")
    if not isinstance(geometry.engine, str) or not geometry.engine.strip():
        fail("engine provenance must be nonempty")
    if geometry.engine_version is not None and not isinstance(geometry.engine_version, str):
        fail("engine version must be a string or None")
    outer = bounds(geometry.bounds, "diagram bounds")

    def contained(point: tuple[float, ...], name: str) -> None:
        x, y = point
        if not (outer[0] - 0.1 <= x <= outer[2] + 0.1 and outer[1] - 0.1 <= y <= outer[3] + 0.1):
            fail(f"{name} lies outside diagram bounds")

    from scifig.diagrams.layout import GroupGeometry, NodeGeometry

    for key, node in geometry.nodes.items():
        if not isinstance(node, NodeGeometry):
            fail(f"node {key!r} must be NodeGeometry")
        x, y = values(node.center, 2, f"node {key!r} center")
        width, height = values(node.size, 2, f"node {key!r} size")
        if width <= 0 or height <= 0:
            fail(f"node {key!r} size must be positive")
        contained((x - width / 2, y - height / 2), f"node {key!r}")
        contained((x + width / 2, y + height / 2), f"node {key!r}")
    for key, group in geometry.groups.items():
        if not isinstance(group, GroupGeometry):
            fail(f"group {key!r} must be GroupGeometry")
        x0, y0, x1, y1 = bounds(group.bounds, f"group {key!r} bounds")
        contained((x0, y0), f"group {key!r}")
        contained((x1, y1), f"group {key!r}")
        for member in diagram.groups[key].nodes:
            node = geometry.nodes[member]
            x, y = node.center
            width, height = node.size
            if not (
                x - width / 2 >= x0 - 0.1
                and x + width / 2 <= x1 + 0.1
                and y - height / 2 >= y0 - 0.1
                and y + height / 2 <= y1 + 0.1
            ):
                fail(f"group {key!r} does not contain member {member!r}")
    for index, edge in enumerate(geometry.edges):
        name = f"edge {index}"
        if not isinstance(edge, EdgeGeometry):
            fail(f"{name} must be EdgeGeometry")
        if not isinstance(edge.curved, bool) or not isinstance(edge.points, list):
            fail(f"{name} requires a boolean curved flag and a point list")
        count = len(edge.points)
        if (edge.curved and (count < 4 or (count - 1) % 3)) or (not edge.curved and count < 2):
            fail(f"{name} requires valid polyline or cubic route points")
        for point in edge.points:
            contained(values(point, 2, f"{name} route"), name)
        for point in (edge.label_position, edge.end_point):
            if point is not None:
                contained(values(point, 2, f"{name} label or arrow tip"), name)
