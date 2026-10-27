# Architecture diagrams

Architecture diagrams describe components and directed connections, rather than plotting observations from a data table. Define the graph explicitly from the researcher's description, code, or documentation; the renderer does not infer an architecture from code. The examples below are illustrative, not claims about a particular model or experiment.

```yaml
diagram:
  type: architecture
  layout: graphviz
  direction: left_to_right
  feedforward: true
  nodes:
    input: {label: Input, role: input}
    encoder: {label: Encoder, role: module}
    output: {label: Output, role: output}
  edges:
    - {source: input, target: encoder}
    - {source: encoder, target: output}
  export: {directory: outputs, stem: architecture, formats: [pdf, svg, png], dpi: 300}
```

Run `scifig validate diagram.yaml` and `scifig render diagram.yaml`. Python users can call `load_spec` and `render`, or build a diagram directly:

```python
from scifig import architecture

result = architecture(
    nodes={
        "x": {"label": "Input", "role": "input"},
        "encoder": {"label": "Encoder", "role": "module"},
    },
    edges=[{"source": "x", "target": "encoder"}],
)
result.export("outputs", stem="architecture", formats=["pdf", "svg", "png"])
print(result.diagnostics)
```

The result exposes the Matplotlib `figure`, `ax`, `node_artists`, `edge_artists`
and `group_artists` for further editing, plus `savefig`, `export`, `save_layout`
and advisory `diagnostics`. PDF and SVG preserve vector artwork; PNG is a raster
preview. Exports use the existing figure style and export settings. Re-render after
changing a semantic spec. The layout JSON records the generated geometry, input
spec, scifig/Matplotlib versions and Graphviz version, when used. It documents the
layout at creation and is not an alternate render-input format.

Install Graphviz separately using its [official installation options](https://graphviz.org/download/).
Its [directed layout engine](https://graphviz.org/docs/layouts/dot/) and
[JSON geometry](https://graphviz.org/docs/outputs/json/) supply node positions and
edge paths; Matplotlib draws the resulting vectors. Nothing is rasterized or
converted into a screenshot. No Graphviz code or binary is bundled in scifig.

## Graph and layout

- Node IDs are unique keys in `nodes`. Each node has a `label` and optional `role` (`input`, `output`, `module`, `data`, `store`, `loss`, or `operation`). `size` is `[width, height]` in nominal inches, defaulting to `[1.4, 0.65]`. `frozen: true` marks a frozen component.
- Every edge names existing `source` and `target` node IDs. Its optional `label` and `kind` (`data`, `gradient`, `control`, or `feedback`) express the connection. Optional `source_port` and `target_port` are `n`, `s`, `e`, or `w` for the corresponding side.
- `groups` maps IDs to a `label`, list of `nodes`, and optional `role` (`group`, `training`, or `inference`). A node can belong to at most one group. Training and inference boundaries distinguish stages; gradient and control edge styles distinguish their connections.
- `direction` is `left_to_right` (default) or `top_to_bottom`. `layout: graphviz` is the default and requires the external Graphviz `dot` executable on `PATH`; it is not a Python extra. `layout: manual` requires a `position: [x, y]` in nominal inches for every node and does not require Graphviz.
- Cycles are allowed by default. Set `feedforward: true` to reject cycles involving data or feedback edges. Gradient and control edges can still describe training behavior.

A node may declare `shape` as a list of positive integers or symbolic dimensions
and `operation` as `identity`, `add`, or `concat`. Shapes describe node outputs;
incoming data edges provide the declared input shapes. Identity requires one
data input; add requires at least two and means equal-shape addition without
broadcasting. Contradictory concrete dimensions or ranks fail validation.
Unknown dimensions are not inferred, differing symbols produce an advisory, and
concat cannot be verified without an axis. These checks do not execute a model
or prove its correctness; verify the graph against its source.

Typography stays in final-size points while layout coordinates fit the physical
canvas without distorting aspect ratio. Node text wraps at word boundaries;
mathtext and long unbroken tokens are preserved. Diagnostics report labels that
do not fit, overlapping nodes, group collisions and routes through unrelated
nodes. Increase canvas dimensions, node sizes or spacing to fix actual defects.
Edge kinds use distinct line styles with a legend; frozen nodes are labeled and
outlined with dashes. Defaults use restrained role colors. For overrides, an
explicit `style.colors` map must cover all **node IDs**; `palette: grayscale`
keeps diagram colors neutral. `direction` affects automatic layout; manual
positions use x rightward and y upward. Edges are straight in manual layouts,
with cubic self-loops. Complex manual bend points, nested groups, automatic tensor
inference and general neural-network tracing are outside this first version.

## Illustrative gallery

Generate all examples with `python examples/make_diagram_gallery.py`. Graphviz is needed for the automatic examples. Each source specification is in `examples/diagrams/` and each export and layout JSON is in `docs/gallery/`.

| Example | Layout | Preview | Vector |
| --- | --- | --- | --- |
| ML pipeline | Graphviz | [PNG](gallery/diagrams_ml_pipeline.png) | [PDF](gallery/diagrams_ml_pipeline.pdf), [SVG](gallery/diagrams_ml_pipeline.svg) |
| Encoder–decoder and skip | Manual | [PNG](gallery/diagrams_encoder_decoder.png) | [PDF](gallery/diagrams_encoder_decoder.pdf), [SVG](gallery/diagrams_encoder_decoder.svg) |
| Training and inference | Graphviz | [PNG](gallery/diagrams_training_inference.png) | [PDF](gallery/diagrams_training_inference.pdf), [SVG](gallery/diagrams_training_inference.svg) |
