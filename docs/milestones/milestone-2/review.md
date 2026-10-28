# Milestone 2 review

The canonical diagram pipeline is implemented. Automated checks and visual
inspection are complete. Human approval is pending in
[the milestone record](../milestone-2.json); technical success does not mark the
milestone PASSED. Milestone 3 is out of scope.

## Changes

- Added strict canonical semantic, layout-hint and presentation models with an
  explicit copying/revalidation boundary and optional internal provenance.
- Put manual and Graphviz algorithms behind a typed `LayoutEngine` protocol and
  fixed dispatcher. Pipeline orchestration owns conversion, engine selection,
  geometry validation, resolved drawing settings, diagnostics and warning emission.
- Drawing consumes canonical content and geometry. Preserved public APIs, native
  artists, style isolation, edge order, ports, groups, self-loops, exports and
  schema-version-1 layout sidecars. Supplied geometry can bypass engine invocation.
- Added geometry/reference/isolation/parity contracts and kept existing baselines.
  Independent Terra review prompted group-member containment checks and explicit
  adapter preconditions; legacy result constructor and checker compatibility have
  regression tests.

## Verification

Baseline commit: `85da967` (`main` before this change), clean working tree,
101 tests passing. All commands ran from the repository root with `.venv`.

| Command | Outcome |
| --- | --- |
| `.venv/bin/pytest -q` before changes | 101 passed |
| Focused IR/layout/spec tests | 23 passed |
| Focused original layout/rendering/visual/integration tests | 21 passed |
| Focused new pipeline tests after review fixes | 25 passed |
| `.venv/bin/pytest -q` final | 141 passed, no failures or skips |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 70 files already formatted |
| `.venv/bin/python -m build` | sdist and wheel built successfully |
| `.venv/bin/python docs/milestones/milestone-2/render_review.py before` | Six fixtures, no diagnostics |
| `.venv/bin/python docs/milestones/milestone-2/render_review.py after` | Six fixtures, no diagnostics |
| `.venv/bin/python docs/milestones/milestone-2/compare_review.py` | Six pixel-identical PNG pairs |

The full suite includes existing vector SVG checks (no raster images), PDF
TrueType font embedding, PDF/PNG physical dimensions, deterministic PDF/SVG/PNG
exports, sidecar schema/provenance and Python/YAML parity. Graphviz integration
checks ran with the installed executable; they remain conditional when unavailable.
No typing checker is configured. Interfaces were checked through annotations,
strict models and contract tests; no static typing result is claimed.

Environment: macOS 26.3 arm64, Python 3.12.2, scifig 0.2.0, Matplotlib 3.11.2,
NumPy 2.5.4, Pydantic 2.14.1, pytest 9.2.0, Ruff 0.17.3, build 1.6.1,
pypdf 6.21.3, Pillow 13.0.0, Graphviz 14.0.2 (20251019.1705).
Isolated builds resolved hatchling 1.33.0. The extracted built wheel was imported in an isolated Python process
and successfully rendered a manual diagram through the canonical pipeline.
`DiagramSpec.model_json_schema()` was compared against baseline commit `85da967`
and is identical. A direct ZIP import smoke check was replaced by extraction
because the package uses namespace subdirectories; the extracted wheel check passed.

## Visual review and artifacts

The retained [contact sheet](comparisons/contact-sheet.png) shows before, after,
and absolute difference images. All six pairs are pixel-identical; retained PDF/SVG/PNG/YAML/layout sidecars are also byte-identical. All six review PDFs embed TrueType fonts and all six SVGs contain no raster images. Individual
post-change previews were also inspected at their saved resolution for clipping,
labels, overlaps and routes:

| Fixture | Inspection |
| --- | --- |
| [Residual block](after/residual_block.png) | Shape details fit; identity and transform branches remain distinct |
| [Research workflow](after/research_workflow.png) | Wrapped question, feedback label, arrows and legend remain legible |
| [Encoder/decoder](after/encoder_decoder.png) | Skip route and two Add inputs remain visible |
| [ML pipeline](after/ml_pipeline.png) | Linear route and labels fit the short canvas |
| [Training/inference](after/training_inference.png) | Groups, loss update, weight-load path and frozen model remain clear |
| [Manual ports/loop](after/manual_ports_loop.png) | Cardinal ports and exterior feedback loop remain visible; group label fits |

No visual regressions or clipping were observed. PDF, SVG, PNG, portable YAML and
schema-version-1 layout JSON for every fixture are retained in `before/` and
`after/`. `comparisons/` contains the contact sheet, six raw difference images and
machine-readable pixel comparisons. These are Milestone 2 review artifacts;
existing `tests/baseline/` and `docs/gallery/` files were preserved.

Known limitations: visual diagnostics are geometry heuristics, not a semantic
architecture audit. Graphviz output/reproducibility depends on the recorded
engine/font/library environment. Canonical metadata/provenance are internal;
there is no source-location inference, nested containment or arbitrary plugin
registry. Direct layout adapters require validated canonical input; use pipeline
entry points for validation guarantees. No known blocking implementation issues.

## Human decision

The version-controlled JSON record remains `READY_FOR_HUMAN_REVIEW` with nullable
human decision, feedback and UTC approval timestamp. Only an explicit APPROVE
changes it to PASSED. REQUEST CHANGES records feedback as CHANGES_REQUESTED;
corrections must be verified and returned to review. Silence leaves it pending.
