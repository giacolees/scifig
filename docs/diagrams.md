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

## Packaged starting points

Discover and load the editable templates through the Python API:

```python
from scifig import list_diagram_templates, load_diagram_template, render

print(list_diagram_templates())  # ['research_workflow', 'residual_block']
spec = load_diagram_template("research_workflow")
spec.nodes["question"].label = "Study question"
result = render(spec)  # revalidates the edited spec
result.export()  # defaults to figures/ in PDF, SVG and PNG
result.save_layout("figures/workflow.layout.json")
print(result.diagnostics)
```

Each load returns a fresh `DiagramSpec`. The packaged source files are
[`research_workflow.yaml`](../src/scifig/diagrams/template_sources/research_workflow.yaml)
and [`residual_block.yaml`](../src/scifig/diagrams/template_sources/residual_block.yaml).
They use manual positions and need no Graphviz. The workflow is a conceptual
illustration with feedback, not evidence of a particular research process. The
residual block declares symbolic output shapes and identity/add operations so the
existing shape checks can check compatible declarations; this does not prove an
actual implementation has those shapes.

Customize labels, roles, positions, sizes, shapes and operations on nodes; edges,
ports, groups, title, style and export settings are also ordinary `DiagramSpec`
fields. Match all changes to the supplied evidence. Rendering revalidates mutable
specs; invalid endpoints, groups, cycles when feedforward is requested, and
contradictory supported shapes fail. See the graph rules below for limitations.
The templates use the `editorial` preset: neutral ink, muted accents, subtle fills
and white background with the existing physical typography settings. It is also
available to other figures as a style preset.

Preserve the customized YAML or Python source, execution command, and dependency
and font versions with the exports. A layout JSON records generated geometry and
versions; it is not a render input and cannot replace the source. Exact appearance
can vary with dependencies and fonts even with the same specification.

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

Generate all examples with `python examples/make_diagram_gallery.py`. Graphviz is needed for the automatic examples. Original examples are in `examples/diagrams/`; packaged templates are linked above. Exports and layout JSON are in `docs/gallery/`; the packaged starters also include resolved YAML with every default.

| Example | Layout | Preview | Vector |
| --- | --- | --- | --- |
| Research workflow | Manual | [PNG](gallery/diagrams_research_workflow.png) | [PDF](gallery/diagrams_research_workflow.pdf), [SVG](gallery/diagrams_research_workflow.svg) |
| Residual block | Manual | [PNG](gallery/diagrams_residual_block.png) | [PDF](gallery/diagrams_residual_block.pdf), [SVG](gallery/diagrams_residual_block.svg) |
| ML pipeline | Graphviz | [PNG](gallery/diagrams_ml_pipeline.png) | [PDF](gallery/diagrams_ml_pipeline.pdf), [SVG](gallery/diagrams_ml_pipeline.svg) |
| Encoder–decoder and skip | Manual | [PNG](gallery/diagrams_encoder_decoder.png) | [PDF](gallery/diagrams_encoder_decoder.pdf), [SVG](gallery/diagrams_encoder_decoder.svg) |
| Training and inference | Graphviz | [PNG](gallery/diagrams_training_inference.png) | [PDF](gallery/diagrams_training_inference.pdf), [SVG](gallery/diagrams_training_inference.svg) |

Resolved starter sources and geometry: research workflow [YAML](gallery/diagrams_research_workflow.yaml)
and [layout JSON](gallery/diagrams_research_workflow.layout.json); residual block
[YAML](gallery/diagrams_residual_block.yaml) and [layout JSON](gallery/diagrams_residual_block.layout.json).

## Future interoperability

The current renderer uses native Matplotlib primitives and does not import external
art or provide adapters. Potential future directions have different semantics:
[Penrose](https://penrose.cs.cmu.edu/docs/tutorial/basics) separates domain,
substance and style for constraint-based mathematical diagrams;
[LikeC4](https://likec4.dev/dsl/views/) derives views from a software architecture
model; and [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML)
expresses C4 architecture diagrams as PlantUML source. A future integration would
need an explicit mapping of supported concepts, views, constraints and layout;
translation would not automatically preserve all semantics. Generating C4-PlantUML
source and importing LikeC4 graphs/views or Penrose diagrams remain future work.
Any reuse of external assets would require a licensing and attribution review.
