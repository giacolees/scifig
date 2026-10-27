"""End-to-end CLI coverage for diagrams and resolved specifications."""

import json
import os
import subprocess
import sys

import yaml


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "scifig", *map(str, args)],
        cwd=cwd,
        env=dict(os.environ, MPLBACKEND="Agg"),
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_lists_and_renders_diagram(tmp_path):
    listing = run_cli("templates", "list", cwd=tmp_path)
    assert listing.returncode == 0, listing.stderr
    assert "architecture" in listing.stdout.splitlines()
    spec = tmp_path / "diagram.yaml"
    spec.write_text("""diagram:
  layout: manual
  title: Example
  nodes:
    a: {label: Input, role: input, position: [1, 1]}
    b: {label: Output, role: output, position: [3, 1]}
  edges:
    - {source: a, target: b, label: signal}
  export: {directory: output, stem: result}
""")
    for command in ("validate", "render"):
        result = run_cli(command, spec, cwd=tmp_path)
        assert result.returncode == 0, result.stderr
    out = tmp_path / "output"
    assert (out / "result.pdf").read_bytes().startswith(b"%PDF")
    assert b"<svg" in (out / "result.svg").read_bytes()[:1000]
    assert (out / "result.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    layout = json.loads((out / "result.layout.json").read_text())
    assert layout["engine"] == "manual"
    saved = yaml.safe_load((out / "result.yaml").read_text())
    assert set(saved) == {"diagram"}
    assert saved["diagram"]["nodes"]["a"]["label"] == "Input"
    assert saved["diagram"]["export"]["directory"] == "."
    check = run_cli("validate", out / "result.yaml", cwd=tmp_path)
    assert check.returncode == 0, check.stderr
