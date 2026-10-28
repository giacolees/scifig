"""Contracts at the canonical diagram, layout and rendering boundaries."""

import json
import warnings
from copy import deepcopy

import pytest
import yaml
from matplotlib.path import Path

from scifig import load_spec
from scifig.diagrams.ir import diagram_to_ir
from scifig.diagrams.layout import EdgeGeometry, layout_ir
from scifig.diagrams.pipeline import prepare_diagram, render_diagram
from scifig.diagrams.specs import DiagramSpec
from scifig.diagrams.validation import validate_geometry


def specimen():
    return DiagramSpec.model_validate(
        {
            "layout": "manual",
            "title": "Pipeline",
            "nodes": {
                "a": {"label": "Alpha", "position": [0, 0], "shape": [2, "N"]},
                "b": {"label": "Beta", "position": [3, 0], "frozen": True},
            },
            "edges": [
                {
                    "source": "a",
                    "target": "b",
                    "label": "forward",
                    "source_port": "e",
                    "target_port": "w",
                },
                {"source": "a", "target": "b", "label": "control", "kind": "control"},
                {"source": "b", "target": "b", "label": "loop", "kind": "feedback"},
            ],
            "groups": {"g": {"label": "Group", "nodes": ["a"]}},
            "style": {"preset": "editorial"},
        }
    )


def _geometry():
    diagram = diagram_to_ir(specimen())
    return diagram, layout_ir(diagram)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda g: g.nodes.pop("a"), "node coverage"),
        (lambda g: g.nodes.update(extra=deepcopy(g.nodes["a"])), "node coverage"),
        (lambda g: g.groups.clear(), "group coverage"),
        (lambda g: g.groups.update(extra=deepcopy(g.groups["g"])), "group coverage"),
        (lambda g: g.edges.pop(), "edge count"),
        (lambda g: setattr(g.nodes["a"], "center", (float("nan"), 0)), "non-finite"),
        (lambda g: setattr(g.nodes["a"], "size", (0, 1)), "size must be positive"),
        (lambda g: setattr(g, "bounds", (0, 0, 0, 1)), "positive width"),
        (lambda g: setattr(g.groups["g"], "bounds", (1, 0, 0, 1)), "positive width"),
        (lambda g: setattr(g.nodes["a"], "center", (10000, 0)), "outside diagram bounds"),
        (
            lambda g: setattr(g.groups["g"], "bounds", (-10000, -10, 10, 10)),
            "outside diagram bounds",
        ),
        (lambda g: setattr(g.edges[0], "points", [(0, 0)]), "polyline or cubic"),
        (lambda g: setattr(g.edges[2], "points", [(0, 0)] * 5), "polyline or cubic"),
        (lambda g: setattr(g.edges[0], "label_position", (float("inf"), 0)), "non-finite"),
        (lambda g: setattr(g.edges[0], "end_point", (10000, 0)), "outside diagram bounds"),
    ],
)
def test_invalid_geometry_is_rejected(mutate, message):
    diagram, geometry = _geometry()
    mutate(geometry)
    with pytest.raises(RuntimeError, match=message):
        validate_geometry(diagram, geometry)


def test_valid_cubic_with_separate_tip_and_multiple_segments():
    diagram, geometry = _geometry()
    geometry.edges[0] = EdgeGeometry(
        [(0, 0), (10, 10), (20, 10), (30, 0), (40, -10), (50, -10), (60, 0)],
        (30, 0),
        True,
        (65, 0),
    )
    validate_geometry(diagram, geometry)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = render_diagram(specimen(), geometry=geometry)
    path = result.edge_artists[0]._path_original
    assert list(path.codes) == [Path.MOVETO] + [Path.CURVE4] * 6 + [Path.LINETO]
    assert tuple(path.vertices[-1]) == (65, 0)


