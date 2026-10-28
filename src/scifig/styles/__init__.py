"""Physical figure styles and categorical color resolution."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import matplotlib as mpl
from matplotlib.colors import to_rgba

from .palettes import PALETTES, category_colors
from .typography import PRESETS, typography_rc

if TYPE_CHECKING:
    from scifig.core.specs import StyleSpec


@dataclass
class ResolvedStyle:
    """Resolved dimensions, Matplotlib settings, and categorical colors."""

    figsize: tuple[float, float]
    rc: dict[str, Any]
    colors: dict[str, str]
    palette: str = "accessible"
    preset: str = "publication"

    def color_map(self, categories: list[str]) -> dict[str, str]:
        """Return stable colors for the requested categories."""
        return category_colors(categories, self.palette, self.colors)


def list_styles() -> list[str]:
    """Return the names of built-in physical style presets."""
    return list(PRESETS)


def resolve_style(style: "StyleSpec | str" = "publication") -> ResolvedStyle:
    """Resolve a style spec or preset name without changing global settings."""
    # Import lazily to avoid circular imports when core models reference styles.
    if isinstance(style, str):
        from scifig.core.specs import StyleSpec

        style = StyleSpec(preset=style)
    try:
        preset = PRESETS[style.preset]
    except KeyError as exc:
        raise ValueError(f"Unknown style preset: {style.preset}") from exc
    if style.palette not in PALETTES:
        raise ValueError(f"Unknown palette: {style.palette}")
    width = preset[style.width] if isinstance(style.width, str) else float(style.width)
    height = float(style.height) if style.height is not None else width * 0.7
    if width <= 0 or height <= 0:
        raise ValueError("Figure dimensions must be positive")
    rc = typography_rc(style.font_family, style.font_size or preset["font_size"])
    for key, value in style.rc.items():
        if key == "backend" or (key == "text.usetex" and value):
            raise ValueError(f"Unsupported rc parameter: {key}")
        if key not in mpl.rcParams.validate:
            raise ValueError(f"Unknown rc parameter: {key}")
        try:
            mpl.rcParams.validate[key](value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid rc parameter {key}: {value!r}") from exc
        rc[key] = value
    for color in style.colors.values():
        to_rgba(color)
    return ResolvedStyle((width, height), rc, dict(style.colors), style.palette, style.preset)
