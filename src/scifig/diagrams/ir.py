"""Canonical, backend-independent representation of a diagram."""

from copy import deepcopy
from typing import Any

from pydantic import Field, field_validator, model_validator

from scifig.core.specs import _Model
from scifig.diagrams.specs import (
    DiagramSpec,
    Direction,
    EdgeKind,
    GroupRole,
    LayoutName,
    NodeRole,
    Operation,
    Port,
)


class CanonicalNode(_Model):
    role: NodeRole = "module"
    shape: tuple[int | str, ...] | None = None
    operation: Operation | None = None
    frozen: bool = False


class CanonicalEdge(_Model):
    index: int = Field(ge=0)
    source: str
    target: str
    kind: EdgeKind = "data"
    source_port: Port | None = None
    target_port: Port | None = None


class CanonicalGroup(_Model):
    nodes: list[str]
    role: GroupRole = "group"


class NodeLayoutHints(_Model):
    """Requested position and size, in inches."""

    position: tuple[float, float] | None = None
    size: tuple[float, float] = (1.4, 0.65)

    @field_validator("size")
    @classmethod
    def positive_size(cls, size: tuple[float, float]) -> tuple[float, float]:
        if any(value <= 0 for value in size):
            raise ValueError("node size must be positive")
        return size


class LayoutHints(_Model):
    engine: LayoutName = "graphviz"
    direction: Direction = "left_to_right"
    nodes: dict[str, NodeLayoutHints]


class Presentation(_Model):
    title: str = ""
    node_labels: dict[str, str]
    edge_labels: list[str]
    group_labels: dict[str, str]


class CanonicalDiagram(_Model):
    nodes: dict[str, CanonicalNode]
    edges: list[CanonicalEdge] = Field(default_factory=list)
    groups: dict[str, CanonicalGroup] = Field(default_factory=dict)
    layout: LayoutHints
    presentation: Presentation
    feedforward: bool = False
    metadata: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> "CanonicalDiagram":
        node_ids, group_ids = set(self.nodes), set(self.groups)
        if set(self.layout.nodes) != node_ids or set(self.presentation.node_labels) != node_ids:
            raise ValueError("layout hints and node labels must cover exactly the node IDs")
        if set(self.presentation.group_labels) != group_ids:
            raise ValueError("group labels must cover exactly the group IDs")
        if len(self.presentation.edge_labels) != len(self.edges):
            raise ValueError("edge labels must cover exactly the edges")
        if [edge.index for edge in self.edges] != list(range(len(self.edges))):
            raise ValueError("edge indices must match their order")
        # Reuse the specification's graph and semantic validation. Build fresh
        # primitive mappings so in-place changes to nested models are rechecked.
        DiagramSpec.model_validate(
            {
                "nodes": {
                    key: {
                        **node.model_dump(),
                        **self.layout.nodes[key].model_dump(),
                        "label": self.presentation.node_labels[key],
                    }
                    for key, node in self.nodes.items()
                },
                "edges": [
                    {
                        **edge.model_dump(exclude={"index"}),
                        "label": self.presentation.edge_labels[i],
                    }
                    for i, edge in enumerate(self.edges)
                ],
                "groups": {
                    key: {**group.model_dump(), "label": self.presentation.group_labels[key]}
                    for key, group in self.groups.items()
                },
                "layout": self.layout.engine,
                "direction": self.layout.direction,
                "feedforward": self.feedforward,
                "title": self.presentation.title,
            }
        )
        return self


def diagram_to_ir(
    spec: DiagramSpec,
    *,
    metadata: dict[str, Any] | None = None,
    provenance: dict[str, Any] | None = None,
) -> CanonicalDiagram:
    """Copy and revalidate a mutable specification into canonical form."""
    spec = DiagramSpec.model_validate(spec.model_dump())
    return CanonicalDiagram.model_validate(
        {
            "nodes": {
                key: node.model_dump(include={"role", "shape", "operation", "frozen"})
                for key, node in spec.nodes.items()
            },
            "edges": [
                {**edge.model_dump(exclude={"label"}), "index": i}
                for i, edge in enumerate(spec.edges)
            ],
            "groups": {
                key: group.model_dump(exclude={"label"}) for key, group in spec.groups.items()
            },
            "layout": {
                "engine": spec.layout,
                "direction": spec.direction,
                "nodes": {
                    key: node.model_dump(include={"position", "size"})
                    for key, node in spec.nodes.items()
                },
            },
            "presentation": {
                "title": spec.title,
                "node_labels": {key: node.label for key, node in spec.nodes.items()},
                "edge_labels": [edge.label for edge in spec.edges],
                "group_labels": {key: group.label for key, group in spec.groups.items()},
            },
            "feedforward": spec.feedforward,
            "metadata": deepcopy(metadata),
            "provenance": deepcopy(provenance),
        }
    )
