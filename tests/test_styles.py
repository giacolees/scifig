import warnings

import matplotlib as mpl
import pytest

from scifig.core.specs import StyleSpec
from scifig.styles import list_styles, resolve_style


def test_style_dimensions_and_rc_are_scoped():
    before = mpl.rcParams["font.size"]
    style = resolve_style(StyleSpec(width=4.0, height=2.0, font_size=11.0))
    assert style.figsize == (4.0, 2.0)
    assert style.rc["font.size"] == 11
    assert mpl.rcParams["font.size"] == before
    assert {"publication", "neurips", "journal"} <= set(list_styles())


def test_stable_color_mapping_and_explicit_validation():
    style = resolve_style("publication")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        both = style.color_map(["alpha", "beta"])
        assert style.color_map(["beta", "alpha"]) == both
        assert style.color_map(["alpha"])["alpha"] == both["alpha"]
    style = resolve_style(StyleSpec(colors={"alpha": "red"}))
    with pytest.raises(ValueError, match="cover"):
        style.color_map(["beta"])
    with pytest.raises(ValueError):
        resolve_style(StyleSpec(colors={"x": "not-a-color"}))
    with pytest.raises(ValueError):
        resolve_style(StyleSpec(rc={"backend": "agg"}))


def test_duplicate_explicit_colors_warn():
    style = resolve_style(StyleSpec(colors={"a": "red", "b": "#ff0000"}))
    with pytest.warns(UserWarning, match="duplicate colors"):
        style.color_map(["a", "b"])


def test_invalid_style_rc_preserves_matplotlib_settings():
    before = mpl.rcParams["font.size"]
    with pytest.raises(ValueError, match="Unknown rc"):
        resolve_style(StyleSpec(rc={"font.size": 22, "bad.key": 1}))
    assert mpl.rcParams["font.size"] == before
