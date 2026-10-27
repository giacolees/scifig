# Python and declarative interfaces

The public functions `learning_curve`, `benchmark`, `ablation`, `distribution`, and
`heatmap` take `data, x, y` and keyword options from `FigureSpec`. Learning curves
and benchmarks accept `group`; heatmaps additionally require `value`.
`data` accepts a DataFrame, column mapping, list of records, or CSV/TSV path.
Selected numeric fields are converted to finite real numbers; unselected fields
are untouched. CSV/TSV category identifiers are preserved as strings. Empty or
uneven rows and duplicate headers fail rather than being skipped or reinterpreted.
The internal names `_lower` and `_upper` are reserved.

`render(FigureSpec(...), data=table)` and `render(load_spec("figure.yaml"))` run the
same pipeline. `validate(spec, data=None)` returns caveats without drawing; errors
raise `ValueError` (including the more specific `DataError` and Pydantic errors).
A YAML document may contain a single `figure:` wrapper or a bare figure mapping.
Unknown options and duplicate YAML keys fail. Save the source data with the spec.

`DiagramSpec`, `NodeSpec`, `EdgeSpec`, `GroupSpec`, and `architecture(nodes, edges,
**kwargs)` provide graph-based diagrams. `load_spec` also accepts a `diagram:`
wrapper (or a bare architecture spec); `render` and `validate` dispatch to the
diagram pipeline. Diagrams reject a tabular `data` override and share style and
export settings with plots. See [the diagram API](diagrams.md) for full semantics.

## Options

| Field | Meaning |
| --- | --- |
| `type`, `data`, `x`, `y`, `group`, `value` | Template and column roles; data path optional with Python table override |
| `aggregate` | `none` (default), `mean`, or `median`; duplicates require an explicit choice |
| `uncertainty` | `std`, `sem`, `ci95`, `{lower: column, upper: column}`, or null |
| `labels` | Explicit `x`, `y`, `title`, `legend`, `colorbar` strings; column names otherwise |
| `units` | `x`, `y`, `value` strings, appended in parentheses to axis/colorbar labels |
| `require_labels`, `require_units` | Default false; require explicit nonempty metadata for relevant roles |
| `order`, `group_order`, `row_order` | Complete category ordering; `row_order` applies to heatmap rows |
| `xscale`, `yscale` | `linear` or `log`; only numeric axes can be log; zero-based bars reject log |
| `xlim`, `ylim` | Increasing finite pairs; clipping emits a diagnostic |
| `legend`, `legend_loc`, `legend_columns` | Boolean, Matplotlib location name (default `best`), positive column count |
| `annotations` | List of `{text, x, y, coords: data}`; coords also supports `axes fraction` |
| `annotate` | Label bar heights or heatmap cell values |
| `cmap`, `color_limits` | Heatmap normalization; default viridis, optional increasing limits; saturation warns |
| `style` | Preset name or style mapping below |
| `export` | Mapping of formats, directory, stem and DPI |

Use `legend_loc: outside upper center` with `legend_columns: 3` to reserve space
above the axes through constrained layout. Other Matplotlib outside upper/lower
and left/right corner placements are supported. Native artist edits are possible,
then rerun `scifig.validation.visual.check_visual(result.figure)`.

Sample uncertainty explicitly selects a mean, requires at least two observations
per cell, and uses ddof=1. `ci95` is a normal approximation, not a Student-t or
bootstrap interval. Independence and experimental design cannot be inferred from
rows. Precomputed bounds require one row per cell and lower ≤ y ≤ upper. No
aggregation of supplied intervals is supported. Distribution and heatmap templates
reject aggregation and uncertainty. Heatmap missing cells fail, never become zero.

## Styling and export

A style mapping accepts `preset` (`publication`, `neurips`, `journal`), `width`
(`single_column`, `double_column`, or numeric inches), numeric `height`,
`font_family`, `font_size` in points, `palette` (`accessible`, `grayscale`),
`colors` (explicit category map), and `rc` (Matplotlib rc overrides).
A nonempty color map must cover every plotted category. Stable automatic color
hashes preserve each category's color across subsets, but collisions warn; use
explicit maps for papers. Curves also use markers and dashes, grouped bars hatches.
TeX execution and changing the global backend through a style are unsupported;
Matplotlib mathtext is available without a TeX installation.

`FigureResult` exposes `.figure`, `.ax`, `.axes`, `.spec`, `.style`, and `.diagnostics`.
`savefig(path, dpi=None, **kwargs)` returns a Path; `export(directory=None,
stem=None, formats=None, dpi=None)` returns a list of Paths, using specification
export defaults when options are absent. Save through the wrapper to apply delayed
PDF/SVG backend settings. Native `result.figure.savefig` follows Matplotlib's
current global settings instead.

Exports support PDF, SVG, PNG. Defaults are all three, directory `figures`, stem
`figure`, 300 DPI. PDF uses embedded TrueType; SVG uses paths for font portability.
For editable SVG use `style: {rc: {svg.fonttype: none}}`, which depends on viewer
fonts. Vector artists are not rasterized; PNG DPI does not change physical inches.
Tight cropping is opt-in via savefig kwargs because it changes canvas dimensions.
Fixed SVG IDs and removed PDF/SVG timestamps improve reproducibility within one
environment. Record dependencies (`uv.lock` or your environment lock) and fonts.

Create the JSON schema programmatically with `FigureSpec.model_json_schema()`.
The registry's `register_template(name, callable, data_family="learning_curve")`
reuses one of the five existing validation contracts; see [contributing](contributing.md).
