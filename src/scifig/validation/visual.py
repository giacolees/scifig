"""Heuristic checks on rendered figure geometry and typography."""

from matplotlib.figure import Figure
from matplotlib.text import Text


def check_visual(figure: Figure) -> list[str]:
    """Draw the figure and return actionable, non-fatal visual diagnostics."""
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    bounds = figure.bbox
    messages: list[str] = []
    small = False
    outside = False
    # Matplotlib retains Tick text objects outside the view, but does not draw
    # them. Ignore those objects while still checking visible tick label extents.
    hidden_ticks = set()
    for ax in figure.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            for tick in (*axis.get_major_ticks(), *axis.get_minor_ticks()):
                if not lo <= tick.get_loc() <= hi:
                    hidden_ticks.update((id(tick.label1), id(tick.label2)))
    for artist in figure.findobj(match=Text):
        if id(artist) in hidden_ticks or not artist.get_visible() or not artist.get_text().strip():
            continue
        if artist.get_fontsize() < 6:
            small = True
        box = artist.get_window_extent(renderer)
        if (
            box.x0 < bounds.x0 - 1
            or box.y0 < bounds.y0 - 1
            or box.x1 > bounds.x1 + 1
            or box.y1 > bounds.y1 + 1
        ):
            outside = True
    if small:
        messages.append("Some visible text is smaller than 6 pt and may be difficult to read.")
    if outside:
        messages.append("Some visible text extends outside the figure and may be clipped.")
    for ax in figure.axes:
        if not ax.get_visible():
            continue
        if ax.get_label() != "<colorbar>" and (ax.bbox.width < 40 or ax.bbox.height < 40):
            messages.append("An axes is very small; check its readability.")
        for axis in (ax.xaxis, ax.yaxis):
            boxes = [
                label.get_window_extent(renderer)
                for label in axis.get_ticklabels()
                if id(label) not in hidden_ticks
                and label.get_visible()
                and label.get_text().strip()
            ]
            if any(a.overlaps(b) for i, a in enumerate(boxes) for b in boxes[i + 1 :]):
                messages.append("Tick labels overlap; increase space or reduce labels.")
    return list(dict.fromkeys(messages))
