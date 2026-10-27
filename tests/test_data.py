import pandas as pd
import pytest

from scifig.core.data import DataError, load_data
from scifig.core.specs import FigureSpec
from scifig.validation.semantic import prepare_data, validate_data


def spec(**kwargs):
    return FigureSpec(type="benchmark", x="method", y="score", **kwargs)


def test_aggregate_and_intervals_preserve_input():
    source = pd.DataFrame({"method": ["b", "a", "a"], "score": [3, 1, 3]})
    with pytest.raises(DataError, match="duplicate"):
        validate_data(source, spec())
    prepared = prepare_data(source.iloc[1:], spec(uncertainty="sem"))
    assert prepared.loc[0, "score"] == 2
    assert prepared.loc[0, "_lower"] == 1
    assert prepared.loc[0, "_upper"] == 3
    assert list(source["score"]) == [3, 1, 3]


def test_bounds_and_heatmap_validation():
    frame = load_data({"method": ["a"], "score": [2], "lo": [3], "hi": [4]})
    with pytest.raises(DataError, match="bounds"):
        validate_data(frame, spec(uncertainty={"lower": "lo", "upper": "hi"}))
    grid = pd.DataFrame({"x": ["a", "a", "b"], "y": ["c", "d", "c"], "v": [1, 2, 3]})
    with pytest.raises(DataError, match="rectangular"):
        validate_data(grid, FigureSpec(type="heatmap", x="x", y="y", value="v"))


def test_invalid_numeric_collisions_and_diagnostics():
    with pytest.raises(DataError, match="collide"):
        validate_data(pd.DataFrame({"method": [1, "1"], "score": [1, 2]}), spec())
    with pytest.raises(DataError, match="finite"):
        validate_data(pd.DataFrame({"method": ["a"], "score": [float("nan")]}), spec())
    warnings = validate_data(pd.DataFrame({"method": ["a"], "score": [2]}), spec(ylim=(1, 1.5)))
    assert any("clip" in warning for warning in warnings)
    assert any("zero" in warning for warning in warnings)


@pytest.mark.parametrize("kind,expected", [("std", 2**0.5), ("sem", 1), ("ci95", 1.96)])
def test_sample_interval_formulas(kind, expected):
    frame = pd.DataFrame({"method": ["a", "a"], "score": [1, 3]})
    before = frame.copy(deep=True)
    options = spec(uncertainty=kind)
    result = prepare_data(frame, options)
    assert result.loc[0, "score"] == pytest.approx(2)
    assert result.loc[0, "_lower"] == pytest.approx(2 - expected)
    assert result.loc[0, "_upper"] == pytest.approx(2 + expected)
    assert any("independent" in message for message in validate_data(frame, options))
    pd.testing.assert_frame_equal(frame, before)


def test_bounds_are_absolute_and_source_is_unchanged():
    frame = pd.DataFrame({"method": ["a"], "score": [2], "lo": [1], "hi": [4]})
    before = frame.copy(deep=True)
    result = prepare_data(frame, spec(uncertainty={"lower": "lo", "upper": "hi"}))
    assert result.loc[0, "_lower"] == 1
    assert result.loc[0, "_upper"] == 4
    pd.testing.assert_frame_equal(frame, before)
    frame["_lower"] = 0
    with pytest.raises(DataError, match="reserved"):
        prepare_data(frame, spec(uncertainty="std"))


def test_group_grid_and_categories():
    frame = pd.DataFrame({"method": ["a", "a", "b"], "score": [1, 2, 3], "group": ["x", "y", "x"]})
    with pytest.raises(DataError, match="every x/group"):
        validate_data(frame, spec(group="group"))
    with pytest.raises(DataError, match="order"):
        validate_data(frame.iloc[:2], spec(group="group", order=["a", "b"]))


def test_log_interval_and_numeric_edge_cases():
    curve = FigureSpec(
        type="learning_curve",
        x="x",
        y="y",
        yscale="log",
        uncertainty={"lower": "lo", "upper": "hi"},
    )
    with pytest.raises(DataError, match="bounds must be positive"):
        validate_data(pd.DataFrame({"x": [1], "y": [1], "lo": [0], "hi": [2]}), curve)
    with pytest.raises(DataError, match="complex"):
        validate_data(pd.DataFrame({"method": ["a"], "score": [1 + 2j]}), spec())
    with pytest.raises(DataError, match="log scale"):
        validate_data(pd.DataFrame({"method": ["a"], "score": [1]}), spec(yscale="log"))
    with pytest.raises(DataError, match="nonfinite"):
        validate_data(
            pd.DataFrame({"method": ["a", "a"], "score": [1e308, 1e308]}), spec(aggregate="mean")
        )


def test_invalid_sample_and_irrelevant_options():
    frame = pd.DataFrame({"method": ["a"], "score": [1]})
    with pytest.raises(DataError, match="at least two"):
        validate_data(frame, spec(uncertainty="std"))
    with pytest.raises(DataError, match="median"):
        validate_data(frame, spec(uncertainty="std", aggregate="median"))
    with pytest.raises(DataError, match="color_limits"):
        validate_data(frame, spec(color_limits=(0, 1)))
    negative = validate_data(pd.DataFrame({"method": ["a"], "score": [-2]}), spec(ylim=(-3, -1)))
    assert any("zero" in message for message in negative)
