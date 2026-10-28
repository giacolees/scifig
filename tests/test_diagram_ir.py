import pytest
from pydantic import ValidationError

from scifig.diagrams.ir import CanonicalDiagram, diagram_to_ir
from scifig.diagrams.specs import DiagramSpec


def specimen():
    return DiagramSpec.model_validate(
        {
            "layout": "manual",
            "nodes": {
                "a": {"label": "A", "position": [0, 0], "shape": [2, "N"]},
                "b": {"label": "B", "position": [2, 0], "frozen": True},
            },
            "edges": [{"source": "a", "target": "b", "label": "data", "source_port": "e"}],
            "groups": {"g": {"label": "Group", "nodes": ["a"]}},
        }
    )


def test_conversion_separates_fields_and_copies():
    spec = specimen()
    diagram = diagram_to_ir(spec)
    assert diagram.nodes["a"].shape == (2, "N")
    assert diagram.presentation.node_labels == {"a": "A", "b": "B"}
    assert diagram.layout.nodes["a"].position == (0, 0)
    assert diagram.edges[0].index == 0
    spec.groups["g"].nodes.append("b")
    spec.nodes["a"].label = "changed"
    assert diagram.groups["g"].nodes == ["a"]
    assert diagram.presentation.node_labels["a"] == "A"


def test_conversion_revalidates_mutated_spec():
    spec = specimen()
    spec.edges[0].target = "missing"
    with pytest.raises(ValidationError, match="unknown edge endpoint"):
        diagram_to_ir(spec)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["layout"]["nodes"].pop("a"),
        lambda d: d["presentation"]["node_labels"].pop("a"),
        lambda d: d["presentation"]["group_labels"].pop("g"),
        lambda d: d["presentation"]["edge_labels"].clear(),
        lambda d: d["edges"][0].update(index=1),
        lambda d: d["groups"]["g"]["nodes"].append("missing"),
        lambda d: d["nodes"]["a"].update(role="invalid"),
        lambda d: d["layout"]["nodes"]["a"].update(size=(0, 1)),
    ],
)
def test_canonical_rejects_invalid_contract(mutate):
    raw = diagram_to_ir(specimen()).model_dump()
    mutate(raw)
    with pytest.raises(ValidationError):
        CanonicalDiagram.model_validate(raw)


def test_metadata_provenance_are_optional_and_deeply_isolated():
    spec = specimen()
    assert diagram_to_ir(spec).metadata is None
    assert diagram_to_ir(spec).provenance is None
    metadata = {"tags": ["review"]}
    provenance = {"producer": {"name": "fixture"}}
    diagram = diagram_to_ir(spec, metadata=metadata, provenance=provenance)
    metadata["tags"].append("changed")
    provenance["producer"]["name"] = "changed"
    assert diagram.metadata == {"tags": ["review"]}
    assert diagram.provenance == {"producer": {"name": "fixture"}}
    assert "metadata" not in spec.model_dump()
    assert "provenance" not in spec.model_dump()


def test_operation_and_role_semantics_survive_conversion():
    spec = DiagramSpec.model_validate(
        {
            "nodes": {
                "a": {"label": "Input", "role": "input", "shape": [4]},
                "b": {
                    "label": "Identity",
                    "role": "operation",
                    "operation": "identity",
                    "shape": [4],
                },
            },
            "edges": [{"source": "a", "target": "b", "target_port": "w"}],
            "feedforward": True,
        }
    )
    diagram = diagram_to_ir(spec)
    assert diagram.nodes["b"].operation == "identity"
    assert diagram.nodes["b"].role == "operation"
    assert diagram.edges[0].target_port == "w"
    assert diagram.feedforward is True
