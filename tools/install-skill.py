#!/usr/bin/env python3
"""Install a self-contained agent skill; no symlinks or administrator rights needed."""
import argparse
import os
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "skills" / "aseprite-pixelart"
    target = args.skills_dir.expanduser() / source.name
    if target.exists() or target.is_symlink():
        parser.error(f"Refusing to replace existing skill: {target}. Remove it explicitly to reinstall.")
    try:
        shutil.copytree(source, target)
        for name in ("scene.schema.json", "moonlit-courier.json"):
            shutil.copy2(root / "examples" / name, target / "references" / name)
    except OSError as exc:
        parser.exit(2, f"Installation failed: {exc}\n")
    print(f"Installed: {target}\nInstall the Python package separately; the skill uses pixelart on PATH.")


if __name__ == "__main__":
    main()
