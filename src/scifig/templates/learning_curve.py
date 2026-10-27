"""Learning dynamics with explicit uncertainty bands."""

import pandas as pd
from matplotlib.axes import Axes

from scifig.core.specs import FigureSpec
from scifig.styles import ResolvedStyle
from scifig.templates._common import categories

_MARKERS = ("o", "s", "^", "D", "v", "P", "X")
_LINES = ("-", "--", "-.", ":")


def draw(ax: Axes, data: pd.DataFrame, spec: FigureSpec, style: ResolvedStyle) -> None:
    """Draw sorted curves without interpolation, smoothing, or implicit aggregation."""
    names = categories(data, spec.group, spec.group_order) if spec.group else [spec.y]
    colors = style.color_map(names)
    for i, name in enumerate(names):
        frame = data[data[spec.group].astype(str) == name] if spec.group else data
        frame = frame.sort_values(spec.x, kind="stable")
        ax.plot(
            frame[spec.x],
            frame[spec.y],
            label=name,
            color=colors[name],
            linestyle=_LINES[i % len(_LINES)],
            marker=_MARKERS[i % len(_MARKERS)],
            markersize=3,
            markevery=max(1, len(frame) // 7),
            zorder=3,
        )
        if "_lower" in frame:
            ax.fill_between(
                frame[spec.x].to_numpy(dtype=float),
                frame["_lower"].to_numpy(dtype=float),
                frame["_upper"].to_numpy(dtype=float),
                color=colors[name],
                alpha=0.16,
                linewidth=0,
                zorder=2,
            )
    ax.grid(axis="y", zorder=0)
