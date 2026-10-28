"""Template export guarantees and publication-size visual regression."""

import json
import shutil
from dataclasses import asdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.image as mpimg
import pytest
import yaml
from matplotlib.testing.compare import compare_images

from scifig import list_diagram_templates, load_diagram_template, load_spec, render, validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["residual_block", "research_workflow"])
def test_template_exports_parity_and_provenance(name, tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    spec = load_diagram_template(name)
    original = spec.model_dump(mode="json")
    source = tmp_path / f"{name}.yaml"
    source.write_text(yaml.safe_dump({"diagram": original}, sort_keys=False))
    parsed = load_spec(source)
    assert validate(spec) == validate(parsed) == []
    mpl.get_backend()  # Resolve the lazy backend before taking a global snapshot.
    before = dict(mpl.rcParams)
    first, second = render(spec), render(parsed)
    assert first.diagnostics == second.diagnostics == []
    assert first.layout == second.layout
    assert first.layout.engine == "manual"
    assert first.layout.engine_version is None
    assert spec.model_dump(mode="json") == original
    dimensions = tuple(first.figure.get_size_inches())
    assert dimensions[0] == 7.0
    for extension in ("pdf", "svg", "png"):
        path = first.savefig(tmp_path / f"first.{extension}")
        expected = path.read_bytes()
        assert second.savefig(tmp_path / f"second.{extension}").read_bytes() == expected
        assert first.savefig(path).read_bytes() == expected
    assert dict(mpl.rcParams) == before

    svg = (tmp_path / "first.svg").read_text()
    assert "<image" not in svg
    for node_id in spec.nodes:
        assert f'id="node:{node_id}"' in svg
    for index in range(len(spec.edges)):
        assert f'id="edge:{index}"' in svg
    image = mpimg.imread(tmp_path / "first.png")
    assert image.shape[:2] == tuple(int(value * spec.export.dpi) for value in dimensions[::-1])

    from pypdf import PdfReader

    page = PdfReader(tmp_path / "first.pdf").pages[0]
    assert (float(page.mediabox.width), float(page.mediabox.height)) == pytest.approx(
        [value * 72 for value in dimensions]
    )
    fonts = page["/Resources"]["/Font"].get_object()
    assert fonts
    for font in fonts.values():
        descendant = font.get_object()["/DescendantFonts"][0].get_object()
        descriptor = descendant["/FontDescriptor"].get_object()
        assert "/FontFile2" in descriptor

    layout_path = first.save_layout(tmp_path / "layout.json")
    payload = json.loads(layout_path.read_text())
    assert payload["schema_version"] == 1
    assert payload["matplotlib_version"] == mpl.__version__
    assert payload["scifig_version"]
    assert payload["figure_size_inches"] == list(dimensions)
    for key, value in asdict(first.layout).items():
        assert payload[key] == json.loads(json.dumps(value))
    assert layout_path.read_bytes() == first.save_layout(layout_path).read_bytes()
    assert payload["spec"]["nodes"] == original["nodes"]


@pytest.mark.parametrize("name", ["residual_block", "research_workflow"])
def test_template_publication_preview(name, tmp_path):
    result = render(load_diagram_template(name))
    assert result.diagnostics == []
    assert set(result.node_artists) == set(result.spec.nodes)
    assert len(result.edge_artists) == len(result.spec.edges)
    for index, edge in enumerate(result.spec.edges):
        assert (
            result.edge_artists[index].get_linestyle()
            == {
                "data": "-",
                "feedback": "-.",
            }[edge.kind]
        )
    labels = {text.get_gid(): text for text in result.ax.texts}
    for node_id, node in result.spec.nodes.items():
        assert labels[f"node-label:{node_id}"].get_text().split() == node.label.split()
        if node.shape is not None:
            assert labels[f"node-detail:{node_id}"].get_text() == " × ".join(map(str, node.shape))
    png = result.savefig(tmp_path / f"{name}.png", dpi=100)
    difference = compare_images(
        str(Path(__file__).parent / "baseline" / f"diagrams_{name}.png"), str(png), tol=15
    )
    assert difference is None, difference


def test_committed_template_sources_reproduce_geometry():
    for name in list_diagram_templates():
        spec = load_spec(ROOT / "docs" / "gallery" / f"diagrams_{name}.yaml")
        result = render(spec)
        provenance = json.loads(
            (ROOT / "docs" / "gallery" / f"diagrams_{name}.layout.json").read_text()
        )
        assert provenance["nodes"] == json.loads(json.dumps(asdict(result.layout)["nodes"]))
        assert provenance["edges"] == json.loads(json.dumps(asdict(result.layout)["edges"]))
        assert result.diagnostics == []
