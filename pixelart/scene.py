"""Validation for the deliberately small, integer-grid scene DSL."""

from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath
from typing import Any

from .errors import SceneError

MAX_CANVAS = 2048
MAX_PALETTE = 256
_HEX = re.compile(r"^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")
_OPS = {"pixel", "line", "rect", "ellipse", "polygon", "image"}


def _error(path: str, message: str) -> None:
    raise SceneError(f"{path}: {message}")


def _integer(value: Any, path: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _error(path, "must be an integer")
    if minimum is not None and value < minimum:
        _error(path, f"must be at least {minimum}")
    return value


def parse_color(value: Any, palette: list[str], path: str = "color") -> tuple[int, int, int, int]:
    """Resolve a palette index or #RRGGBB[AA] color to an RGBA tuple."""
    if isinstance(value, bool):
        _error(path, "must be a palette index or #RRGGBB[AA]")
    if isinstance(value, int):
        if not 0 <= value < len(palette):
            _error(path, f"palette index must be between 0 and {len(palette) - 1}")
        value = palette[value]
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        _error(path, "must be a palette index or #RRGGBB[AA]")
    digits = value[1:]
    if len(digits) == 6:
        digits += "ff"
    return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16), int(digits[6:8], 16))


def _expect_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _error(path, "must be an object")
    return value


def _expect_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        _error(path, "must be an array")
    return value


def _validate_command(command: Any, palette: list[str], path: str) -> None:
    item = _expect_object(command, path)
    op = item.get("op")
    if not isinstance(op, str) or op not in _OPS:
        _error(f"{path}.op", f"must be one of {', '.join(sorted(_OPS))}")

    def coord(name: str) -> int:
        return _integer(item.get(name), f"{path}.{name}")

    if op == "pixel":
        coord("x"); coord("y"); parse_color(item.get("color"), palette, f"{path}.color")
    elif op == "line":
        for name in ("x1", "y1", "x2", "y2"):
            coord(name)
        parse_color(item.get("color"), palette, f"{path}.color")
    elif op in {"rect", "ellipse"}:
        coord("x"); coord("y")
        _integer(item.get("width"), f"{path}.width", minimum=1)
        _integer(item.get("height"), f"{path}.height", minimum=1)
        parse_color(item.get("color"), palette, f"{path}.color")
        if "fill" in item and not isinstance(item["fill"], bool):
            _error(f"{path}.fill", "must be true or false")
    elif op == "polygon":
        points = _expect_list(item.get("points"), f"{path}.points")
        if len(points) < 3:
            _error(f"{path}.points", "must contain at least three [x, y] points")
        for i, point in enumerate(points):
            point = _expect_list(point, f"{path}.points[{i}]")
            if len(point) != 2:
                _error(f"{path}.points[{i}]", "must contain exactly [x, y]")
            _integer(point[0], f"{path}.points[{i}][0]")
            _integer(point[1], f"{path}.points[{i}][1]")
        parse_color(item.get("color"), palette, f"{path}.color")
        if "fill" in item and not isinstance(item["fill"], bool):
            _error(f"{path}.fill", "must be true or false")
    elif op == "image":
        if not isinstance(item.get("path"), str) or not item["path"]:
            _error(f"{path}.path", "must be a non-empty relative image path")
        image_path = Path(item["path"])
        if image_path.is_absolute() or PureWindowsPath(item["path"]).drive or "\\" in item["path"] or ".." in image_path.parts:
            _error(f"{path}.path", "must stay inside the scene directory")
        coord("x"); coord("y")
        if "scale" in item:
            _integer(item["scale"], f"{path}.scale", minimum=1)
        if "opacity" in item:
            opacity = _integer(item["opacity"], f"{path}.opacity", minimum=0)
            if opacity > 255:
                _error(f"{path}.opacity", "must be at most 255")


