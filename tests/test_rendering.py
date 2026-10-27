import warnings

import matplotlib as mpl
import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection, QuadMesh

import scifig
from scifig import FigureSpec, FigureWarning
from scifig.core.data import DataError


def quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FigureWarning)
        return call(*args, **kwargs)


def test_learning_curve_artists_labels_legend_and_copy():
    frame = pd.DataFrame(
        {"step": [2, 1, 2, 1], "score": [4, 2, 5, 3], "model": ["a", "a", "b", "b"]}
    )
    original = frame.copy(deep=True)
    result = quiet(
        scifig.learning_curve,
        frame,
        "step",
        "score",
        group="model",
        labels={"x": "Epoch", "y": "Accuracy", "title": "Training", "legend": "Model"},
        units={"x": "epochs"},
        annotations=[{"text": "note", "x": 1, "y": 2}],
    )
    assert [line.get_label() for line in result.ax.lines] == ["a", "b"]
    np.testing.assert_allclose(result.ax.lines[0].get_xdata(), [1, 2])
    np.testing.assert_allclose(result.ax.lines[0].get_ydata(), [2, 4])
    assert result.ax.get_xlabel() == "Epoch (epochs)"
    assert result.ax.get_ylabel() == "Accuracy"
    assert result.ax.get_title() == "Training"
    assert result.ax.get_legend().get_title().get_text() == "Model"
    assert any(t.get_text() == "note" for t in result.ax.texts)
    pd.testing.assert_frame_equal(frame, original)


def test_bar_templates_and_distribution_values():
    frame = pd.DataFrame(
        {"method": ["b", "a", "b", "a"], "score": [4, 1, 3, 2], "group": ["g1", "g1", "g2", "g2"]}
    )
    result = quiet(scifig.benchmark, frame, "method", "score", group="group", annotate=True)
    assert [[p.get_height() for p in c.patches] for c in result.ax.containers] == [[1, 4], [2, 3]]
    assert result.ax.get_legend() is not None
    assert [t.get_text() for t in result.ax.get_xticklabels()] == ["a", "b"]
    assert len(result.ax.texts) == 4
    ablation = quiet(scifig.ablation, frame.iloc[:2], "method", "score", order=["b", "a"])
    assert [p.get_height() for p in ablation.ax.patches] == [4, 1]
    dist = quiet(scifig.distribution, frame, "method", "score")
    points = [a for a in dist.ax.collections if isinstance(a, PathCollection)]
    assert len(points) == 2
    np.testing.assert_allclose(np.sort(points[0].get_offsets()[:, 1]), [1, 2])
    np.testing.assert_allclose(np.sort(points[1].get_offsets()[:, 1]), [3, 4])


def test_heatmap_mesh_and_colorbar():
    data = {"col": ["a", "b", "a", "b"], "row": ["u", "u", "v", "v"], "value": [1, 2, 3, 4]}
    result = quiet(
        scifig.heatmap,
        data,
        "col",
        "row",
        "value",
        annotate=True,
        labels={"colorbar": "Rate"},
        units={"value": "%"},
    )
    mesh = next(a for a in result.ax.collections if isinstance(a, QuadMesh))
    np.testing.assert_allclose(np.asarray(mesh.get_array()).reshape(2, 2), [[1, 2], [3, 4]])
    assert not mesh.get_rasterized()
    assert len(result.axes) == 2
    assert result.axes[1].get_ylabel() == "Rate (%)"
    assert [t.get_text() for t in result.ax.texts] == ["1", "2", "3", "4"]


def test_yaml_api_equivalence(tmp_path):
    frame = pd.DataFrame({"epoch": [1, 2, 3], "score": [0.1, 0.3, 0.4]})
    frame.to_csv(tmp_path / "data.csv", index=False)
    config = tmp_path / "spec.yaml"
    config.write_text(
        "figure:\n  type: learning_curve\n  data: data.csv\n  x: epoch\n"
        "  y: score\n  labels: {x: Epoch, y: Score}\n"
    )
    from_yaml = quiet(scifig.render, scifig.load_spec(config))
    from_api = quiet(
        scifig.learning_curve, frame, "epoch", "score", labels={"x": "Epoch", "y": "Score"}
    )
    np.testing.assert_array_equal(
        from_yaml.ax.lines[0].get_xdata(), from_api.ax.lines[0].get_xdata()
    )
    np.testing.assert_array_equal(
        from_yaml.ax.lines[0].get_ydata(), from_api.ax.lines[0].get_ydata()
    )
    np.testing.assert_allclose(
        from_yaml.figure.get_size_inches(), from_api.figure.get_size_inches()
    )
    assert from_yaml.ax.get_xlabel() == from_api.ax.get_xlabel()
    assert from_yaml.spec.model_dump(exclude={"data", "export"}) == from_api.spec.model_dump(
        exclude={"data", "export"}
    )


