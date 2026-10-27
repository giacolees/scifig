"""Small command-line interface for reproducible scientific figures."""

import argparse
import os
import sys
from pathlib import Path

import yaml

from scifig import DiagramSpec, list_styles, list_templates, load_spec, render, validate


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, returning an exit code; validation errors never produce a traceback."""
    parser = argparse.ArgumentParser(prog="scifig", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("render", "validate"):
        sub = commands.add_parser(command)
        sub.add_argument("spec", type=Path, help="YAML specification (paths relative to this file)")
    for command in ("templates", "styles"):
        sub = commands.add_parser(command)
        sub.add_subparsers(dest="action", required=True).add_parser("list")
    args = parser.parse_args(argv)
    try:
        if args.command in {"templates", "styles"}:
            print("\n".join(list_templates() if args.command == "templates" else list_styles()))
            return 0
        spec = load_spec(args.spec)
        if args.command == "validate":
            messages = validate(spec)
            for message in messages:
                print(f"warning: {message}", file=sys.stderr)
            print(f"Valid: {args.spec}")
            return 0
        result = render(spec)
        paths = result.export()
        # Preserve a portable resolved spec alongside the figures. Input data
        # remain user-owned and must accompany this spec for reproduction.
        saved_spec = spec.export.directory / f"{spec.export.stem}.yaml"
        payload = spec.model_dump(mode="json")
        if not isinstance(spec, DiagramSpec) and spec.data is not None:
            payload["data"] = os.path.relpath(spec.data, saved_spec.parent)
        payload["export"]["directory"] = "."
        wrapper = "diagram" if isinstance(spec, DiagramSpec) else "figure"
        saved_spec.write_text(yaml.safe_dump({wrapper: payload}, sort_keys=False), encoding="utf-8")
        sidecars = [saved_spec]
        if isinstance(spec, DiagramSpec):
            sidecars.append(
                result.save_layout(spec.export.directory / f"{spec.export.stem}.layout.json")
            )
        for path in [*paths, *sidecars]:
            print(path)
        return 0
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        print(f"scifig: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
