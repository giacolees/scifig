import shutil

import pytest

from scifig.diagrams.layout import layout_diagram
from scifig.diagrams.specs import DiagramSpec


def test_manual_geometry_and_group_bounds():
    spec = DiagramSpec.model_validate(
        {
            "layout": "manual",
            "nodes": {
                "a": {"label": "A", "position": [0, 0], "size": [1, 1]},
                "b": {"label": "B", "position": [2, 0], "size": [1, 1]},
            },
            "edges": [{"source": "a", "target": "b", "source_port": "n"}],
            "groups": {"g": {"label": "Group", "nodes": ["a"]}},
        }
    )
    geometry = layout_diagram(spec)
    assert geometry.edges[0].points == [(0, 36), (108, 0)]
    assert geometry.groups["g"].bounds == (-50, -50, 50, 58)
    assert geometry.bounds == (-50, -50, 180, 58)


def test_missing_graphviz_is_actionable(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    spec = DiagramSpec.model_validate({"nodes": {"a": {"label": "A"}}})
    with pytest.raises(RuntimeError, match="install Graphviz or use manual"):
        layout_diagram(spec)


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz unavailable")
def test_graphviz_routing_and_safe_labels():
    spec = DiagramSpec.model_validate(
        {
            "nodes": {
                "a; }": {"label": '<bad> "quoted"'},
                "b": {"label": "B"},
                "c": {"label": "C"},
            },
            "edges": [
                {"source": "b", "target": "c", "label": "second"},
                {"source": "a; }", "target": "b", "label": "first"},
            ],
            "groups": {"g": {"label": "Group", "nodes": ["a; }"]}},
        }
    )
    geometry = layout_diagram(spec)
    assert len(geometry.nodes) == 3
    assert geometry.edges[0].points[0][0] > geometry.edges[1].points[0][0]
    assert all(e.curved and e.end_point for e in geometry.edges)
    assert geometry.groups["g"].bounds[0] < geometry.nodes["a; }"].center[0]


def test_invalid_graphviz_output_is_actionable(monkeypatch):
    import subprocess

    monkeypatch.setattr(shutil, "which", lambda _: "/fake/dot")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="not json", stderr=""
        ),
    )
    spec = DiagramSpec.model_validate({"nodes": {"a": {"label": "A"}}})
    with pytest.raises(RuntimeError, match="invalid layout data"):
        layout_diagram(spec)


def test_manual_self_loop_is_routed_and_in_bounds():
    spec = DiagramSpec.model_validate(
        {
            "layout": "manual",
            "nodes": {"a": {"label": "A", "position": [0, 0], "size": [1, 1]}},
            "edges": [{"source": "a", "target": "a"}],
        }
    )
    geometry = layout_diagram(spec)
    edge = geometry.edges[0]
    assert edge.curved and edge.points[0] == (0, 36) and edge.points[-1] == (36, 0)
    assert geometry.bounds[2:] == (72, 72)


def test_graphviz_timeout(monkeypatch):
    import subprocess

    monkeypatch.setattr(shutil, "which", lambda _: "/fake/dot")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 10)

    monkeypatch.setattr(subprocess, "run", timeout)
    spec = DiagramSpec.model_validate({"nodes": {"a": {"label": "A"}}})
    with pytest.raises(RuntimeError, match="timed out"):
        layout_diagram(spec)
