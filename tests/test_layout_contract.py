import pytest
from pydantic import ValidationError

from scifig.diagrams.ir import diagram_to_ir
from scifig.diagrams.layout import get_layout_engine, layout_diagram, layout_ir
from scifig.diagrams.specs import DiagramSpec


def test_manual_adapter_and_compatibility():
    spec = DiagramSpec.model_validate(
        {"layout": "manual", "nodes": {"a": {"label": "A", "position": [1, 2]}}}
    )
    assert layout_ir(diagram_to_ir(spec)) == layout_diagram(spec)
    assert layout_ir(diagram_to_ir(spec)).nodes["a"].center == (72, 144)


def test_engine_dispatch_rejects_unknown():
    with pytest.raises(ValueError, match="unsupported"):
        get_layout_engine("other")


def test_layout_revalidates_mutable_ir():
    spec = DiagramSpec.model_validate({"nodes": {"a": {"label": "A"}}})
    diagram = diagram_to_ir(spec)
    diagram.layout.nodes.clear()
    with pytest.raises(ValidationError):
        layout_ir(diagram)
