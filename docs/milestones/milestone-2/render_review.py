"""Reproduce Milestone 2 previews; run from the repository root."""

import json
import sys
import warnings
from pathlib import Path

import yaml

from scifig import DiagramSpec, list_diagram_templates, load_diagram_template, load_spec, render

ROOT = Path(__file__).resolve().parents[3]
REVIEW = Path(__file__).resolve().parent


def fixtures():
    for name in list_diagram_templates():
        yield name, load_diagram_template(name)
    for source in sorted((ROOT / "examples" / "diagrams").glob("*.yaml")):
        yield source.stem, load_spec(source)
    yield (
        "manual_ports_loop",
        DiagramSpec.model_validate(
            {
                "layout": "manual",
                "nodes": {
                    "input": {"label": "Input", "role": "input", "position": [0, 0]},
                    "state": {"label": "State", "position": [2.5, 0]},
                    "output": {"label": "Output", "role": "output", "position": [5, 0]},
                },
                "edges": [
                    {"source": "input", "target": "state", "source_port": "e", "target_port": "w"},
                    {"source": "state", "target": "output", "source_port": "e", "target_port": "w"},
                    {"source": "state", "target": "state", "kind": "feedback"},
                ],
                "groups": {"core": {"label": "Core", "nodes": ["state"]}},
                "style": {"width": "double_column", "height": 3.0},
            }
        ),
    )


def main():
    stage = sys.argv[1]
    directory = REVIEW / stage
    directory.mkdir(parents=True, exist_ok=True)
    diagnostics = {}
    for name, spec in fixtures():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = render(spec)
        result.export(directory, stem=name, formats=["pdf", "svg", "png"], dpi=100)
        result.save_layout(directory / f"{name}.layout.json")
        saved = spec.model_dump(mode="json")
        saved["export"]["directory"] = "."
        (directory / f"{name}.yaml").write_text(yaml.safe_dump({"diagram": saved}, sort_keys=False))
        diagnostics[name] = result.diagnostics
    (directory / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
