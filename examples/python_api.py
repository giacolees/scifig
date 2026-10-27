"""Make the synthetic learning curve with the Python interface."""

from pathlib import Path

import pandas as pd

from scifig import learning_curve

ROOT = Path(__file__).resolve().parent


def main():
    data = pd.read_csv(ROOT / "data" / "learning_curve.csv")
    result = learning_curve(
        data,
        x="iteration",
        y="success_pct",
        group="method",
        group_order=["DAgger", "AggreVaTe", "BC"],
        uncertainty="std",
        labels={
            "x": "Training",
            "y": "Success",
            "title": "Synthetic: imitation learning",
            "legend": "Method (mean ± SD)",
        },
        units={"x": "iterations", "y": "%"},
        style={
            "preset": "publication",
            "width": "single_column",
            "height": 2.8,
            "colors": {"DAgger": "#0072B2", "AggreVaTe": "#D55E00", "BC": "#009E73"},
        },
    )
    result.export(
        ROOT / ".." / "docs" / "gallery",
        stem="learning_curve_python",
        formats=["pdf", "svg", "png"],
        dpi=300,
    )
    print(result.diagnostics)


if __name__ == "__main__":
    main()
