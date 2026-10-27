"""Reject malformed records before a parser can reinterpret or skip them."""

import pandas as pd
import pytest

from scifig import FigureSpec, validate
from scifig.core.data import DataError, load_data


@pytest.mark.parametrize("text", ["x,x\n1,2\n", "x,y\n1,2,3\n", "x,y\n1\n", "x,y\n\n"])
def test_malformed_csv_rows_are_not_silently_removed(tmp_path, text):
    path = tmp_path / "bad.csv"
    path.write_text(text)
    with pytest.raises(DataError):
        load_data(path)


def test_csv_preserves_identifiers_and_literal_na(tmp_path):
    path = tmp_path / "table.csv"
    path.write_text("method,score\n001,2\nNA,3\n")
    data = load_data(path)
    assert data["method"].tolist() == ["001", "NA"]
    assert validate(FigureSpec(type="ablation", x="method", y="score"), data) == []


def test_reserved_columns_and_blank_categories_fail():
    for data in [
        {"method": ["a"], "score": [1], "_lower": [0]},
        {"method": [" "], "score": [1]},
    ]:
        with pytest.raises(DataError):
            validate(FigureSpec(type="ablation", x="method", y="score"), pd.DataFrame(data))


def test_heatmap_saturation_and_category_crop_diagnosed():
    spec = FigureSpec(type="heatmap", x="x", y="y", value="z", color_limits=(0, 1), xlim=(0.1, 1))
    messages = validate(spec, {"x": ["a"], "y": ["b"], "z": [2]})
    assert any("saturate" in item for item in messages)
    assert any("categorical" in item for item in messages)
