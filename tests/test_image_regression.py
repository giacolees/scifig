"""Structural image regression independent of font rasterizer and Matplotlib minor version."""

import warnings
from pathlib import Path

import matplotlib.image as mpimg
import numpy as np
import pandas as pd
from matplotlib.testing.compare import compare_images

import scifig


def test_bar_image_colors_geometry_and_cross_render_reproducibility(tmp_path):
    data = pd.DataFrame({"task": ["Reach", "Place"], "score": [80, 40]})
    spec = {
        "type": "ablation",
        "x": "task",
        "y": "score",
        "order": ["Reach", "Place"],
        "style": {"colors": {"Reach": "#0072B2", "Place": "#D55E00"}},
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = scifig.render(spec, data)
        second = scifig.render(spec, data)
    # Pin axes geometry for the pixel baseline: constrained-layout spacing
    # changes between supported Matplotlib releases. Its behavior has separate
    # visual tests; this baseline covers marks, labels, and typography.
    for result in (first, second):
        result.figure.set_layout_engine("none")
        result.ax.set_position((0.15, 0.19, 0.83, 0.78))
        result.ax.set_ylim(0, 85)
    assert [tick.get_text() for tick in first.ax.get_xticklabels()] == ["Reach", "Place"]
    png = first.savefig(tmp_path / "first.png", dpi=100)
    other_png = second.savefig(tmp_path / "second.png", dpi=100)
    assert png.read_bytes() == other_png.read_bytes()
    assert (
        first.savefig(tmp_path / "first.svg").read_bytes()
        == second.savefig(tmp_path / "second.svg").read_bytes()
    )
    image = mpimg.imread(png)
    # Sample inside each bar well away from text, edges and grid lines.
    for x, y, expected in [(0, 30, (0, 114, 178)), (1, 20, (213, 94, 0))]:
        px, py = first.ax.transData.transform((x, y))
        actual = image[image.shape[0] - 1 - int(py), int(px), :3] * 255
        np.testing.assert_allclose(actual, expected, atol=3)
    assert image.shape[:2] == (
        int(first.figure.get_figheight() * 100),
        int(first.figure.get_figwidth() * 100),
    )
    # Tolerate font rasterization and minor layout shifts across supported
    # Matplotlib versions, while catching materially changed marks and layout.
    difference = compare_images(
        str(Path(__file__).parent / "baseline/ablation.png"), str(png), tol=15
    )
    assert difference is None, difference


def test_default_style_isolated_from_caller_typography():
    import matplotlib as mpl

    data = pd.DataFrame({"x": [0, 1], "y": [1, 2]})
    with mpl.rc_context({"font.family": "serif", "text.usetex": True, "grid.alpha": 1.0}):
        result = scifig.learning_curve(data, "x", "y")
        assert result.ax.xaxis.label.get_fontfamily() == ["DejaVu Sans"]
        assert not result.ax.xaxis.label.get_usetex()
        assert result.style.rc["grid.alpha"] == 0.5
        assert mpl.rcParams["text.usetex"]
