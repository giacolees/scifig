"""Render the illustrative architecture gallery from any working directory."""

from pathlib import Path

import yaml

from scifig import list_diagram_templates, load_diagram_template, load_spec, render

SPECS = Path(__file__).resolve().parent / "diagrams"
GALLERY = Path(__file__).resolve().parents[1] / "docs" / "gallery"


def main() -> None:
    for path in sorted(SPECS.glob("*.yaml")):
        spec = load_spec(path)
        result = render(spec)
        result.export(
            spec.export.directory,
            stem=spec.export.stem,
            formats=spec.export.formats,
            dpi=spec.export.dpi,
        )
        result.save_layout(Path(spec.export.directory) / f"{spec.export.stem}.layout.json")
        print(f"{path.stem}: {result.diagnostics}")
    for name in list_diagram_templates():
        spec = load_diagram_template(name)
        spec.export.directory = GALLERY
        spec.export.stem = f"diagrams_{name}"
        result = render(spec)
        result.export()
        result.save_layout(GALLERY / f"{spec.export.stem}.layout.json")
        # Preserve every resolved default alongside the exports. Relative paths
        # keep this source portable and rerenderable with the existing CLI.
        resolved = spec.model_dump(mode="json")
        resolved["export"]["directory"] = "."
        (GALLERY / f"{spec.export.stem}.yaml").write_text(
            yaml.safe_dump({"diagram": resolved}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"{name}: {result.diagnostics}")


if __name__ == "__main__":
    main()
