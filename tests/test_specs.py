import pytest
from pydantic import ValidationError

from scifig.core.specs import FigureSpec, load_spec


def test_paths_are_relative_to_yaml(tmp_path):
    config = tmp_path / "plot.yaml"
    config.write_text(
        "type: benchmark\nx: method\ny: score\ndata: data.csv\nexport:\n  directory: output\n"
    )
    spec = load_spec(config)
    assert spec.data == tmp_path / "data.csv"
    assert spec.export.directory == tmp_path / "output"


def test_strict_spec_rejects_bad_fields_and_shared_defaults():
    with pytest.raises(ValidationError):
        FigureSpec(type="benchmark", x="a", y="b", typo=True)
    with pytest.raises(ValidationError):
        FigureSpec(type="benchmark", x="a", y="b", export={"stem": "../outside"})
    with pytest.raises(ValidationError):
        FigureSpec(type="benchmark", x="a", y="b", ylim=(0, float("inf")))
    a = FigureSpec(type="benchmark", x="a", y="b")
    b = FigureSpec(type="benchmark", x="a", y="b")
    a.labels["x"] = "changed"
    assert b.labels == {}


def test_yaml_wrapper_and_duplicate_keys(tmp_path):
    path = tmp_path / "spec.yaml"
    path.write_text("figure:\n  type: benchmark\n  x: name\n  y: score\n")
    assert load_spec(path).x == "name"
    path.write_text("figure:\n  type: benchmark\n  x: a\n  x: b\n  y: score\n")
    with pytest.raises(ValueError, match="duplicate YAML key"):
        load_spec(path)
    path.write_text("figure: {type: benchmark, x: a, y: b}\nextra: 1\n")
    with pytest.raises(ValueError, match="sibling"):
        load_spec(path)


def test_model_rejects_invalid_values():
    for options in [
        {"style": {"height": 0}},
        {"style": {"width": -1}},
        {"export": {"dpi": 71}},
        {"annotations": [{"text": "a", "x": 1, "y": float("nan")}]},
        {"xscale": "logarithmic"},
    ]:
        with pytest.raises(ValidationError):
            FigureSpec(type="benchmark", x="a", y="b", **options)
