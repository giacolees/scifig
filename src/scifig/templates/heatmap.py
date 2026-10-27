"""Vector-backed rectangular heatmaps."""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import Normalize

from scifig.core.specs import FigureSpec
from scifig.styles import ResolvedStyle
from scifig.templates._common import categories


def draw(ax: Axes, data: pd.DataFrame, spec: FigureSpec, style: ResolvedStyle) -> None:
    """Draw cells using pcolormesh, preserving vectors in PDF and SVG."""
    columns = categories(data, spec.x, spec.order)
    rows = categories(data, spec.y, spec.row_order)
    values = data.pivot(index=spec.y, columns=spec.x, values=spec.value).loc[rows, columns]
    limits = spec.color_limits
    norm = Normalize(vmin=limits[0], vmax=limits[1]) if limits else None
    mesh = ax.pcolormesh(
        np.arange(len(columns) + 1),
        np.arange(len(rows) + 1),
        values.to_numpy(float),
        cmap=spec.cmap,
        norm=norm,
        edgecolors="white",
        linewidth=0.5,
        rasterized=False,
        shading="flat",
    )
    ax.set_xticks(np.arange(len(columns)) + 0.5, columns)
    ax.set_yticks(np.arange(len(rows)) + 0.5, rows)
    ax.invert_yaxis()
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    colorbar = ax.figure.colorbar(mesh, ax=ax, pad=0.03, shrink=0.9)
    # Matplotlib rasterizes long colorbar meshes by default; keep this supported
    # layer vector as well as the scientific data cells.
    if colorbar.solids is not None:
        colorbar.solids.set_rasterized(False)
    label = spec.labels.get("colorbar", spec.value or "value")
    if unit := spec.units.get("value"):
        label += f" ({unit})"
    colorbar.set_label(label)
    if spec.annotate:
        for row in range(len(rows)):
            for col in range(len(columns)):
                value = float(values.iloc[row, col])
                r, g, b, _ = mesh.cmap(mesh.norm(value))
                color = "white" if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.48 else "#222222"
                ax.text(col + 0.5, row + 0.5, f"{value:.2g}", color=color, ha="center", va="center")