def validate_scene(scene: Any) -> dict[str, Any]:
    """Validate and return *scene*. All painting coordinates remain integers."""
    scene = _expect_object(scene, "scene")
    if isinstance(scene.get("version"), bool) or scene.get("version") != 1:
        _error("scene.version", "must be 1")
    canvas = _expect_object(scene.get("canvas"), "scene.canvas")
    _integer(canvas.get("width"), "scene.canvas.width", minimum=1)
    _integer(canvas.get("height"), "scene.canvas.height", minimum=1)
    if canvas["width"] > MAX_CANVAS or canvas["height"] > MAX_CANVAS:
        _error("scene.canvas", f"width and height must not exceed {MAX_CANVAS}")
    palette = _expect_list(scene.get("palette"), "scene.palette")
    if not palette or len(palette) > MAX_PALETTE:
        _error("scene.palette", f"must contain 1 to {MAX_PALETTE} colors")
    for i, color in enumerate(palette):
        parse_color(color, [], f"scene.palette[{i}]")
    if len(set(palette)) != len(palette):
        _error("scene.palette", "must not contain duplicate colors")
    frames = _expect_list(scene.get("frames"), "scene.frames")
    if not frames:
        _error("scene.frames", "must contain at least one frame")
    layer_names: list[str] | None = None
    layer_states: list[tuple[bool, int]] | None = None
    for frame_i, frame in enumerate(frames):
        frame = _expect_object(frame, f"scene.frames[{frame_i}]")
        if "name" in frame and (not isinstance(frame["name"], str) or not frame["name"]):
            _error(f"scene.frames[{frame_i}].name", "must be a non-empty string")
        _integer(frame.get("duration", 100), f"scene.frames[{frame_i}].duration", minimum=1)
        layers = _expect_list(frame.get("layers"), f"scene.frames[{frame_i}].layers")
        if not layers:
            _error(f"scene.frames[{frame_i}].layers", "must contain at least one layer")
        names: list[str] = []
        states: list[tuple[bool, int]] = []
        for layer_i, layer in enumerate(layers):
            layer = _expect_object(layer, f"scene.frames[{frame_i}].layers[{layer_i}]")
            name = layer.get("name")
            if not isinstance(name, str) or not name:
                _error(f"scene.frames[{frame_i}].layers[{layer_i}].name", "must be a non-empty string")
            names.append(name)
            if "visible" in layer and not isinstance(layer["visible"], bool):
                _error(f"scene.frames[{frame_i}].layers[{layer_i}].visible", "must be true or false")
            if "opacity" in layer:
                opacity = _integer(layer["opacity"], f"scene.frames[{frame_i}].layers[{layer_i}].opacity", minimum=0)
                if opacity > 255:
                    _error(f"scene.frames[{frame_i}].layers[{layer_i}].opacity", "must be at most 255")
            else:
                opacity = 255
            states.append((layer.get("visible", True), opacity))
            commands = _expect_list(layer.get("commands"), f"scene.frames[{frame_i}].layers[{layer_i}].commands")
            for command_i, command in enumerate(commands):
                _validate_command(command, palette, f"scene.frames[{frame_i}].layers[{layer_i}].commands[{command_i}]")
        if len(set(names)) != len(names):
            _error(f"scene.frames[{frame_i}].layers", "must not repeat a layer name")
        if layer_names is None:
            layer_names = names
            layer_states = states
        elif names != layer_names:
            _error(f"scene.frames[{frame_i}].layers", "must use the same layer names and order as frame 0")
        elif states != layer_states:
            _error(
                f"scene.frames[{frame_i}].layers",
                "must keep each layer's visible and opacity settings consistent across frames; cels hold frame variation",
            )
    tags = _expect_list(scene.get("tags", []), "scene.tags")
    for tag_i, tag in enumerate(tags):
        tag = _expect_object(tag, f"scene.tags[{tag_i}]")
        if not isinstance(tag.get("name"), str) or not tag["name"]:
            _error(f"scene.tags[{tag_i}].name", "must be a non-empty string")
        start = _integer(tag.get("from"), f"scene.tags[{tag_i}].from", minimum=0)
        end = _integer(tag.get("to"), f"scene.tags[{tag_i}].to", minimum=0)
        if start > end or end >= len(frames):
            _error(f"scene.tags[{tag_i}]", "must select an inclusive range inside frames")
        if not isinstance(tag.get("direction", "forward"), str) or tag.get("direction", "forward") not in {"forward", "reverse", "pingpong", "pingpong_reverse"}:
            _error(f"scene.tags[{tag_i}].direction", "must be forward, reverse, pingpong, or pingpong_reverse")
    return scene


def load_scene(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SceneError(f"scene file not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise SceneError(f"invalid JSON in {source}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    return validate_scene(data)
