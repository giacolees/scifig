"""Distribution comparisons preserving raw observations."""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from scifig.core.specs import FigureSpec
from scifig.styles import ResolvedStyle
from scifig.templates._common import categories


def draw(ax: Axes, data: pd.DataFrame, spec: FigureSpec, style: ResolvedStyle) -> None:
    """Draw Tukey boxplots plus all observations with deterministic horizontal offsets."""
    order = categories(data, spec.x, spec.order)
    colors = style.color_map(order)
    arrays = [data.loc[data[spec.x] == name, spec.y].to_numpy(float) for name in order]
    boxes = ax.boxplot(
        arrays,
        positions=np.arange(len(order)),
        widths=0.48,
        patch_artist=True,
        showfliers=False,
        whis=1.5,
        medianprops={"color": "#222222", "linewidth": 1.1},
        whiskerprops={"linewidth": 0.8},
        capprops={"linewidth": 0.8},
        zorder=2,
    )
    for i, (name, values, box) in enumerate(zip(order, arrays, boxes["boxes"], strict=True)):
        box.set_facecolor(colors[name])
        box.set_alpha(0.3)
        # Offsets are a display aid only, with no RNG or vertical perturbation.
        offsets = (
            (((np.arange(len(values)) + 0.5) * 0.61803398875) % 1 - 0.5) * 0.26
            if len(values) > 1
            else np.array([0.0])
        )
        ax.scatter(
            i + offsets, values, s=9, color=colors[name], alpha=0.7, zorder=3, edgecolors="none"
        )
    ax.set_xticks(np.arange(len(order)), order)
    ax.grid(axis="y", zorder=0)
