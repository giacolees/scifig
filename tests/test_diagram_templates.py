"""Packaged diagram templates are independent, validated semantic graphs."""

import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from scifig import list_diagram_templates, load_diagram_template, render, validate
from scifig.diagrams.specs import DiagramSpec, validate_diagram


def test_template_names_and_unknown_name():
    assert list_diagram_templates() == ["research_workflow", "residual_block"]
    names = list_diagram_templates()
    names.clear()
    assert len(list_diagram_templates()) == 2
    with pytest.raises(ValueError, match="unknown diagram template.*available"):
        load_diagram_template("missing")


def test_residual_block_semantics():
    spec = load_diagram_template("residual_block")
    assert isinstance(spec, DiagramSpec)
    assert spec.layout == "manual" and spec.feedforward
    assert spec.style.preset == "editorial"
    assert all(node.position is not None for node in spec.nodes.values())
    assert {(edge.source, edge.target, edge.kind) for edge in spec.edges} == {
        ("input", "transform", "data"),
        ("input", "identity", "data"),
        ("transform", "add", "data"),
        ("identity", "add", "data"),
        ("add", "output", "data"),
    }
    assert spec.nodes["identity"].operation == "identity"
    assert spec.nodes["add"].operation == "add"
    assert all(node.shape == ("B", "C", "H", "W") for node in spec.nodes.values())
    assert validate_diagram(spec) == []
    assert spec.export.directory == Path("figures")


def test_research_workflow_semantics():
    spec = load_diagram_template("research_workflow")
    assert spec.layout == "manual" and not spec.feedforward
    assert spec.style.preset == "editorial"
    assert "conceptual" in spec.title.lower()
    assert all(node.position is not None for node in spec.nodes.values())
    assert {(edge.source, edge.target, edge.kind) for edge in spec.edges} == {
        ("question", "hypothesis", "data"),
        ("hypothesis", "experiment", "data"),
        ("experiment", "evidence", "data"),
        ("evidence", "hypothesis", "feedback"),
    }
    assert validate_diagram(spec) == []
    assert spec.export.directory == Path("figures")


def test_each_load_is_fresh():
    first = load_diagram_template("residual_block")
    first.nodes["input"].label = "changed"
    first.edges.clear()
    first.export.formats.clear()
    second = load_diagram_template("residual_block")
    assert second.nodes["input"].label == "Input"
    assert len(second.edges) == 5
    assert second.export.formats == ["pdf", "svg", "png"]


def test_template_semantic_validation_rejects_invalid_changes():
    residual = load_diagram_template("residual_block").model_dump()
    residual["nodes"]["identity"]["shape"] = ("B", "C")
    with pytest.raises(ValueError, match="shapes differ"):
        DiagramSpec.model_validate(residual)
    workflow = load_diagram_template("research_workflow").model_dump()
    workflow["feedforward"] = True
    with pytest.raises(ValueError, match="cycle"):
        DiagramSpec.model_validate(workflow)


@pytest.mark.parametrize("name", ["residual_block", "research_workflow"])
def test_templates_render_without_diagnostics(name):
    spec = load_diagram_template(name)
    assert validate(spec) == []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = render(spec)
    assert not caught
    plt.close(result.figure)


def test_resources_use_strict_yaml_parser(tmp_path, monkeypatch):
    from scifig.diagrams import templates

    resource_dir = tmp_path / "template_sources"
    resource_dir.mkdir()
    resource = resource_dir / "residual_block.yaml"
    monkeypatch.setattr(templates, "files", lambda _package: tmp_path)
    resource.write_text("diagram:\n  nodes:\n    a: {label: First, label: Second}\n")
    with pytest.raises(ValueError, match="duplicate YAML key"):
        load_diagram_template("residual_block")
    resource.write_text("diagram:\n  nodes:\n    a: {label: A, unknown: true}\n")
    with pytest.raises(ValueError, match="unknown"):
        load_diagram_template("residual_block")


def test_built_wheel_contains_loadable_resources(tmp_path):
    project = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    extracted = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(extracted)
    code = """
import sys
sys.path.insert(0, sys.argv[1])
import scifig
assert scifig.__file__.startswith(sys.argv[1])
assert scifig.list_diagram_templates() == ['research_workflow', 'residual_block']
for name in scifig.list_diagram_templates():
    assert scifig.load_diagram_template(name).layout == 'manual'
"""
    subprocess.run(
        [sys.executable, "-I", "-c", code, str(extracted)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
