"""Verify diagram appearance and style precedence across presets."""

import warnings

import matplotlib as mpl
import pytest
from matplotlib.colors import to_rgba

from scifig.core.specs import StyleSpec
from scifig.diagrams.rendering import render_diagram
from scifig.diagrams.specs import DiagramSpec
from scifig.styles import list_styles, resolve_style


def diagram(style):
    return DiagramSpec.model_validate(
        {
            "nodes": {
                "a": {"label": "Input", "role": "input", "position": [1, 1]},
                "b": {"label": "Model", "position": [3, 1], "frozen": True},
            },
            "edges": [
                {"source": "a", "target": "b", "kind": kind}
                for kind in ("data", "gradient", "control", "feedback")
            ],
            "groups": {"train": {"label": "Train", "nodes": ["b"], "role": "training"}},
            "layout": "manual",
            "style": style,
        }
    )


def render(style):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return render_diagram(diagram(style))


def test_editorial_retains_physical_typography_defaults():
    editorial = resolve_style("editorial")
    publication = resolve_style("publication")
    assert "editorial" in list_styles()
    assert editorial.figsize == publication.figsize
    assert editorial.rc == publication.rc
    assert editorial.preset == "editorial"


def test_preset_appearance_and_semantic_lines():
    old = render("publication")
    new = render("editorial")
    assert old.node_artists["a"].get_edgecolor() == pytest.approx(to_rgba("#0072B2"))
    assert old.node_artists["b"].get_edgecolor() == pytest.approx(to_rgba("#555555"))
    assert old.group_artists["train"].get_facecolor() == pytest.approx(to_rgba("#F7F8FA"))
    assert old.edge_artists[0].get_edgecolor() == pytest.approx(to_rgba("#444444"))
    assert old.node_artists["a"].get_linewidth() == 0.8
    assert new.node_artists["a"].get_edgecolor() == pytest.approx(to_rgba("#587887"))
    assert new.group_artists["train"].get_facecolor() == pytest.approx(to_rgba("#F8F9F8"))
    for result in (old, new):
        assert [edge.get_linestyle() for edge in result.edge_artists] == ["-", "--", ":", "-."]
        assert result.node_artists["b"].get_linestyle() == "--"
        assert result.group_artists["train"].get_linestyle() == "--"


def test_explicit_and_grayscale_precedence():
    explicit = render(
        StyleSpec(preset="editorial", palette="grayscale", colors={"a": "red", "b": "blue"})
    )
    assert explicit.node_artists["a"].get_edgecolor() == pytest.approx(to_rgba("red"))
    assert explicit.node_artists["b"].get_edgecolor() == pytest.approx(to_rgba("blue"))
    gray = render(StyleSpec(preset="editorial", palette="grayscale"))
    assert all(
        node.get_edgecolor() == pytest.approx(to_rgba("#555555"))
        for node in gray.node_artists.values()
    )
    with pytest.raises(ValueError, match="cover"):
        render(StyleSpec(preset="editorial", colors={"a": "red"}))


def test_render_and_export_leave_rc_unchanged(tmp_path):
    mpl.get_backend()
    before = mpl.rcParams.copy()
    result = render("editorial")
    result.export(tmp_path, formats=["svg", "png"])
    assert dict(mpl.rcParams) == dict(before)
