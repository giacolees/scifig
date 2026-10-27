"""Color palettes and deterministic categorical assignments."""

import hashlib
import warnings

from matplotlib.colors import to_rgba

# Okabe-Ito palette, excluding yellow for legibility on a white background.
PALETTES = {
    "accessible": ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"),
    "grayscale": ("#111111", "#555555", "#888888", "#BBBBBB"),
}


def category_colors(
    categories: list[str], palette: str, explicit: dict[str, str]
) -> dict[str, str]:
    """Assign colors reproducibly, with explicit mappings taking precedence."""
    categories = list(dict.fromkeys(categories))
    if explicit:
        missing = [category for category in categories if category not in explicit]
        if missing:
            raise ValueError(f"Explicit colors do not cover categories: {missing}")
        result = {category: explicit[category] for category in categories}
    else:
        choices = PALETTES[palette]
        if len(categories) > len(choices):
            warnings.warn(
                "Palette exhausted; categories will share colors.", UserWarning, stacklevel=2
            )
        result = {
            category: choices[
                int.from_bytes(hashlib.sha256(category.encode("utf-8")).digest(), "big")
                % len(choices)
            ]
            for category in categories
        }
    normalized = [to_rgba(color) for color in result.values()]
    if len(normalized) != len(set(normalized)):
        warnings.warn(
            "Categories have duplicate colors; use an explicit mapping or redundant encodings.",
            UserWarning,
            stacklevel=2,
        )
    return result
