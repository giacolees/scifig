"""Render the illustrative architecture gallery from any working directory."""

from pathlib import Path

from scifig import load_spec, render

SPECS = Path(__file__).resolve().parent / "diagrams"


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


if __name__ == "__main__":
    main()
