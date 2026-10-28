"""Orchestrate the specification, canonical, layout and rendering boundaries."""

import warnings
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING

from scifig.diagrams._appearance import DiagramAppearance, diagram_appearance
from scifig.diagrams.ir import CanonicalDiagram, diagram_to_ir
from scifig.diagrams.layout import DiagramGeometry, get_layout_engine
from scifig.diagrams.specs import DiagramSpec, validate_diagram
from scifig.styles import ResolvedStyle, resolve_style

if TYPE_CHECKING:
    from scifig.diagrams.rendering import DiagramResult


@dataclass
class ResolvedPresentation:
    """Fully resolved drawing settings, independent of engine selection."""

    style: ResolvedStyle
    appearance: DiagramAppearance
    node_colors: dict[str, str]


@dataclass
class PreparedDiagram:
    """An isolated, validated source with canonical content and presentation."""

    spec: DiagramSpec
    diagram: CanonicalDiagram
    presentation: ResolvedPresentation
    diagnostics: list[str]


def prepare_diagram(spec: DiagramSpec) -> PreparedDiagram:
    """Revalidate mutable inputs and resolve presentation without invoking layout."""
    checked = DiagramSpec.model_validate(spec.model_dump())
    diagram = diagram_to_ir(checked)
    style = resolve_style(checked.style)
    appearance = diagram_appearance(style.preset)
    colors = (
        style.color_map(list(diagram.nodes))
        if style.colors
        else {
            key: appearance.grayscale_node
            if style.palette == "grayscale"
            else appearance.role_colors[node.role]
            for key, node in diagram.nodes.items()
        }
    )
    return PreparedDiagram(
        checked, diagram, ResolvedPresentation(style, appearance, colors), validate_diagram(checked)
    )


def layout_canonical(diagram: CanonicalDiagram) -> DiagramGeometry:
    """Revalidate canonical input, select the engine, and validate its output."""
    from scifig.diagrams.validation import validate_geometry

    checked = CanonicalDiagram.model_validate(diagram.model_dump())
    geometry = get_layout_engine(checked.layout.engine).layout(checked)
    validate_geometry(checked, geometry)
    return geometry


def layout_diagram(spec: DiagramSpec) -> DiagramGeometry:
    """Convert and lay out a specification without resolving drawing settings."""
    return layout_canonical(diagram_to_ir(spec))


def render_diagram(
    spec: DiagramSpec, *, geometry: DiagramGeometry | None = None
) -> "DiagramResult":
    """Execute the pipeline, validating engine output or copied supplied geometry."""
    from scifig.diagrams.rendering import render_geometry
    from scifig.diagrams.validation import check_diagram_visual, validate_geometry
    from scifig.rendering.matplotlib import FigureWarning

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        prepared = prepare_diagram(spec)
        resolved_geometry = (
            layout_canonical(prepared.diagram) if geometry is None else deepcopy(geometry)
        )
        validate_geometry(prepared.diagram, resolved_geometry)
        result = render_geometry(
            prepared.spec, prepared.diagram, resolved_geometry, prepared.presentation
        )
        diagnostics = [*prepared.diagnostics, *check_diagram_visual(result)]
    diagnostics.extend(str(record.message) for record in records)
    result.diagnostics = list(dict.fromkeys(diagnostics))
    for message in result.diagnostics:
        warnings.warn(message, FigureWarning, stacklevel=2)
    return result
