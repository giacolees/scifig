"""Packaged, editable diagram starting points."""

from importlib.resources import files

from scifig.core.specs import _parse_spec
from scifig.diagrams.specs import DiagramSpec

_TEMPLATES = {
    "residual_block": "residual_block.yaml",
    "research_workflow": "research_workflow.yaml",
}


def list_diagram_templates() -> list[str]:
    """Return the names of the packaged diagram templates."""
    return sorted(_TEMPLATES)


def load_diagram_template(name: str) -> DiagramSpec:
    """Load a fresh, strictly validated diagram template by name."""
    try:
        filename = _TEMPLATES[name]
    except KeyError:
        raise ValueError(
            f"unknown diagram template {name!r}; available: {', '.join(list_diagram_templates())}"
        ) from None
    resource = files("scifig.diagrams").joinpath("template_sources", filename)
    with resource.open(encoding="utf-8") as stream:
        spec = _parse_spec(stream)
    if not isinstance(spec, DiagramSpec):
        raise ValueError(f"diagram template {name!r} must contain a diagram")
    return spec
