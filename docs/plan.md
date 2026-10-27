# Implementation plan

1. Research the three reference repositories and licenses; review Matplotlib's
   styling, layout, artists, transforms and export documentation.
2. Build a working learning-curve slice: strict semantic specs, tabular validation,
   isolated publication style, Python and YAML interfaces, CLI and vector exports.
3. Extend the same engine with benchmark, ablation, distribution and heatmap
   templates; test scientific edge cases and deterministic rendering.
4. Add a bounded agent skill and exercise it on a realistic request using the
   explicitly synthetic example data.
5. Render and inspect a five-family gallery, complete contributor and user docs,
   run headless end-to-end tests, lint and packaging checks, and add CI.

## Architecture decisions

- One Matplotlib backend; composition and a small callable registry, no plugin framework.
- Strict Pydantic schemas separate semantics, styling and export; unknown options fail.
- pandas handles CSV/TSV/DataFrame ingestion; selected numeric fields must be finite.
- No silent dropping, interpolation or smoothing. Aggregation is opt-in and recorded.
- A lightweight result exposes native Figure/Axes and saves inside its style context.
- Direct Figure/Agg construction avoids pyplot/backend selection side effects.
- Explicit category-to-color maps can be shared across figures; redundant marks and
  hatches support grayscale. Palette exhaustion warns instead of implying uniqueness.
- Publication presets are editable starting points, never venue compliance claims.
- Semantic errors stop rendering; scientific caveats and visual diagnostics remain
  inspectable warnings. Visual checks cannot establish scientific validity.
- New original implementation: reference examples are studied, not vendored.

Progress and final verification results are recorded in docs/validation.md.

## Completion

All five phases are implemented. The working vertical slice was extended through
the same engine to five families; the agent workflow was independently exercised;
the gallery was rendered and visually inspected. Final verification: 57 passing
tests in both the locked environment and an isolated Python 3.11 wheel install,
Ruff passing, and wheel/source archive built. See [validation](validation.md).

## Diagram extension

Completed a separate graph spec and manual/optional Graphviz layout, native
Matplotlib vector artists, shared Python/YAML/CLI dispatch, graph/shape and visual
checks, and portable layout records. Three illustrative diagrams were rendered
and inspected. The updated skill was independently exercised against a supplied
forward function without inventing tensor dimensions. Version 0.2 adds no Python
runtime dependency; CI installs the optional layout executable for its gallery.
