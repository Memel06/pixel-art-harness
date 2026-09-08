"""Command line interface for the Aseprite pixel-art harness."""

from __future__ import annotations

import argparse
import json
import sys
import subprocess
from pathlib import Path
from typing import Sequence

from .errors import PixelartError
from .renderer import doctor, inspect_file, render_scene, review_file, run_lua
from .scene import load_scene


def _json(value: object) -> None:
    print(json.dumps(value, indent=2))


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="pixelart", description="Portable editable Aseprite pixel-art harness")
    command.add_argument("--aseprite", help="Aseprite executable; otherwise ASEPRITE_BIN, then PATH")
    subcommands = command.add_subparsers(dest="command", required=True)
    subcommands.add_parser("doctor", help="report Pillow and Aseprite availability")
    render = subcommands.add_parser("render", help="validate a JSON scene and produce a new artifact directory")
    render.add_argument("scene", type=Path)
    render.add_argument("--out", required=True, type=Path, help="new output directory (must not already exist)")
    render.add_argument(
        "--raster-only",
        action="store_true",
        help="diagnostic only: omit source.aseprite and mark the output non-production",
    )
    inspect = subcommands.add_parser("inspect", help="inspect a raster image or export an existing .aseprite for QA")
    inspect.add_argument("input", type=Path)
    review = subcommands.add_parser("review", help="create nearest-neighbor visual review artifacts for a raster or .aseprite")
    review.add_argument("input", type=Path)
    review.add_argument("--out", required=True, type=Path, help="new output directory (must not already exist)")
    lua = subcommands.add_parser("run-lua", help="run an arbitrary Lua edit on a copied .aseprite source")
    lua.add_argument("source", type=Path)
    lua.add_argument("script", type=Path)
    lua.add_argument("--out", required=True, type=Path, help="new output directory (must not already exist)")
    lua.add_argument("--param", action="append", default=[], help="pass key=value to app.params (repeatable)")
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            report = doctor(args.aseprite)
            _json(report)
            return 0 if report["production_ready"] else 2
        elif args.command == "render":
            _json(
                render_scene(
                    load_scene(args.scene),
                    args.scene,
                    args.out,
                    aseprite=args.aseprite,
                    raster_only=args.raster_only,
                )
            )
        elif args.command == "inspect":
            _json(inspect_file(args.input, aseprite=args.aseprite))
        elif args.command == "review":
            _json(review_file(args.input, args.out, aseprite=args.aseprite))
        elif args.command == "run-lua":
            _json(run_lua(args.source, args.script, args.out, aseprite=args.aseprite, params=args.param))
        return 0
    except PixelartError as exc:
        print(f"pixelart: {exc}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired as exc:
        print(f"pixelart: Aseprite timed out after {exc.timeout} seconds", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"pixelart: filesystem or process error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
