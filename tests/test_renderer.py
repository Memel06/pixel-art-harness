import json
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pixelart.errors import AsepriteNotFound, PixelartError
from pixelart.renderer import _extract_aseprite, _verify_native_roundtrip, build_qa, doctor, render_scene, run_lua


def minimal_scene():
    return {
        "version": 1,
        "canvas": {"width": 4, "height": 3},
        "palette": ["#00000000", "#ff0000"],
        "frames": [
            {"duration": 90, "layers": [{"name": "ink", "commands": [{"op": "rect", "x": 1, "y": 1, "width": 2, "height": 1, "color": 1}]}]},
            {"duration": 110, "layers": [{"name": "ink", "commands": []}]},
        ],
    }


class RenderTests(unittest.TestCase):
    def test_doctor_rejects_other_program_and_missing_lua(self):
        import subprocess
        resolution = type("Resolution", (), {"executable": "/fake/aseprite", "candidates": []})()
        for responses, ready in [
            ([subprocess.CompletedProcess([], 0, "Python 3.14", "")], False),
            ([subprocess.CompletedProcess([], 0, "Aseprite 1.3", ""), subprocess.CompletedProcess([], 0, "", "")], False),
            ([subprocess.CompletedProcess([], 0, "Aseprite 1.3", ""), subprocess.CompletedProcess([], 0, "PIXELART_LUA_READY\n", "")], True),
        ]:
            with self.subTest(ready=ready, responses=responses), patch("pixelart.renderer.resolve_aseprite", return_value=resolution), patch("pixelart.renderer.subprocess.run", side_effect=responses):
                self.assertEqual(doctor()["production_ready"], ready)

    def test_review_layer_names_cannot_overwrite_each_other(self):
        scene = minimal_scene()
        scene["frames"] = [scene["frames"][0]]
        scene["frames"][0]["layers"][0]["name"] = "A B"
        scene["frames"][0]["layers"].append({"name": "A-B", "commands": []})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            render_scene(scene, root / "scene.json", root / "out", raster_only=True)
            review = json.loads((root / "out/review.json").read_text())
            paths = review["artifacts"]["layer_silhouettes"]
            self.assertNotEqual(paths["A B"], paths["A-B"])
            self.assertNotEqual((root / "out" / paths["A B"]).read_bytes(), (root / "out" / paths["A-B"]).read_bytes())

    def test_raster_only_is_explicit_and_marked_non_production(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scene_file = root / "scene.json"
            scene_file.write_text(json.dumps(minimal_scene()), encoding="utf-8")
            output = root / "render"
            metadata = render_scene(minimal_scene(), scene_file, output, raster_only=True)
            self.assertIsNone(metadata["editable_source"])
            self.assertFalse(metadata["production_ready"])
            qa = json.loads((output / "qa.json").read_text())
            self.assertEqual(qa["technical"]["empty_frames"], [1])
            self.assertTrue((output / "review" / "layers" / "00-ink-silhouette.png").is_file())
            self.assertFalse((output / "source.aseprite").exists())

    def test_gif_preserves_opaque_colors_and_transparent_frame_clearing(self):
        from pixelart.renderer import _write_preview, _nearest_scale

        for transparent in (False, True):
            with self.subTest(transparent=transparent), tempfile.TemporaryDirectory() as temporary:
                background = (0, 0, 0, 0) if transparent else (20, 30, 40, 255)
                frames = []
                for x in (0, 2):
                    frame = Image.new("RGBA", (4, 3), background)
                    frame.putpixel((x, 1), (255, 180, 40, 255))
                    frames.append(frame)
                _write_preview(frames, [90, 110], Path(temporary))
                with Image.open(Path(temporary) / "preview.gif") as gif:
                    self.assertEqual(gif.n_frames, 2)
                    for index, expected in enumerate(frames):
                        gif.seek(index)
                        self.assertEqual(gif.info["duration"], [90, 110][index])
                        actual = gif.convert("RGBA")
                        expected = _nearest_scale(expected)[0]
                        self.assertEqual(actual.getchannel("A").tobytes(), expected.getchannel("A").tobytes())
                        for point in [(0, 0), (0, 8), (16, 8)]:
                            if expected.getpixel(point)[3]:
                                self.assertEqual(actual.getpixel(point), expected.getpixel(point))

    def test_render_requires_aseprite_without_raster_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scene_file = root / "scene.json"
            scene_file.write_text(json.dumps(minimal_scene()), encoding="utf-8")
            resolution = type("Resolution", (), {"executable": None, "candidates": []})()
            with patch("pixelart.renderer.resolve_aseprite", return_value=resolution):
                with self.assertRaises(AsepriteNotFound):
                    render_scene(minimal_scene(), scene_file, root / "render")

    def test_roundtrip_rejects_wrong_duration(self):
        image = Image.new("RGBA", (1, 1), (1, 2, 3, 255))
        with self.assertRaisesRegex(PixelartError, "durations"):
            _verify_native_roundtrip([image], [image.copy()], {"frames": [{"duration": 100}]}, [90])

    def test_qa_reports_actual_colors_not_just_declared_palette_size(self):
        image = Image.new("RGBA", (1, 1), (1, 2, 3, 255))
        qa = build_qa([image], {"palette": ["#000000"], "frames": [{}]})["technical"]
        self.assertEqual(qa["colors_used_count"], 1)
        self.assertEqual(qa["out_of_declared_palette_colors"], ["#010203"])
        self.assertFalse(qa["colors_used_within_declared_palette"])
        self.assertTrue(qa["actual_palette_limit_ok"])

    def test_doctor_exception_is_not_production_ready(self):
        resolution = type("Resolution", (), {"executable": "/fake/aseprite", "candidates": ["/fake/aseprite"]})()
        with patch("pixelart.renderer.resolve_aseprite", return_value=resolution), patch(
            "pixelart.renderer.subprocess.run", side_effect=OSError("launch failed")
        ):
            report = doctor()
        self.assertFalse(report["production_ready"])
        self.assertIn("launch failed", report["aseprite_startup_error"])

    def test_doctor_cli_fails_when_not_production_ready(self):
        from pixelart.cli import main

        with patch("pixelart.cli.doctor", return_value={"production_ready": False, "aseprite": None}):
            self.assertEqual(main(["doctor"]), 2)

    @unittest.skipUnless(os.environ.get("ASEPRITE_NATIVE_TEST") == "1", "set ASEPRITE_NATIVE_TEST=1 for host Aseprite integration")
    def test_run_lua_savefile_never_mutates_original_source(self):
        from pixelart.renderer import require_aseprite

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scene_file = root / "scene.json"
            scene_file.write_text(json.dumps(minimal_scene()), encoding="utf-8")
            executable = require_aseprite()
            source_dir = root / "source"
            render_scene(minimal_scene(), scene_file, source_dir, aseprite=executable)
            original = source_dir / "source.aseprite"
            original_digest = hashlib.sha256(original.read_bytes()).hexdigest()
            script = root / "save.lua"
            script.write_text(
                "local cel = app.activeSprite.layers[1]:cel(1)\n"
                "cel.image:putPixel(0, 0, Color{r=1, g=2, b=3, a=255})\n"
                "app.command.SaveFile()\n",
                encoding="utf-8",
            )
            result = run_lua(original, script, root / "edited", aseprite=executable)
            self.assertEqual(original_digest, hashlib.sha256(original.read_bytes()).hexdigest())
            edited = root / "edited" / result["edited"]
            self.assertTrue(edited.is_file())
            extracted, _ = _extract_aseprite(edited, executable, root / "extract")
            self.assertEqual(extracted[0].getpixel((0, 0)), (1, 2, 3, 255))

    @unittest.skipUnless(os.environ.get("ASEPRITE_NATIVE_TEST") == "1", "set ASEPRITE_NATIVE_TEST=1 for host Aseprite integration")
    def test_native_roundtrip_matches_layer_opacity_160(self):
        from pixelart.renderer import require_aseprite

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGBA", (1, 1), (248, 250, 252, 255)).save(root / "reference.png")
            scene = {
                "version": 1,
                "canvas": {"width": 3, "height": 2},
                "palette": ["#111827", "#eab308"],
                "frames": [{"duration": 70, "layers": [
                    {"name": "backdrop", "commands": [{"op": "rect", "x": 0, "y": 0, "width": 3, "height": 2, "color": 0}]},
                    {"name": "reference", "opacity": 160, "commands": [{"op": "image", "path": "reference.png", "x": 1, "y": 0}]},
                    {"name": "hidden-guide", "visible": False, "commands": [{"op": "rect", "x": 0, "y": 0, "width": 3, "height": 2, "color": 1}]}
                ]}],
            }
            scene_file = root / "opacity.json"
            scene_file.write_text(json.dumps(scene), encoding="utf-8")
            metadata = render_scene(scene, scene_file, root / "render", aseprite=require_aseprite())
            self.assertTrue(metadata["production_ready"])
            qa = json.loads((root / "render" / "qa.json").read_text())["technical"]
            self.assertTrue(qa["native_roundtrip"]["pixel_match"])
