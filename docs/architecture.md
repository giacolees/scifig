# Architecture and extension contract

Python convenience functions construct the same `FigureSpec` consumed by YAML.
`render(spec, data=None)` loads and validates data, prepares an explicit statistical
summary, resolves a style, invokes a registered template, decorates axes, and
returns `FigureResult`. The result exposes `.figure`, `.ax`, `.axes`, `.spec`,
`.diagnostics`, `.savefig()` and `.export()`.

Pydantic rejects unknown keys. Paths in YAML are relative to the YAML file, not the
shell directory. Templates receive a copy of validated data, an Axes, a spec and
resolved style. A dictionary registry provides extension without a backend or
plugin abstraction. The source table is never modified.

## Data contracts

All families use long tables. Learning curves use numeric x/y with optional group;
benchmarks use categorical x, numeric y and optional group; ablations use categorical
x and numeric y; distributions use categorical x and numeric y (raw observations);
heatmaps use categorical x/y and numeric value, exactly one row per cell and a
complete rectangular grid. Duplicates in summary cells fail unless aggregation
is explicitly requested. Sorting categories is deterministic; `order` and
`group_order` override it and must include exactly observed categories.

`aggregate` defaults to `none`. `mean` and `median` are explicit choices.
`uncertainty: std|sem|ci95` explicitly requests mean plus sample-based intervals
and requires at least two observations per cell. ci95 is a normal approximation,
warns about assumptions, and is not claimed to establish run independence.
`uncertainty: {lower: lo, upper: hi}` accepts provided absolute endpoints, requires
one row per cell, and checks lower <= y <= upper. No interpolation or smoothing.

Raw CSV/TSV records are read without type inference or skipped rows; numeric
conversion belongs to the semantic layer, preserving category IDs such as `001`.
Duplicate headers, uneven rows, empty categories and reserved `_lower`/`_upper`
columns fail. Numerical overflow and nonpositive log intervals fail. Bar log axes
are rejected because zero baselines are undefined. Any explicit bar limits
excluding zero, categorical cropping and heatmap color saturation are diagnosed.
Group grids must be complete for grouped benchmarks. `row_order` controls heatmap
rows independently of columns; outside legends can reserve space above data.

The registry accepts a `data_family` naming one of the five existing contracts for
custom templates. A genuinely different data contract requires an explicit semantic
validator change; registration never bypasses validation.

## Rendering boundaries

Styles resolve physical inches, font points, palette and rcParams. Matplotlib
Figure/Agg is created and drawn in rc_context. Save repeats that context so delayed
backend settings (PDF fonts, SVG text/paths) are honored. Constrained layout handles
labels and legends without changing the requested canvas dimensions; automatic
tight cropping is avoided. PDF uses TrueType embedding; SVG defaults to paths for
portable viewing, optionally editable text. Vector bar/line/mesh artists stay vector.
Visual checks inspect drawn text and axes, but are heuristics, not a scientific audit.

Figure creation is reproducible for a fixed environment and inputs; PDF/SVG time
metadata and SVG IDs are stabilized by package-managed export. Concurrent Matplotlib
use across threads is not supported; use separate processes. Native artist edits
remain possible and callers must repeat validation after their own changes.

## Architecture diagrams (0.2)

`DiagramSpec` models nodes, directed edges and groups separately from tabular
`FigureSpec`. The public `render`, `validate` and YAML loader dispatch on that
explicit semantic choice; the CLI commands remain unchanged. Both paths use
scoped Matplotlib styling and the same PDF/SVG/PNG exporter. A separate lightweight
`DiagramResult` exposes native artists and geometry without forcing a graph into
a DataFrame or adding a generic rendering-backend hierarchy.

Manual coordinates work with core dependencies alone. Optional Graphviz supplies
geometry through its JSON output; it does not render the final figure. Internal
DOT IDs and quoted labels keep user text separate from graph syntax. The subprocess
has a timeout and actionable dependency errors. Layout sidecars record geometry,
the source spec, scifig/Matplotlib versions and the external engine version.
Typography remains in final-size points even as geometry fits the requested
canvas, so crowding is diagnosed rather than hidden through automatic font shrinking.

Known identity/add shape contradictions and declared feedforward cycles fail;
missing shapes and unverifiable symbolic dimensions remain advisory. Membership
is flat and disjoint. Visual checks inspect label fit, node/group overlap and
routes crossing unrelated nodes. Complex manual routing, nested groups, general
shape inference and tracing code into a graph are deliberately outside this slice.

## Canonical diagram pipeline (Milestone 2)

Diagrams now follow `DiagramSpec → CanonicalDiagram → LayoutEngine →
DiagramGeometry → Matplotlib artists → validation`. The YAML schema, defaults,
public `render(spec)` / `architecture(...)` APIs, and CLI remain compatible.
`layout_diagram(spec)` and `render_diagram(spec)` remain available from their
existing modules as wrappers around `diagrams.pipeline` orchestration.

`diagrams.ir.diagram_to_ir` is the explicit conversion boundary. It serializes
and revalidates mutable specifications, then copies semantic nodes, ordered
edges, and flat groups into strict Pydantic models. Shared role, edge-kind,
operation and cardinal-port types are reused. Node sizes/positions and layout
engine/direction live in layout hints; labels/title live in presentation.
Tensor shapes, operations, frozen flags and feedforward declarations retain
their meaning. Edge indices are stable list indices, including parallel edges.
Canonical validation checks references, disjoint membership, exact hint/label
coverage, edge ordering and the existing semantic constraints. Optional internal
metadata/provenance are copied without adding YAML keys or fabricating source
locations. Canonical models contain no computed geometry or original `NodeSpec`.

`pipeline.prepare_diagram` resolves style, colors and appearance without invoking
an engine. `pipeline.layout_canonical` revalidates canonical input, selects
`ManualLayoutEngine` or `GraphvizLayoutEngine` through a fixed dispatcher, and
validates the returned geometry. `LayoutEngine` is a small typed protocol;
adapters assume validated canonical input and implement layout only. New engines
require an explicit dispatcher/schema change and contract tests; there is no
plugin registry or new dependency. Manual positions and requested sizes are in
inches and convert to points at layout (72 points/inch). All computed centers,
sizes, route points, label positions, arrow tips and bounds use points. Cubic
routes contain 1 + 3n points; arrow tips remain separate from spline controls.

`diagrams.validation.validate_geometry` requires exact node/group coverage, edge
count/order, finite coordinate pairs, positive sizes and ordered nondegenerate
bounds. It checks routes, enclosing diagram bounds, and group containment of
members. A 0.1 point containment tolerance accommodates Graphviz JSON rounding.
Malformed engine output fails before drawing. Visual relationship checks live
in the same validation module; the existing rendering-module import remains
available. The checks retain their advisory, heuristic nature.

`rendering.render_geometry` draws canonical content with validated geometry and
resolved presentation settings. The original validated spec snapshot is retained
on `DiagramResult` for export configuration and schema-version-1 sidecars;
`result.diagram` additionally exposes the canonical snapshot. Existing positional
result constructor arguments are preserved. `render_diagram(spec, geometry=...)`
uses a validated copy of supplied geometry without invoking a layout engine.
This is the supported entry point for reusing geometry; sidecars remain records,
not a new input format. Callers who edit native artists must rerun visual checks.

No typing checker is configured in this repository. Typed interfaces are covered
by annotations and contract tests, rather than a claimed static type-check pass.
The [Milestone 2 review report](milestones/milestone-2/review.md) records technical
verification and the separate pending human approval gate.
