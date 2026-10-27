"""A small explicit registry of Matplotlib template callables."""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.axes import Axes

    from scifig.core.specs import FigureSpec
    from scifig.styles import ResolvedStyle

Template = Callable[["Axes", "pd.DataFrame", "FigureSpec", "ResolvedStyle"], None]
_TEMPLATES: dict[str, Template] = {}
_DATA_FAMILIES: dict[str, str] = {}


def register_template(
    name: str, template: Template, *, data_family: str = "learning_curve", replace: bool = False
) -> None:
    """Register a template; accidental replacement is an error."""
    if not name or not name.isidentifier():
        raise ValueError("Template name must be a Python identifier.")
    if not callable(template):
        raise TypeError("Template must be callable.")
    if data_family not in {"learning_curve", "benchmark", "ablation", "distribution", "heatmap"}:
        raise ValueError("data_family must name one of the five built-in data contracts.")
    if name in _TEMPLATES and not replace:
        raise ValueError(f"Template {name!r} is already registered.")
    _TEMPLATES[name] = template
    _DATA_FAMILIES[name] = data_family


def get_data_family(name: str) -> str:
    """Return the built-in validation contract reused by a template."""
    get_template(name)
    return _DATA_FAMILIES[name]


def get_template(name: str) -> Template:
    """Resolve a registered template with an actionable error."""
    try:
        return _TEMPLATES[name]
    except KeyError:
        raise ValueError(
            f"Unknown template {name!r}; choose from {', '.join(list_templates())}."
        ) from None


def list_templates() -> list[str]:
    """Return registered template names in deterministic order."""
    return sorted(_TEMPLATES)
