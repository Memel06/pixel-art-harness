import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pixelart.cli import main
from pixelart.errors import SceneError
from pixelart.renderer import resolve_aseprite, render_scene
from pixelart.scene import validate_scene
from test_renderer import minimal_scene

ROOT = Path(__file__).resolve().parents[1]


class PortabilityTests(unittest.TestCase):
    def test_invalid_explicit_path_does_not_fall_back(self):
        with patch.dict(os.environ, {"ASEPRITE_BIN": sys.executable}):
            self.assertIsNone(resolve_aseprite("/missing/pixel-art-harness/aseprite").executable)

    def test_invalid_environment_does_not_fall_back(self):
        with patch.dict(os.environ, {"ASEPRITE_BIN": "/missing/pixel-art-harness/aseprite"}):
            self.assertIsNone(resolve_aseprite().executable)

    def test_explicit_executable_overrides_environment(self):
        with patch.dict(os.environ, {"ASEPRITE_BIN": "/missing/aseprite"}):
            self.assertEqual(resolve_aseprite(sys.executable).executable, str(Path(sys.executable).resolve()))

    def test_timeout_is_reported_as_cli_error(self):
        with patch("pixelart.cli.inspect_file", side_effect=subprocess.TimeoutExpired("aseprite", 120)):
            self.assertEqual(main(["inspect", "source.aseprite"]), 2)

    def test_windows_paths_are_rejected_on_every_platform(self):
        for path in ["C:/outside.png", "C:outside.png", "..\\outside.png", "folder\\image.png"]:
            scene = minimal_scene()
            scene["frames"][0]["layers"][0]["commands"] = [{"op": "image", "path": path, "x": 0, "y": 0}]
            with self.subTest(path=path), self.assertRaises(SceneError):
                validate_scene(scene)

    def test_skill_copy_is_self_contained_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="skill space ") as temporary:
            command = [sys.executable, str(ROOT / "tools/install-skill.py"), "--skills-dir", temporary]
            subprocess.run(command, check=True, capture_output=True)
            installed = Path(temporary) / "aseprite-pixelart"
            self.assertFalse(installed.is_symlink())
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "references/art-direction.md").is_file())
            validate_scene(json.loads((installed / "references/moonlit-courier.json").read_text()))
            self.assertTrue((installed / "references/scene.schema.json").is_file())
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 2)

    def test_failed_render_cleans_staging_and_existing_output_survives(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scene = minimal_scene()
            scene["frames"][0]["layers"][0]["commands"] = [{"op": "image", "path": "missing.png", "x": 0, "y": 0}]
            with self.assertRaises(SceneError):
                render_scene(scene, root / "scene.json", root / "result", raster_only=True)
            self.assertEqual(list(root.iterdir()), [])
            output = root / "result"
            output.mkdir()
            (output / "keep.txt").write_text("keep")
            from pixelart.errors import PixelartError
            with self.assertRaises(PixelartError):
                render_scene(minimal_scene(), root / "scene.json", output, raster_only=True)
            self.assertEqual((output / "keep.txt").read_text(), "keep")

    def test_example_matches_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("install .[dev] for JSON Schema checks")
        schema = json.loads((ROOT / "examples/scene.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        for name in ("moonlit-courier.json", "skywhale.json"):
            with self.subTest(example=name):
                jsonschema.validate(json.loads((ROOT / "examples" / name).read_text()), schema)