def test_supplied_geometry_skips_layout_is_copied_and_preserves_output(monkeypatch, tmp_path):
    spec = specimen()
    diagram, geometry = _geometry()

    def forbidden(*args, **kwargs):
        pytest.fail("supplied geometry must not call the layout engine")

    monkeypatch.setattr("scifig.diagrams.pipeline.get_layout_engine", forbidden)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = render_diagram(spec, geometry=geometry)
        second = render_diagram(spec, geometry=geometry)
    assert first.spec == spec and first.spec is not spec
    assert first.diagram == diagram
    assert first.layout == geometry and first.layout is not geometry
    assert first.layout.nodes["a"] is not geometry.nodes["a"]
    assert set(first.node_artists) == {"a", "b"}
    assert set(first.group_artists) == {"g"}
    assert len(first.edge_artists) == 3
    labels = {t.get_gid(): t.get_text() for t in first.ax.texts}
    assert labels["node-label:a"] == "Alpha"
    assert labels["edge-label:0"] == "forward"
    assert labels["group-label:g"] == "Group"
    assert first.style.preset == "editorial"
    one = first.save_layout(tmp_path / "one.json")
    two = second.save_layout(tmp_path / "two.json")
    assert one.read_bytes() == two.read_bytes()
    payload = json.loads(one.read_text())
    assert payload["schema_version"] == 1
    assert payload["engine"] == "manual"
    assert payload["spec"]["nodes"]["a"]["label"] == "Alpha"
    assert set(payload) == {
        "schema_version",
        "nodes",
        "edges",
        "groups",
        "bounds",
        "engine",
        "engine_version",
        "figure_size_inches",
        "matplotlib_version",
        "scifig_version",
        "spec",
    }
    spec.nodes["a"].label = "changed"
    geometry.nodes["a"].center = (999, 999)
    assert first.spec.nodes["a"].label == "Alpha"
    assert first.layout.nodes["a"].center != (999, 999)


def test_invalid_supplied_geometry_fails_before_drawing(monkeypatch):
    _, geometry = _geometry()
    geometry.edges.clear()

    def forbidden(*args, **kwargs):
        pytest.fail("invalid geometry reached drawing")

    monkeypatch.setattr("scifig.diagrams.rendering.render_geometry", forbidden)
    with pytest.raises(RuntimeError, match="edge count"):
        render_diagram(specimen(), geometry=geometry)


def test_python_yaml_canonical_and_layout_parity(tmp_path):
    spec = specimen()
    source = tmp_path / "diagram.yaml"
    source.write_text(yaml.safe_dump({"diagram": spec.model_dump(mode="json")}, sort_keys=False))
    parsed = load_spec(source)
    original = prepare_diagram(spec)
    loaded = prepare_diagram(parsed)
    assert original.diagram == loaded.diagram
    assert layout_ir(original.diagram) == layout_ir(loaded.diagram)
    assert [(e.source_port, e.target_port) for e in loaded.diagram.edges] == [
        ("e", "w"),
        (None, None),
        (None, None),
    ]
    assert [e.index for e in loaded.diagram.edges] == [0, 1, 2]
    assert loaded.diagram.groups["g"].nodes == ["a"]
    assert loaded.diagram.edges[2].source == loaded.diagram.edges[2].target == "b"


@pytest.mark.parametrize("side", ["left", "bottom", "right", "top"])
def test_group_bounds_must_contain_entire_member(side):
    diagram, geometry = _geometry()
    x, y = geometry.nodes["a"].center
    width, height = geometry.nodes["a"].size
    box = [x - width / 2, y - height / 2, x + width / 2, y + height / 2]
    index = {"left": 0, "bottom": 1, "right": 2, "top": 3}[side]
    box[index] += 1 if index < 2 else -1
    geometry.groups["g"].bounds = tuple(box)
    with pytest.raises(RuntimeError, match="does not contain member"):
        validate_geometry(diagram, geometry)


def test_legacy_result_positional_diagnostics_and_visual_fallback():
    from scifig.diagrams.rendering import DiagramResult
    from scifig.diagrams.validation import check_diagram_visual

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = render_diagram(specimen())
    legacy = DiagramResult(
        result.figure,
        result.ax,
        result.spec,
        result.style,
        result.layout,
        ["legacy diagnostic"],
        result.node_artists,
        result.edge_artists,
        result.group_artists,
    )
    assert legacy.diagram is None
    assert legacy.diagnostics == ["legacy diagnostic"]
    assert check_diagram_visual(legacy) == check_diagram_visual(result)


def test_mutated_source_fails_before_drawing_with_supplied_geometry(monkeypatch):
    spec = specimen()
    _, geometry = _geometry()
    spec.edges[0].target = "missing"

    def forbidden(*args, **kwargs):
        pytest.fail("invalid specification reached drawing")

    monkeypatch.setattr("scifig.diagrams.rendering.render_geometry", forbidden)
    with pytest.raises(ValueError, match="unknown edge endpoint"):
        render_diagram(spec, geometry=geometry)
