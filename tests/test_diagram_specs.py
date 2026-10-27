import pytest
from pydantic import ValidationError

from scifig.diagrams.specs import DiagramSpec, validate_diagram


def test_graph_validation_and_manual_positions():
    nodes = {"a": {"label": "A", "position": [0, 0]}, "b": {"label": "B", "position": [2, 0]}}
    spec = DiagramSpec.model_validate({"nodes": nodes, "layout": "manual"})
    assert spec.nodes["a"].position == (0.0, 0.0)
    with pytest.raises(ValidationError, match="positions require manual"):
        DiagramSpec.model_validate({"nodes": nodes})
    with pytest.raises(ValidationError, match="unknown edge endpoint"):
        DiagramSpec.model_validate(
            {"nodes": nodes, "layout": "manual", "edges": [{"source": "a", "target": "missing"}]}
        )
    with pytest.raises(ValidationError, match="multiple groups"):
        DiagramSpec.model_validate(
            {
                "nodes": nodes,
                "layout": "manual",
                "groups": {
                    "one": {"label": "One", "nodes": ["a"]},
                    "two": {"label": "Two", "nodes": ["a"]},
                },
            }
        )


def test_feedforward_cycle_and_gradient():
    nodes = {"a": {"label": "A"}, "b": {"label": "B"}}
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}]
    DiagramSpec.model_validate({"nodes": nodes, "edges": edges})
    with pytest.raises(ValidationError, match="cycle"):
        DiagramSpec.model_validate({"nodes": nodes, "edges": edges, "feedforward": True})
    edges[1]["kind"] = "gradient"
    DiagramSpec.model_validate({"nodes": nodes, "edges": edges, "feedforward": True})


def test_shape_diagnostics_distinguish_concrete_and_symbolic():
    spec = DiagramSpec.model_validate(
        {
            "nodes": {
                "a": {"label": "A", "shape": ["N", 3]},
                "b": {"label": "B", "shape": ["M", 3], "operation": "identity"},
            },
            "edges": [{"source": "a", "target": "b"}],
        }
    )
    assert "symbolic" in validate_diagram(spec)[0]
    raw = spec.model_dump()
    raw["nodes"]["b"]["shape"] = ("N", 4)
    with pytest.raises(ValidationError, match="shapes differ"):
        DiagramSpec.model_validate(raw)


def test_operation_arity_and_parallel_edges():
    nodes = {"a": {"label": "A"}, "b": {"label": "B", "operation": "add"}}
    with pytest.raises(ValidationError, match="at least two"):
        DiagramSpec.model_validate({"nodes": nodes, "edges": [{"source": "a", "target": "b"}]})
    edges = [
        {"source": "a", "target": "b", "label": "first"},
        {"source": "a", "target": "b", "label": "second"},
    ]
    DiagramSpec.model_validate({"nodes": nodes, "edges": edges})
    edges[1]["label"] = "first"
    with pytest.raises(ValidationError, match="duplicate edge"):
        DiagramSpec.model_validate({"nodes": nodes, "edges": edges})
