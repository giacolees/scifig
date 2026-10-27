"""Validated specifications for semantic architecture diagrams."""

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from scifig.core.specs import ExportSpec, StyleSpec, _Model


class NodeSpec(_Model):
    """A diagram node; sizes and manual positions are measured in inches."""

    label: str
    role: Literal["input", "output", "module", "data", "store", "loss", "operation"] = "module"
    position: tuple[float, float] | None = None
    size: tuple[float, float] = (1.4, 0.65)
    shape: tuple[int | str, ...] | None = None
    operation: Literal["identity", "add", "concat"] | None = None
    frozen: bool = False

    @field_validator("position", "size", "shape", mode="before")
    @classmethod
    def sequences(cls, value: Any) -> Any:
        """Accept YAML sequences for tuple fields."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def valid_node(self) -> "NodeSpec":
        if not self.label.strip():
            raise ValueError("node label must be nonempty")
        if any(x <= 0 for x in self.size):
            raise ValueError("node size must be positive")
        if self.shape is not None and any(
            (isinstance(x, int) and x <= 0) or (isinstance(x, str) and not x.strip())
            for x in self.shape
        ):
            raise ValueError("shape dimensions must be positive or nonempty symbols")
        return self


class EdgeSpec(_Model):
    """Directed connection between node IDs, with optional boundary ports."""

    source: str
    target: str
    label: str = ""
    kind: Literal["data", "gradient", "control", "feedback"] = "data"
    source_port: Literal["n", "s", "e", "w"] | None = None
    target_port: Literal["n", "s", "e", "w"] | None = None


class GroupSpec(_Model):
    """A labeled, non-overlapping group of nodes."""

    label: str
    nodes: list[str]
    role: Literal["group", "training", "inference"] = "group"

    @model_validator(mode="after")
    def valid_group(self) -> "GroupSpec":
        if not self.label.strip():
            raise ValueError("group label must be nonempty")
        if not self.nodes or len(self.nodes) != len(set(self.nodes)):
            raise ValueError("group nodes must be nonempty and unique")
        return self


class DiagramSpec(_Model):
    """An architecture graph independent of any plotting backend."""

    type: Literal["architecture"] = "architecture"
    nodes: dict[str, NodeSpec]
    edges: list[EdgeSpec] = Field(default_factory=list)
    groups: dict[str, GroupSpec] = Field(default_factory=dict)
    direction: Literal["left_to_right", "top_to_bottom"] = "left_to_right"
    layout: Literal["graphviz", "manual"] = "graphviz"
    feedforward: bool = False
    title: str = ""
    style: StyleSpec | str = Field(
        default_factory=lambda: StyleSpec(width="double_column", height=3.0)
    )
    export: ExportSpec = Field(default_factory=ExportSpec)

    @model_validator(mode="after")
    def valid_graph(self) -> "DiagramSpec":
        if not self.nodes or any(not key.strip() for key in self.nodes):
            raise ValueError("nodes must have nonempty IDs")
        if any(not key.strip() for key in self.groups):
            raise ValueError("group IDs must be nonempty")
        assigned: set[str] = set()
        for group in self.groups.values():
            for node in group.nodes:
                if node not in self.nodes:
                    raise ValueError(f"unknown group node: {node}")
                if node in assigned:
                    raise ValueError(f"node belongs to multiple groups: {node}")
                assigned.add(node)
        seen: set[tuple] = set()
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError(f"unknown edge endpoint: {edge.source} -> {edge.target}")
            key = (
                edge.source,
                edge.target,
                edge.kind,
                edge.source_port,
                edge.target_port,
                edge.label,
            )
            if key in seen:
                raise ValueError(f"duplicate edge: {edge.source} -> {edge.target} ({edge.kind})")
            seen.add(key)
        positions = [node.position is not None for node in self.nodes.values()]
        if self.layout == "manual" and not all(positions):
            raise ValueError("manual layout requires a position for every node")
        if self.layout == "graphviz" and any(positions):
            raise ValueError("node positions require manual layout")
        if self.feedforward:
            adjacency = {node: [] for node in self.nodes}
            for edge in self.edges:
                if edge.kind in {"data", "feedback"}:
                    adjacency[edge.source].append(edge.target)
            visiting: set[str] = set()
            visited: set[str] = set()

            def visit(node: str) -> None:
                if node in visiting:
                    raise ValueError("feedforward diagram contains a data or feedback cycle")
                if node in visited:
                    return
                visiting.add(node)
                for target in adjacency[node]:
                    visit(target)
                visiting.remove(node)
                visited.add(node)

            for node in adjacency:
                visit(node)
        for node_id, node in self.nodes.items():
            if node.operation not in {"identity", "add"}:
                continue
            inputs = [
                self.nodes[e.source].shape
                for e in self.edges
                if e.target == node_id and e.kind == "data"
            ]
            required = 1 if node.operation == "identity" else 2
            if (node.operation == "identity" and len(inputs) != required) or (
                node.operation == "add" and len(inputs) < required
            ):
                count = "exactly one" if required == 1 else "at least two"
                raise ValueError(f"node {node_id}: {node.operation} requires {count} data inputs")
            shapes = [shape for shape in [*inputs, node.shape] if shape is not None]
            for i, shape in enumerate(shapes):
                for other in shapes[i + 1 :]:
                    if len(shape) != len(other) or any(
                        isinstance(a, int) and isinstance(b, int) and a != b
                        for a, b in zip(shape, other, strict=False)
                    ):
                        raise ValueError(f"node {node_id}: {node.operation} shapes differ")
        return self


def validate_diagram(spec: DiagramSpec) -> list[str]:
    """Return advisory shape diagnostics without inferring unspecified dimensions."""
    diagnostics: list[str] = []
    for node_id, node in spec.nodes.items():
        if node.operation == "concat":
            diagnostics.append(f"node {node_id}: concat shape cannot be checked without an axis")
            continue
        if node.operation not in {"identity", "add"}:
            continue
        inputs = [
            spec.nodes[e.source].shape
            for e in spec.edges
            if e.target == node_id and e.kind == "data"
        ]
        shapes = [shape for shape in [*inputs, node.shape] if shape is not None]
        if len(shapes) < len(inputs) + 1:
            diagnostics.append(f"node {node_id}: shape cannot be checked with missing dimensions")
        elif any(shape != shapes[0] for shape in shapes[1:]):
            diagnostics.append(f"node {node_id}: symbolic shapes cannot be verified")
    for edge in spec.edges:
        if edge.kind == "gradient" and spec.nodes[edge.target].frozen:
            diagnostics.append(f"gradient edge targets frozen node {edge.target}")
    return diagnostics
