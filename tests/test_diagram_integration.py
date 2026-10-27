"""Check interoperability, reproducibility and invalid diagram inputs."""

import json
import os
import subprocess
import sys
import warnings

import pytest
import yaml

from scifig import DiagramSpec, NodeSpec, architecture, load_spec, render, validate


def test_manual_python_yaml_parity(tmp_path):
    options = {
        "nodes": {
            "a": {"label": "Input", "position": [0, 0]},
            "b": {"label": "Output", "position": [2, 0]},
        },
        "edges": [{"source": "a", "target": "b", "label": "signal"}],
        "layout": "manual",
    }
    source = tmp_path / "diagram.yaml"
    source.write_text(yaml.safe_dump({"diagram": options}, sort_keys=False))
    parsed = load_spec(source)
    assert isinstance(parsed, DiagramSpec)
    first, second = architecture(**options), render(parsed)
    assert first.layout == second.layout
    for extension in ("pdf", "svg", "png"):
        a = first.savefig(tmp_path / f"api.{extension}").read_bytes()
        b = second.savefig(tmp_path / f"yaml.{extension}").read_bytes()
        assert a == b
    sidecar = json.loads(first.save_layout(tmp_path / "layout.json").read_text())
    assert sidecar["scifig_version"] == "0.2.0"
    assert sidecar["matplotlib_version"]
    assert sidecar["spec"]["layout"] == "manual"


def test_diagram_color_diagnostics_and_data_override():
    spec = DiagramSpec(
        nodes={"a": {"label": "A"}, "b": {"label": "B"}}, style={"colors": {"a": "red", "b": "red"}}
    )
    with warnings.catch_warnings(record=True) as caught:
        assert any("duplicate colors" in item for item in validate(spec))
    assert not caught  # validate returns caveats without emitting them
    with pytest.raises(ValueError, match="tabular"):
        render(spec, data={"x": [1]})
    with pytest.raises(ValueError, match="tabular"):
        validate(spec, data={"x": [1]})


@pytest.mark.parametrize(
    "options",
    [
        {"size": (float("nan"), 1.0)},
        {"position": (float("inf"), 0.0)},
        {"size": (0.0, 1.0)},
        {"shape": (True, 3)},
    ],
)
def test_invalid_node_numerics_fail_before_layout(options):
    with pytest.raises(ValueError):
        NodeSpec(label="Node", **options)


def test_cli_missing_optional_layout_dependency_has_no_traceback(tmp_path):
    source = tmp_path / "auto.yaml"
    source.write_text("diagram:\n  nodes:\n    a: {label: A}\n")
    result = subprocess.run(
        [sys.executable, "-m", "scifig", "render", str(source)],
        env=dict(os.environ, PATH="/nonexistent", MPLBACKEND="Agg"),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Graphviz" in result.stderr and "manual" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "figures").exists()
