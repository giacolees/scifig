# Synthetic figure gallery

Every number in this gallery is invented to demonstrate the API. The figures are **not actual research results** and do not establish comparisons between methods. Generate them with `python examples/make_gallery.py` from the repository root. Each YAML specification and its source CSV are under `examples/`; exports are written to `docs/gallery/` as PDF, SVG, and PNG.

| Family | Data and purpose | Preview |
| --- | --- | --- |
| Learning curve | Three synthetic runs per iteration and method; the line is the mean and the band is sample standard deviation. | [PNG](gallery/learning_curve.png) |
| Benchmark | One synthetic success value per task and method. | [PNG](gallery/benchmark.png) |
| Ablation | One synthetic value per configuration. | [PNG](gallery/ablation.png) |
| Distribution | Synthetic per-run observations. | [PNG](gallery/distribution.png) |
| Heatmap | A complete synthetic task-by-method grid. | [PNG](gallery/heatmap.png) |

Vector downloads:

- Learning curve: [PDF](gallery/learning_curve.pdf), [SVG](gallery/learning_curve.svg)
- Benchmark: [PDF](gallery/benchmark.pdf), [SVG](gallery/benchmark.svg)
- Ablation: [PDF](gallery/ablation.pdf), [SVG](gallery/ablation.svg)
- Distribution: [PDF](gallery/distribution.pdf), [SVG](gallery/distribution.svg)
- Heatmap: [PDF](gallery/heatmap.pdf), [SVG](gallery/heatmap.svg)

Colors are explicitly mapped to methods in applicable figures. Physical dimensions and export settings are in the specs; presets do not certify compliance with any venue.

The [architecture diagram gallery](diagrams.md#illustrative-gallery) adds an
illustrative ML pipeline, encoder–decoder with a skip connection, and a training
and inference system. These describe example structures, not empirical results.
