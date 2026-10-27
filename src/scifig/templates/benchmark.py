"""Grouped categorical comparisons with zero-based bars."""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from scifig.core.specs import FigureSpec
from scifig.styles import ResolvedStyle
from scifig.templates._common import categories, errors

_HATCHES = ("", "//", "..", "xx", "\\\\", "++", "oo")


def draw(ax: Axes, data: pd.DataFrame, spec: FigureSpec, style: ResolvedStyle) -> None:
    """Draw a complete grouped comparison, with optional supplied/computed intervals."""
    order = categories(data, spec.x, spec.order)
    names = categories(data, spec.group, spec.group_order) if spec.group else [spec.y]
    colors = style.color_map(names)
    width = 0.8 / len(names)
    for i, name in enumerate(names):
        frame = data[data[spec.group].astype(str) == name] if spec.group else data
        frame = frame.set_index(spec.x).loc[order].reset_index()
        positions = np.arange(len(order)) + (i - (len(names) - 1) / 2) * width
        bars = ax.bar(
            positions,
            frame[spec.y],
            width=width,
            label=name,
            color=colors[name],
            edgecolor="#333333",
            linewidth=0.5,
            hatch=_HATCHES[i % len(_HATCHES)],
            yerr=errors(frame, spec.y),
            capsize=2,
            error_kw={"linewidth": 0.8},
            zorder=3,
        )
        if spec.annotate:
            ax.bar_label(bars, fmt="%.2g", padding=3)
    ax.set_xticks(np.arange(len(order)), order)
    ax.grid(axis="y", zorder=0)
