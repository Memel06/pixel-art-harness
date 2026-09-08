import unittest
from re import escape
from json import loads
from pathlib import Path

from pixelart.errors import SceneError
from pixelart.scene import load_scene, validate_scene


def scene(**changes):
    value = {
        "version": 1,
        "canvas": {"width": 8, "height": 8},
        "palette": ["#000000", "#ffffff"],
        "frames": [{"duration": 100, "layers": [{"name": "ink", "commands": [{"op": "pixel", "x": 1, "y": 2, "color": 1}]}]}],
    }
    value.update(changes)
    return value


class SceneValidationTests(unittest.TestCase):
    def test_invalid_top_level_inputs_are_actionable(self):
        for mutated, fragment in (
            ({"version": True}, "scene.version"),
            ({"palette": [{"not": "a color"}]}, "scene.palette[0]"),
            ({"tags": {"name": "idle"}}, "scene.tags"),
            ({"frames": []}, "scene.frames"),
        ):
            with self.subTest(mutated=mutated), self.assertRaisesRegex(SceneError, escape(fragment)):
                validate_scene(scene(**mutated))


    def test_rejects_palette_index_outside_declared_palette(self):
        value = scene()
        value["frames"][0]["layers"][0]["commands"][0]["color"] = 2
        with self.assertRaisesRegex(SceneError, "palette index"):
            validate_scene(value)


    def test_rejects_per_frame_layer_property_changes(self):
        value = scene(
            frames=[
                {"layers": [{"name": "ink", "visible": True, "commands": []}]},
                {"layers": [{"name": "ink", "visible": False, "commands": []}]},
            ]
        )
        with self.assertRaisesRegex(SceneError, "visible and opacity"):
            validate_scene(value)

    def test_rejects_empty_layer_list_before_rendering(self):
        with self.assertRaisesRegex(SceneError, "at least one layer"):
            validate_scene(scene(frames=[{"layers": []}]))

    def test_schema_is_json_and_example_passes_runtime_validation(self):
        root = Path(__file__).parents[1]
        schema = loads((root / "examples" / "scene.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$defs"]["frame"]["properties"]["layers"]["minItems"], 1)
        loaded = load_scene(root / "examples" / "moonlit-courier.json")
        self.assertEqual(loaded["canvas"], {"width": 96, "height": 96})
