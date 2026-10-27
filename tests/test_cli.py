import os
import subprocess
import sys

from scifig import load_spec


def run_cli(*args, cwd):
    env = dict(os.environ, MPLBACKEND="Agg")
    return subprocess.run(
        [sys.executable, "-m", "scifig", *map(str, args)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_validate_render_and_export(tmp_path):
    (tmp_path / "data.csv").write_text("epoch,score\n1,0.2\n2,0.4\n")
    spec = tmp_path / "plot.yaml"
    spec.write_text(
        "figure:\n  type: learning_curve\n  data: data.csv\n  x: epoch\n"
        "  y: score\n  export:\n    directory: output\n    stem: result\n"
    )
    check = run_cli("validate", spec, cwd=tmp_path)
    assert check.returncode == 0, check.stderr
    assert "Valid:" in check.stdout
    result = run_cli("render", spec, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    out = tmp_path / "output"
    assert (out / "result.pdf").read_bytes().startswith(b"%PDF")
    assert b"<svg" in (out / "result.svg").read_bytes()[:1000]
    assert (out / "result.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert (out / "result.yaml").is_file()
    preserved = load_spec(out / "result.yaml")
    assert preserved.data == tmp_path / "data.csv"
    assert preserved.export.directory == out
    for suffix in ("pdf", "svg", "png"):
        assert (out / f"result.{suffix}").stat().st_size > 1000


def test_cli_lists_and_actionable_invalid_spec(tmp_path):
    for kind, expected in [("templates", "learning_curve"), ("styles", "publication")]:
        result = run_cli(kind, "list", cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert expected in result.stdout
    (tmp_path / "data.csv").write_text("x,y\n1,2\n")
    spec = tmp_path / "bad.yaml"
    spec.write_text("type: learning_curve\ndata: data.csv\nx: missing\ny: y\n")
    for command in ("validate", "render"):
        result = run_cli(command, spec, cwd=tmp_path)
        assert result.returncode != 0
        assert "missing" in result.stderr
        assert "Traceback" not in result.stderr
