---
name: scientific-figures
description: Create reproducible publication-sized scientific figures with scifig from supplied research data, including learning curves, benchmarks, ablations, distributions, heatmaps and architecture diagrams. Use for research figures and conceptual model diagrams, not interactive dashboards.
---

# Scientific figures with scifig

Inspect the research objective and, for plots, the actual input table. Identify the claim or
comparison the figure should communicate, the measurement unit, experimental unit
(e.g. independent seed versus repeated checkpoint), grouping and uncertainty.
Never invent measurements, uncertainty, sample sizes or scientific claims. Ask for
missing semantics when they affect interpretation; label synthetic examples plainly.

For architecture diagrams, verify components, connections, labels and any tensor shapes
against supplied code, documentation or the user. Never invent connections or tensor
dimensions; distinguish a conceptual illustration from measured results. Use the
architecture diagram API and consult `docs/diagrams.md` for layout and validation.
Graphviz layout requires the external `dot` executable; manual layout does not.
Shape diagnostics check supplied declarations only and do not infer a graph from code.

For data figures, choose an existing template before creating custom plotting code:

- Numeric trajectories: `learning_curve`; use bands only when justified.
- Method-by-task summaries: `benchmark`; compare like units on a zero-based bar axis.
- Named component removals: `ablation`; establish the full-model reference from data.
- Per-run spread or outliers: `distribution`; retain raw observations.
- Rectangular numeric relations: `heatmap`; choose normalization deliberately.

Read the installed scifig docs and examples for current options. Inspect the input
with Python, then save executable Python or YAML using the shared engine. Run
`scifig validate figure.yaml` before `scifig render figure.yaml` for YAML workflows.
For Python, use `validate` or inspect `result.diagnostics`. Never silently
remove observations, smooth, impute missing values, change aggregation, or treat
boxplot whiskers as confidence intervals. Sample `std`, `sem` and `ci95` explicitly
request means; the normal approximation in `ci95` requires scientific justification.
Prefer supplied bounds when an appropriate interval was computed upstream.

Use physical final dimensions, legible typography and restrained grids. Give
related figures an explicit shared category-to-color map; use markers or hatches
for redundant distinctions. Avoid generic AI aesthetics: excessive colors,
decorative gradients, shadows, 3D bars, crowded panels and oversized titles. Venue
presets are starting points, not certificates of compliance.

Render once and inspect the actual PNG using an available image-viewing tool,
at intended publication size. Check the represented graph and connections for diagrams; for plots check labels and units, clipped marks/intervals,
overlapping ticks, legend over data, grayscale contrast and the scientific meaning
of axes and interval definitions. A successful render or clean diagnostics do not
establish scientific correctness. If no image viewer is available, report that
visual inspection was not performed rather than claiming it passed.

Make at most two revision renders after the initial render (three total). Fix
observed defects and re-inspect after each revision. At the limit, report unresolved
issues and the specific change needed. Export PDF and SVG plus a PNG preview unless
the user requests fewer formats. Preserve input data, source specification and code,
execution command, dependency versions and the interval/aggregation explanation.
Deliver the outputs with caveats that affect their interpretation.

For Codex, a prompt can say: "$scientific-figures: compare DAgger, AggreVaTe and BC
learning dynamics from experiments.csv; preserve the script/spec and vector exports."
For Claude Code, use its installed skill mechanism or ask it to read this SKILL.md
and perform the same task. Use the host's available file, terminal and image tools;
do not assume the two agents expose identical tool APIs.