def test_rc_restored_on_success_and_failure():
    before = mpl.rcParams.copy()
    quiet(
        scifig.learning_curve,
        {"x": [1, 2], "y": [2, 3]},
        "x",
        "y",
        style={"rc": {"axes.linewidth": 2.5}},
    )
    assert dict(mpl.rcParams) == dict(before)
    with pytest.raises(ValueError):
        quiet(
            scifig.learning_curve,
            {"x": [1, 2], "y": [2, 3]},
            "x",
            "y",
            style={"rc": {"this.is.not.valid": 1}},
        )
    assert dict(mpl.rcParams) == dict(before)

    def fail_inside_draw(ax, data, spec, style):
        assert mpl.rcParams["axes.linewidth"] == 2.5
        raise ValueError("template failed")

    scifig.register_template("failing_test", fail_inside_draw, replace=True)
    with pytest.raises(ValueError, match="template failed"):
        quiet(
            scifig.render,
            FigureSpec(type="failing_test", x="x", y="y", style={"rc": {"axes.linewidth": 2.5}}),
            {"x": [1], "y": [2]},
        )
    assert dict(mpl.rcParams) == dict(before)


def test_scientific_warnings_are_returned_and_emitted():
    data = {"x": [1, 1, 2, 2], "y": [1, 3, 2, 4]}
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", FigureWarning)
        result = scifig.learning_curve(data, "x", "y", uncertainty="sem")
    assert any("independent" in str(item.message) for item in captured)
    assert any("independent" in item for item in result.diagnostics)
    assert result.ax.collections  # uncertainty band


def test_custom_registration_reuses_selected_data_family():
    def draw(ax, data, spec, style):
        ax.scatter(data[spec.x], data[spec.y])

    scifig.register_template("custom_points_test", draw, data_family="learning_curve", replace=True)
    result = quiet(
        scifig.render,
        FigureSpec(type="custom_points_test", x="x", y="y"),
        {"x": [1, 2], "y": [2, 3]},
    )
    np.testing.assert_allclose(result.ax.collections[0].get_offsets(), [[1, 2], [2, 3]])
    with pytest.raises(DataError, match="numeric"):
        quiet(
            scifig.render,
            FigureSpec(type="custom_points_test", x="x", y="y"),
            {"x": ["bad"], "y": [2]},
        )


def test_outside_legend_and_api_input_path_are_preserved(tmp_path):
    path = tmp_path / "curve.csv"
    path.write_text("x,y,group\n0,1,a\n1,2,a\n0,2,b\n1,3,b\n")
    result = quiet(
        scifig.learning_curve,
        path,
        "x",
        "y",
        group="group",
        legend_loc="outside upper center",
        legend_columns=2,
    )
    assert result.spec.data == path.resolve()
    assert len(result.figure.legends) == 1
    result.savefig(tmp_path / "curve.png")
    legend = result.figure.legends[0].get_window_extent()
    assert legend.y0 > result.ax.bbox.y1
    with pytest.raises(ValueError, match="dpi"):
        result.savefig(tmp_path / "bad.png", dpi=0)


def test_heatmap_row_order_and_incorrect_order():
    table = {"x": ["a", "a"], "y": ["first", "second"], "v": [1, 2]}
    result = quiet(scifig.heatmap, table, "x", "y", "v", row_order=["second", "first"])
    assert [tick.get_text() for tick in result.ax.get_yticklabels()] == ["second", "first"]
    with pytest.raises(DataError, match="row_order"):
        quiet(scifig.heatmap, table, "x", "y", "v", row_order=["first"])


def test_heatmap_colorbar_and_cells_remain_vector(tmp_path):
    result = quiet(scifig.heatmap, {"x": ["a"], "y": ["b"], "v": [1]}, "x", "y", "v")
    assert b"<image" not in result.savefig(tmp_path / "heatmap.svg").read_bytes()
