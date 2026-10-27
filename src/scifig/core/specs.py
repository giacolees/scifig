"""Validated, serializable figure specifications."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _UniqueLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses ambiguous duplicate keys."""


def _construct_mapping(loader: _UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    """Construct a mapping while detecting repeated keys at every depth."""
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ValueError("YAML mapping keys must be hashable") from exc
        if duplicate:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class BoundsSpec(_Model):
    """Column names containing precomputed absolute interval endpoints."""

    lower: str
    upper: str


class AnnotationSpec(_Model):
    """A text annotation positioned in data or normalized axes coordinates."""

    text: str
    x: float
    y: float
    coords: Literal["data", "axes fraction"] = "data"


class StyleSpec(_Model):
    """Physical dimensions and visual tokens, independent of data semantics."""

    preset: str = "publication"
    width: Literal["single_column", "double_column"] | float = "single_column"
    height: float | None = Field(default=None, gt=0)
    font_family: str | None = None
    font_size: float | None = Field(default=None, gt=0)
    palette: Literal["accessible", "grayscale"] = "accessible"
    colors: dict[str, str] = Field(default_factory=dict)
    rc: dict[str, Any] = Field(default_factory=dict)

    @field_validator("width")
    @classmethod
    def positive_width(cls, value: str | float) -> str | float:
        """Reject nonpositive numeric widths."""
        if isinstance(value, float) and value <= 0:
            raise ValueError("width must be positive")
        return value


class ExportSpec(_Model):
    """Output filenames, vector/raster formats and preview resolution."""

    formats: list[Literal["pdf", "svg", "png"]] = Field(
        default_factory=lambda: ["pdf", "svg", "png"]
    )
    directory: Path = Path("figures")
    stem: str = "figure"
    dpi: int = Field(default=300, ge=72)

    @field_validator("directory", mode="before")
    @classmethod
    def path(cls, value: str | Path) -> Path:
        """Accept YAML paths as strings under strict validation."""
        return Path(value) if isinstance(value, str) else value

    @field_validator("stem")
    @classmethod
    def safe_stem(cls, value: str) -> str:
        """Prevent output names from traversing directories."""
        if not value or value in {".", ".."} or "/" in value or "\\" in value:
            raise ValueError("stem must be a nonempty basename")
        return value

    @field_validator("formats")
    @classmethod
    def nonempty_formats(cls, value: list[str]) -> list[str]:
        """Require at least one unique export format."""
        if not value or len(value) != len(set(value)):
            raise ValueError("formats must be nonempty and unique")
        return value


class FigureSpec(_Model):
    """Serializable semantic figure intent shared by every interface."""

    type: str
    data: str | Path | None = None
    x: str
    y: str
    group: str | None = None
    value: str | None = None
    uncertainty: Literal["std", "sem", "ci95"] | BoundsSpec | None = None
    aggregate: Literal["none", "mean", "median"] = "none"
    style: StyleSpec | str = "publication"
    labels: dict[str, str] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    require_labels: bool = False
    require_units: bool = False
    xscale: Literal["linear", "log"] = "linear"
    yscale: Literal["linear", "log"] = "linear"
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    order: list[str] | None = None
    row_order: list[str] | None = None
    group_order: list[str] | None = None
    legend: bool = True
    legend_loc: str = "best"
    legend_columns: int = Field(default=1, ge=1)
    annotations: list[AnnotationSpec] = Field(default_factory=list)
    annotate: bool = False
    cmap: str = "viridis"
    color_limits: tuple[float, float] | None = None
    export: ExportSpec = Field(default_factory=ExportSpec)

    @field_validator("xlim", "ylim", "color_limits", mode="before")
    @classmethod
    def tuple_from_yaml(cls, value: Any) -> Any:
        """Accept YAML sequences for fixed-size bounds."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def valid_options(self) -> "FigureSpec":
        """Check bounds and semantic label names."""
        for name in ("xlim", "ylim", "color_limits"):
            bounds = getattr(self, name)
            if bounds is not None and bounds[0] >= bounds[1]:
                raise ValueError(f"{name} must be strictly increasing")
        unknown = set(self.labels) - {"x", "y", "title", "legend", "colorbar"}
        if unknown:
            raise ValueError(f"unknown labels: {sorted(unknown)}")
        unknown_units = set(self.units) - {"x", "y", "value"}
        if unknown_units:
            raise ValueError(f"unknown units: {sorted(unknown_units)}")
        return self


def load_spec(path: str | Path) -> FigureSpec:
    """Load YAML and resolve its paths relative to the specification file."""
    path = Path(path).resolve()
    try:
        with path.open(encoding="utf-8") as stream:
            raw = yaml.load(stream, Loader=_UniqueLoader)
        if not isinstance(raw, dict):
            raise ValueError("specification must be a mapping")
        if "figure" in raw:
            if set(raw) != {"figure"}:
                raise ValueError("figure wrapper cannot have sibling keys")
            raw = raw["figure"]
            if not isinstance(raw, dict):
                raise ValueError("figure must be a mapping")
        spec = FigureSpec.model_validate(raw)
        if spec.data is not None:
            spec.data = (path.parent / spec.data).resolve()
        spec.export.directory = (path.parent / spec.export.directory).resolve()
        return spec
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot load specification {path}: {exc}") from exc
