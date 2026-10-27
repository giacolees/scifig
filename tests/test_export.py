import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from scifig.rendering.export import export_figure, save_figure
from scifig.validation.visual import check_visual


def make_figure():
    fig = Figure(figsize=(3, 2), layout="constrained")
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.plot([0, 1], [1, 2])
    ax.set_xlabel("x")
    return fig


def test_export_formats_and_stable_svg(tmp_path):
    fig = make_figure()
    files = export_figure(fig, tmp_path)
    assert files[0].read_bytes().startswith(b"%PDF")
    assert b"<svg" in files[1].read_bytes()
    assert files[2].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    first = files[1].read_bytes()
    save_figure(fig, files[1])
    assert first == files[1].read_bytes()
    with pytest.raises(ValueError, match="Unsupported"):
        save_figure(fig, tmp_path / "figure.jpg")


def test_visual_detects_small_and_outside_text():
    fig = make_figure()
    fig.text(1.2, 0.5, "outside", fontsize=4)
    diagnostics = check_visual(fig)
    assert any("smaller" in item for item in diagnostics)
    assert any("outside" in item for item in diagnostics)


def test_repeated_png_bytes_are_stable(tmp_path):
    fig = make_figure()
    path = save_figure(fig, tmp_path / "a.png")
    first = path.read_bytes()
    save_figure(fig, path)
    assert path.read_bytes() == first


@pytest.mark.parametrize(
    ("stem", "formats", "dpi"),
    [
        ("../escape", ("png",), 300),
        ("bad\\name", ("png",), 300),
        ("", ("png",), 300),
        ("figure", (), 300),
        ("figure", ("png", "jpg"), 300),
        ("figure", ("png", "png"), 300),
        ("figure", ("png",), 1.5),
    ],
)
def test_export_request_is_validated_before_writing(tmp_path, stem, formats, dpi):
    with pytest.raises(ValueError):
        export_figure(make_figure(), tmp_path / "out", stem=stem, formats=formats, dpi=dpi)
    assert not (tmp_path / "out").exists()


def test_custom_export_rc_controls_svg_and_does_not_leak(tmp_path):
    import matplotlib as mpl

    fig = make_figure()
    before = mpl.rcParams["svg.fonttype"]
    svg = save_figure(fig, tmp_path / "editable.svg", {"svg.fonttype": "none"})
    assert b"<text" in svg.read_bytes()
    assert mpl.rcParams["svg.fonttype"] == before


def test_export_failure_restores_settings_and_layout(tmp_path, monkeypatch):
    import matplotlib as mpl

    fig = make_figure()
    engine = fig.get_layout_engine()
    before = mpl.rcParams["svg.fonttype"]

    def fail(*args, **kwargs):
        raise RuntimeError("save failed")

    monkeypatch.setattr(fig, "savefig", fail)
    with pytest.raises(RuntimeError, match="save failed"):
        save_figure(fig, tmp_path / "failed.svg", {"svg.fonttype": "none"})
    assert mpl.rcParams["svg.fonttype"] == before
    assert fig.get_layout_engine() is engine


def test_invalid_rc_does_not_leak_or_write(tmp_path):
    import matplotlib as mpl

    before = mpl.rcParams["font.size"]
    with pytest.raises(ValueError):
        save_figure(make_figure(), tmp_path / "out" / "f.svg", {"font.size": 20, "bad.key": 1})
    assert mpl.rcParams["font.size"] == before
    assert not (tmp_path / "out").exists()


def test_vector_output_and_pdf_embedded_font(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    fig = make_figure()
    pdf, svg = export_figure(fig, tmp_path, formats=("pdf", "svg"))
    assert b"<image" not in svg.read_bytes()
    page = pypdf.PdfReader(pdf).pages[0]
    fonts = page["/Resources"]["/Font"].get_object()
    assert fonts
    # TrueType CID fonts have an embedded font stream in their descriptor.
    font = next(iter(fonts.values())).get_object()
    descendant = font["/DescendantFonts"][0].get_object()
    descriptor = descendant["/FontDescriptor"].get_object()
    assert "/FontFile2" in descriptor
    contents = page.get_contents().get_data()
    assert b" m\n" in contents  # vector path move operator
