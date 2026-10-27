"""Ablation comparisons as named bars with explicit ordering."""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from scifig.core.specs import FigureSpec
from scifig.styles import ResolvedStyle
from scifig.templates._common import categories, errors


def draw(ax: Axes, data: pd.DataFrame, spec: FigureSpec, style: ResolvedStyle) -> None:
    """Draw ablation values; never infer a full-model baseline or improvement direction."""
    order = categories(data, spec.x, spec.order)
    frame = data.set_index(spec.x).loc[order].reset_index()
    colors = style.color_map(order)
    bars = ax.bar(
        np.arange(len(order)),
        frame[spec.y],
        color=[colors[name] for name in order],
        edgecolor="#333333",
        linewidth=0.5,
        yerr=errors(frame, spec.y),
        capsize=2,
        error_kw={"linewidth": 0.8},
        zorder=3,
    )
    if spec.annotate:
        ax.bar_label(bars, fmt="%.2g", padding=3)
    ax.set_xticks(np.arange(len(order)), order)
    ax.grid(axis="y", zorder=0)
