"""Default typography and publication-sized presets."""

PRESETS = {
    "publication": {"single_column": 3.4, "double_column": 7.0, "font_size": 9.0},
    "neurips": {"single_column": 3.25, "double_column": 6.75, "font_size": 9.0},
    "journal": {"single_column": 3.5, "double_column": 7.2, "font_size": 9.0},
}


def typography_rc(family: str | None, size: float) -> dict:
    rc = {
        "font.family": family or "DejaVu Sans",
        "font.size": size,
        "text.usetex": False,
        "text.color": "#222222",
        "mathtext.fontset": "dejavusans",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.facecolor": "white",
        "axes.labelcolor": "#222222",
        "axes.titlecolor": "#222222",
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.7,
        "axes.axisbelow": True,
        "grid.color": "#999999",
        "grid.linewidth": 0.45,
        "grid.alpha": 0.5,
        "lines.linewidth": 1.4,
        "legend.frameon": False,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
        "hatch.color": "#333333",
        "hatch.linewidth": 0.7,
        "axes.labelsize": size,
        "axes.titlesize": size,
        "xtick.labelsize": size * 0.9,
        "ytick.labelsize": size * 0.9,
        "legend.fontsize": size * 0.9,
        "pdf.fonttype": 42,
        "svg.fonttype": "path",
        "svg.hashsalt": "scifig",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
    return rc
