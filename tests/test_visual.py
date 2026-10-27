"""Tests for practical, deliberately heuristic visual diagnostics."""

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from scifig.validation.visual import check_visual


def figure():
    fig = Figure(figsize=(3, 2))
    FigureCanvasAgg(fig)
    return fig


def test_outside_annotation_and_small_text_are_reported():
    fig = figure()
    ax = fig.subplots()
    ax.annotate("outside", (1.3, 0.5), xycoords="axes fraction", annotation_clip=False)
    fig.text(0.5, 0.5, "small", fontsize=4)
    messages = check_visual(fig)
    assert any("outside" in message for message in messages)
    assert any("smaller" in message for message in messages)


def test_crowded_tick_labels_are_reported():
    fig = figure()
    ax = fig.subplots()
    ax.set_xticks([0.4, 0.41], ["long first label", "long second label"])
    assert any("overlap" in message for message in check_visual(fig))


def test_tiny_axes_are_reported():
    fig = figure()
    fig.add_axes([0.1, 0.1, 0.05, 0.05])
    assert any("very small" in message for message in check_visual(fig))


def test_out_of_range_ticks_and_colorbar_are_not_false_positives():
    fig = figure()
    fig.set_layout_engine("constrained")
    ax = fig.subplots()
    ax.set_xlim(0, 1)
    ax.set_xticks([-3, 0, 1, 4], ["off left", "zero", "one", "off right"])
    ax.set_xlim(0, 1)
    fig.colorbar(ax.imshow([[0, 1]], extent=(0, 1, 0, 1)), ax=ax)
    messages = check_visual(fig)
    assert not any("outside" in message or "very small" in message for message in messages)
