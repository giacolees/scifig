"""Internal diagram appearance tokens, independent of layout and semantics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DiagramAppearance:
    role_colors: dict[str, str]
    group_fill: str = "#F7F8FA"
    group_border: str = "#888888"
    secondary_text: str = "#555555"
    edge_color: str = "#444444"
    label_background: str = "white"
    grayscale_node: str = "#555555"
    node_tint: float = 0.08
    group_linewidth: float = 0.7
    edge_linewidth: float = 0.9
    node_linewidth: float = 0.8
    arrow_size: float = 8


_DEFAULT = DiagramAppearance(
    role_colors={
        "input": "#0072B2",
        "output": "#0072B2",
        "module": "#555555",
        "data": "#009E73",
        "store": "#009E73",
        "loss": "#D55E00",
        "operation": "#555555",
    }
)
_EDITORIAL = DiagramAppearance(
    role_colors={
        "input": "#587887",
        "output": "#587887",
        "module": "#535C60",
        "data": "#668479",
        "store": "#668479",
        "loss": "#A16F5F",
        "operation": "#535C60",
    },
    group_fill="#F8F9F8",
    group_border="#AAB2B0",
    secondary_text="#626B69",
    edge_color="#535C5A",
    node_tint=0.06,
)

EDGE_STYLES = {"data": "-", "gradient": "--", "control": ":", "feedback": "-."}


def diagram_appearance(preset: str) -> DiagramAppearance:
    return _EDITORIAL if preset == "editorial" else _DEFAULT
