# Reference research

Reviewed 2026-10-27 via the GitHub repository contents and source files at the commits below. These are design references, not dependencies or vendored material. No reference code, figures, data, or fonts are copied into this project.

## figures4papers

[ChenLiu-1996/figures4papers](https://github.com/ChenLiu-1996/figures4papers/tree/b709de17da7e8f9a72e51a5de5bced924a01eeab), commit `b709de17da7e8f9a72e51a5de5bced924a01eeab`.

- The [CellSpliceNet comparison script](https://github.com/ChenLiu-1996/figures4papers/blob/b709de17da7e8f9a72e51a5de5bced924a01eeab/figure_CellSpliceNet/plot_comparison.py) uses coordinated method colors, repeated metric panels, means and standard-deviation error bars, numeric labels, a frameless legend, and high-resolution output. [ImmunoStruct bars](https://github.com/ChenLiu-1996/figures4papers/blob/b709de17da7e8f9a72e51a5de5bced924a01eeab/figure_ImmunoStruct/plot_bars.py) allocate a separate panel to a shared legend and place ablations in horizontal bars.
- Strength: publication-oriented examples show complete, concrete comparisons and consistent visual hierarchy. Limitation: data, colors, axis limits, sizes and output paths are coupled to individual studies; scripts mutate global Matplotlib settings and assume Helvetica. They are examples, not a general plotting API. Some bar panels truncate the baseline; that choice should not be generalized without considering the visual implication.
- [License](https://github.com/ChenLiu-1996/figures4papers/blob/b709de17da7e8f9a72e51a5de5bced924a01eeab/LICENSE): CC BY-NC 4.0. Reuse of licensed material is restricted to noncommercial purposes; sharing requires attribution, license information, and indication of changes. Do not copy source or assets into a general-purpose implementation.

## Scientific Visualization: Python + Matplotlib

[rougier/scientific-visualization-book](https://github.com/rougier/scientific-visualization-book/tree/62fa569f30333c817c13e4dc757877c1192fd15a), commit `62fa569f30333c817c13e4dc757877c1192fd15a`.

- The [complex layout example](https://github.com/rougier/scientific-visualization-book/blob/62fa569f30333c817c13e4dc757877c1192fd15a/code/layout/complex-layout.py) uses GridSpec proportions to reserve space for explanatory text, a legend, and repeated square panels. The [direct annotation example](https://github.com/rougier/scientific-visualization-book/blob/62fa569f30333c817c13e4dc757877c1192fd15a/code/ornaments/annotation-direct.py) offsets labels in points and uses a light stroke to preserve contrast over marks. Other examples systematically cover coordinates, colors, scales, typography, and export.
- Strength: explains the mechanics behind layout and legibility, with focused runnable examples. Limitation: examples are demonstrations, often use hard-coded relative output paths, random sample data, local font assumptions and interactive display; they do not constitute an integrated production plotting library.
- [License](https://github.com/rougier/scientific-visualization-book/blob/62fa569f30333c817c13e4dc757877c1192fd15a/LICENSE.txt) distinguishes the book (CC BY-NC-SA 4.0: attribution, noncommercial use, and share-alike for adaptations) from code (two-clause BSD: retain copyright, conditions and disclaimer in source redistribution, and reproduce them in binary distribution materials). Assets and fonts may have separate rights. No code is copied here.

## ResearchFigure

[DaoD/ResearchFigure](https://github.com/DaoD/ResearchFigure/tree/a842e7c264beced66167fc113221e821ae7e3049), commit `a842e7c264beced66167fc113221e821ae7e3049`.

- [drawfigure.py](https://github.com/DaoD/ResearchFigure/blob/a842e7c264beced66167fc113221e821ae7e3049/drawfigure.py) includes shared-x line panels, grouped hatched bars, paired comparisons, and a dense embedding plot saved as a 300-dpi raster. Markers, line styles and hatches offer redundant group distinctions.
- Strength: approachable examples of common paper plots. Limitation: one monolithic script embeds data and output filenames, assumes absolute local font paths, imports PyTorch for a serialized embedding, and uses manually assigned tick labels. The README omits the PyTorch dependency; its scripts are tightly coupled to their data and environment.
- No license file or explicit grant was found in the repository tree at this revision. Treat code, images and bundled fonts as unavailable for copying or redistribution without separate permission; the fonts' own rights require independent verification.

## Principles for this project

1. Separate input data, style configuration and rendering; preserve consistent series colors and markers across related panels.
2. Start with physical output dimensions and readable type; allow layout to reserve space for labels and legends rather than relying on oversized canvases.
3. Display uncertainty when supplied, use explicit axis labels and sensible scales, and avoid hiding baseline choices. Use direct labels where they improve interpretation.
4. Offer vector output for text and simple marks, with selective rasterization or raster export for dense layers; avoid depending on a bundled or machine-specific font.
5. Use scoped Matplotlib settings, caller-controlled output paths, deterministic examples and explicit dependencies. Adapt general ideas independently rather than copying the reference implementations.
