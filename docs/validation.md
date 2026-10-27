# Validation record

Verified locally on 2026-10-27, macOS arm64. CI is configured for Linux and macOS,
Python 3.11–3.13; the remote workflow has not been run in this session.

## Automated checks

- Locked development environment: Python 3.12.2, Matplotlib 3.11.2, NumPy 2.5.4,
  pandas 3.1.0, Pydantic 2.14.1. `MPLBACKEND=Agg uv run pytest -q`: **57 passed**.
- Independently installed wheel: Python 3.11.14, Matplotlib 3.9.4, NumPy 1.26.4,
  pandas 2.2.3, Pydantic 2.9.2. All **57 tests passed**. The older Matplotlib
  environment reports upstream Pyparsing deprecation warnings.
- `uv run ruff check .` and `uv run ruff format --check .`: passed.
- `uv build`: wheel and source archive built successfully. The wheel contains
  all five templates, the typing marker and the MIT license.
- Skill frontmatter validated with the skill-creator `quick_validate.py` utility.

Coverage includes strict YAML and duplicate-key rejection; malformed CSV/TSV,
missing categories and nonfinite values; explicit aggregation and exact sample
interval formulas; supplied absolute bounds and log constraints; complete grids;
input immutability; color maps; categorical labels; native artist values; public
API/YAML equivalence; outside legends; rcParams restoration on success and failure;
headless CLI behavior; PDF/SVG/PNG headers; embedded PDF fonts; vector heatmap
colorbars; repeated-export determinism; and visual geometry diagnostics.

The image regression includes a checked-in 100-DPI ablation PNG. Its axes geometry
is fixed to distinguish artist/style changes from constrained-layout differences
between Matplotlib releases. An RMS tolerance of 15/255 allows observed font and
antialiasing differences; exact bar-color samples, category labels, numerical
artist values and repeat-render bytes are checked separately. Layout diagnostics
and real gallery inspection cover constrained layout. This is not a comprehensive
perceptual regression suite. Review intended visual changes before updating a
baseline; never update it simply to clear a failing test.

## Actual figures and visual review

`MPLBACKEND=Agg uv run python examples/make_gallery.py` generates five families,
each as PDF, SVG and PNG. All 15 primary exports exist and are nonempty. PDF page
inches match PNG dimensions at 300 DPI; every gallery SVG has vector marks and
contains no embedded raster image. Heatmap cells and colorbar both remain vector.
The learning-curve Python example produces the same PDF, SVG and PNG bytes as
its YAML counterpart within the locked environment.

All five previews were inspected. Review found and fixed categorical labels being
reset by scale initialization, a benchmark legend overlying bars, false visual
warnings for undrawn ticks, and Matplotlib's default rasterized colorbar. Examples
now use shared explicit method colors, readable category labels and restrained
styling. The learning-curve example intentionally emits an independence caveat;
other gallery examples have no reported diagnostics. All datasets are explicitly
synthetic and establish no real comparison between methods.

## Agent workflow

An independent Terra agent followed the final skill in an isolated workspace,
using the synthetic imitation-learning CSV. It preserved the input, YAML,
standalone Python, dependency versions and interval explanation; generated all
three export formats; inspected a real PNG; and retained the independence caveat.
It used two render passes, within the three-render bound. See
[the behavioral validation record](skill-validation.md).

This verifies the instruction workflow with available tools, not live installation
or invocation in a separate Codex or Claude Code product session.

## Reproduce

```bash
uv sync --locked --extra dev
MPLBACKEND=Agg uv run pytest -q
uv run ruff check .
uv run ruff format --check .
MPLBACKEND=Agg uv run python examples/make_gallery.py
MPLBACKEND=Agg uv run python examples/python_api.py
uv build
```

## Current limitations and next steps

- One main axes per built-in figure. Multi-panel composition should follow actual
  researcher use cases, using Matplotlib's existing GridSpec rather than a new backend.
- Only CSV/TSV and in-memory tables. Complete benchmark and heatmap grids are
  required; missing-cell semantics should be added explicitly when needed.
- Three simple sample estimators; no bootstrap, paired/hierarchical inference,
  run-ID validation or uncertainty for medians. Add those from concrete studies,
  with statistical tests and recorded assumptions.
- The system cannot determine independence, appropriate units, research claims,
  causal validity, or conference compliance from a table. Authors must review them.
- Automatic color hashes may collide and warn; explicit shared mappings are
  recommended. A palette does not guarantee every accessibility requirement.
- Geometry checks are heuristics; no full legend/data collision detector.
- Cross-platform and cross-version byte identity is not promised. Preserve data,
  specifications, code, fonts and environment locks. Matplotlib uses global rc
  settings temporarily; use separate processes for concurrent rendering.
- Custom templates reuse a registered built-in data contract. Novel contracts
  require an explicit semantic validator change; they cannot bypass validation.
- The source tree and distributions are ready locally; no remote repository,
  package-index release or live agent-host installation was performed.
