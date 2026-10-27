"""Exercise native diagram artists, reproducible export, and input isolation."""

import json
import shutil
from copy import deepcopy

import matplotlib as mpl
import pytest
from matplotlib.patches import FancyArrowPatch

import scifig


def test_text_remains_readable_with_caller_dark_style():
    with mpl.rc_context({"text.color": "white", "axes.labelcolor": "white"}):
        result = scifig.architecture(**manual_graph())
        assert all(text.get_color() != "white" for text in result.ax.texts)
        assert mpl.rcParams["text.color"] == "white"


def manual_graph():
    return {
        "nodes": {
            "a": {"label": "Input", "role": "input", "position": [1, 1]},
            "b": {"label": "Model", "position": [3, 1]},
            "c": {"label": "Output", "role": "output", "position": [5, 1]},
        },
        "edges": [
            {"source": "a", "target": "b", "label": "signal", "kind": "data"},
            {"source": "b", "target": "c", "label": "gradient", "kind": "gradient"},
        ],
        "layout": "manual",
    }


def test_manual_artists_and_input_isolation_without_graphviz(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    graph = manual_graph()
    original = deepcopy(graph)
    mpl.get_backend()  # Resolve Matplotlib's lazy backend before comparing rcParams.
    before = mpl.rcParams.copy()
    result = scifig.architecture(**graph)
    assert graph == original
    assert dict(mpl.rcParams) == dict(before)
    assert result.axes == [result.ax]
    assert result.figure.get_size_inches() == pytest.approx([7, 3])
    assert result.layout.engine == "manual"
    assert set(result.layout.nodes) == {"a", "b", "c"}
    labels = [text.get_text() for text in result.ax.texts]
    for label in ("Input", "Model", "Output", "signal", "gradient"):
        assert label in labels
    for node_id, label in (("a", "Input"), ("b", "Model"), ("c", "Output")):
        text = next(item for item in result.ax.texts if item.get_text() == label)
        assert text.get_position() == pytest.approx(result.layout.nodes[node_id].center)
    arrows = [patch for patch in result.ax.patches if isinstance(patch, FancyArrowPatch)]
    assert len(arrows) == 2
    assert arrows[0].get_linestyle() != arrows[1].get_linestyle()
    assert all(arrow.get_arrowstyle() is not None for arrow in arrows)
    result.spec.nodes["a"].label = "Edited"
    assert graph == original


def test_export_and_layout_sidecar(tmp_path):
    result = scifig.architecture(**manual_graph())
    pdf, svg, png = result.export(tmp_path, stem="diagram")
    assert pdf.read_bytes().startswith(b"%PDF")
    assert b"<svg" in svg.read_bytes()[:1000]
    assert b"<image" not in svg.read_bytes()
    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    path = result.save_layout(tmp_path / "layout.json")
    layout = json.loads(path.read_text())
    assert layout["engine"] == "manual"
    assert set(layout["nodes"]) == {"a", "b", "c"}
    pypdf = pytest.importorskip("pypdf")
    page = pypdf.PdfReader(pdf).pages[0]
    fonts = page["/Resources"]["/Font"].get_object()
    assert fonts
    font = next(iter(fonts.values())).get_object()
    descriptor = font["/DescendantFonts"][0].get_object()["/FontDescriptor"].get_object()
    assert "/FontFile2" in descriptor


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz unavailable")
def test_graphviz_render_uses_routed_geometry():
    result = scifig.architecture(
        nodes={"a": {"label": "A"}, "b": {"label": "B"}},
        edges=[{"source": "a", "target": "b", "label": "edge"}],
    )
    assert result.layout.engine == "graphviz"
    assert result.layout.engine_version
    assert result.layout.edges[0].curved
    assert any(text.get_text() == "edge" for text in result.ax.texts)
    assert any(isinstance(patch, FancyArrowPatch) for patch in result.ax.patches)


def test_manual_self_loop_is_visible_and_feedforward_rejects_cycle():
    graph = {
        "nodes": {"a": {"label": "A", "position": [1, 1]}},
        "edges": [{"source": "a", "target": "a", "kind": "feedback"}],
        "layout": "manual",
    }
    result = scifig.architecture(**graph)
    route = result.layout.edges[0]
    assert route.curved and len(set(route.points)) > 2
    assert len(result.edge_artists) == 1
    with pytest.raises(ValueError, match="cycle"):
        scifig.architecture(**graph, feedforward=True)
