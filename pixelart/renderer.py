"""Deterministic Pillow staging and Aseprite batch assembly."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from importlib import resources
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import PIL
from PIL import Image, ImageDraw

from .errors import AsepriteNotFound, PixelartError, SceneError
from .scene import parse_color, validate_scene


@dataclass(frozen=True)
class AsepriteResolution:
    executable: str | None
    candidates: list[str]


def resolve_aseprite(explicit: str | None = None) -> AsepriteResolution:
    """Resolve Aseprite without downloading or installing anything."""
    # An explicit choice is authoritative: a typo must not launch another build.
    configured = explicit if explicit is not None else os.environ.get("ASEPRITE_BIN")
    raw_candidates = [configured] if configured is not None else ["aseprite"]
    candidates = [str(Path(value).expanduser()) for value in raw_candidates]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved and Path(resolved).is_file():
            return AsepriteResolution(str(Path(resolved).resolve()), candidates)
    return AsepriteResolution(None, candidates)


def require_aseprite(explicit: str | None = None) -> str:
    resolution = resolve_aseprite(explicit)
    if resolution.executable:
        return resolution.executable
    searched = "\n  ".join(resolution.candidates) or "(no candidates)"
    raise AsepriteNotFound(
        "Aseprite is required for an editable .aseprite source. Set --aseprite or ASEPRITE_BIN, "
        f"or put aseprite on PATH. Searched:\n  {searched}"
    )


def doctor(explicit: str | None = None) -> dict[str, Any]:
    resolution = resolve_aseprite(explicit)
    result: dict[str, Any] = {
        "aseprite": resolution.executable,
        "candidates": resolution.candidates,
        "pillow": PIL.__version__,
        "production_ready": resolution.executable is not None,
    }
    if resolution.executable:
        try:
            process = subprocess.run(
                [resolution.executable, "--version"], capture_output=True, text=True, check=False, timeout=15
            )
            version = (process.stdout or process.stderr).strip()
            result["aseprite_version"] = version
            if process.returncode != 0 or not re.match(r"^Aseprite\s+\d", version):
                result["production_ready"] = False
                result["aseprite_startup_error"] = (
                    f"Expected an Aseprite version; --version exited {process.returncode}" + (f": {version}" if version else " with no output")
                )
            else:
                with tempfile.TemporaryDirectory(prefix="pixelart-doctor-") as temporary:
                    script = Path(temporary) / "probe.lua"
                    script.write_text(
                        'local s = Sprite{width=1, height=1, colorMode=ColorMode.RGB}\n'
                        'assert(s.width == 1 and json.encode({ok=true}))\n'
                        's:close()\nprint("PIXELART_LUA_READY")\n', encoding="utf-8"
                    )
                    probe = subprocess.run(
                        [resolution.executable, "--batch", "--script", str(script)],
                        capture_output=True, text=True, check=False, timeout=15,
                    )
                    result["lua_ready"] = probe.returncode == 0 and "PIXELART_LUA_READY" in probe.stdout.splitlines()
                    result["production_ready"] = result["lua_ready"]
                    if not result["lua_ready"]:
                        result["aseprite_startup_error"] = "Aseprite Lua capability probe failed: " + (probe.stderr or probe.stdout).strip()[-800:]
        except (OSError, subprocess.SubprocessError) as exc:
            result["production_ready"] = False
            result["aseprite_startup_error"] = str(exc)
    return result


def _create_stage(output: Path) -> Path:
    output = output.resolve()
    if output.exists():
        raise PixelartError(f"output directory already exists: {output} (choose a new directory)")
    if not output.parent.exists():
        raise PixelartError(f"output parent directory does not exist: {output.parent}")
    return Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))


def _publish(stage: Path, output: Path) -> None:
    # output is verified absent before staging, so rename is an atomic publication on one filesystem.
    stage.replace(output)


def _hex(color: tuple[int, int, int, int]) -> str:
    if color[3] == 255:
        return "#%02x%02x%02x" % color[:3]
    return "#%02x%02x%02x%02x" % color


def _pixels(image: Image.Image):
    """Return pixels on Pillow 10+ without requiring Pillow 12.1's new API."""
    flattened = getattr(image, "get_flattened_data", None)
    return flattened() if flattened else image.getdata()


# Normal blending follows MIT-licensed Aseprite doc code and Pixman arithmetic.
# Copyright and permission notices are preserved in THIRD_PARTY.md.
def _mul_un8(left: int, right: int) -> int:
    """Aseprite/Pixman MUL_UN8: rounded multiplication on the 0..255 grid."""
    product = left * right + 0x80
    return ((product >> 8) + product) >> 8


def _trunc_div(numerator: int, denominator: int) -> int:
    """C++ integer division truncates toward zero, unlike Python // for negatives."""
    return numerator // denominator if numerator >= 0 else -((-numerator) // denominator)


def _aseprite_normal_composite(backdrop: Image.Image, source: Image.Image, opacity: int) -> Image.Image:
    """Composite NORMAL RGB layers with Aseprite's exact integer arithmetic."""
    if backdrop.size != source.size:
        raise PixelartError("cannot composite layers with different dimensions")
    result = Image.new("RGBA", backdrop.size, (0, 0, 0, 0))
    output = bytearray(result.width * result.height * 4)
    for index, (base, top) in enumerate(zip(_pixels(backdrop), _pixels(source))):
        br, bg, bb, ba = base
        sr, sg, sb, sa = top
        effective_alpha = _mul_un8(sa, opacity)
        if ba == 0:
            red, green, blue, alpha = sr, sg, sb, effective_alpha
        elif sa == 0:
            red, green, blue, alpha = br, bg, bb, ba
        else:
            alpha = effective_alpha + ba - _mul_un8(ba, effective_alpha)
            red = br + _trunc_div((sr - br) * effective_alpha, alpha)
            green = bg + _trunc_div((sg - bg) * effective_alpha, alpha)
            blue = bb + _trunc_div((sb - bb) * effective_alpha, alpha)
        offset = index * 4
        output[offset : offset + 4] = bytes((red, green, blue, alpha))
    return Image.frombytes("RGBA", backdrop.size, bytes(output))


def _command_image(command: dict[str, Any], palette: list[str], base_dir: Path, canvas: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", canvas, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    op = command["op"]
    if op == "pixel":
        draw.point((command["x"], command["y"]), fill=parse_color(command["color"], palette))
    elif op == "line":
        draw.line((command["x1"], command["y1"], command["x2"], command["y2"]), fill=parse_color(command["color"], palette), width=1)
    elif op == "rect":
        bounds = (command["x"], command["y"], command["x"] + command["width"] - 1, command["y"] + command["height"] - 1)
        if command.get("fill", True):
            draw.rectangle(bounds, fill=parse_color(command["color"], palette))
        else:
            draw.rectangle(bounds, outline=parse_color(command["color"], palette), width=1)
    elif op == "ellipse":
        bounds = (command["x"], command["y"], command["x"] + command["width"] - 1, command["y"] + command["height"] - 1)
        if command.get("fill", True):
            draw.ellipse(bounds, fill=parse_color(command["color"], palette))
        else:
            draw.ellipse(bounds, outline=parse_color(command["color"], palette), width=1)
    elif op == "polygon":
        points = [tuple(point) for point in command["points"]]
        if command.get("fill", True):
            draw.polygon(points, fill=parse_color(command["color"], palette))
        else:
            draw.line(points + [points[0]], fill=parse_color(command["color"], palette), width=1)
    elif op == "image":
        source = (base_dir / command["path"]).resolve()
        if not source.is_relative_to(base_dir.resolve()):
            raise SceneError("image command source must stay inside the scene directory")
        if not source.is_file():
            raise SceneError(f"image command source not found: {source}")
        with Image.open(source) as imported:
            imported = imported.convert("RGBA")
        scale = command.get("scale", 1)
        if scale != 1:
            imported = imported.resize((imported.width * scale, imported.height * scale), Image.Resampling.NEAREST)
        if "opacity" in command:
            alpha = imported.getchannel("A").point(lambda value: value * command["opacity"] // 255)
            imported.putalpha(alpha)
        image.alpha_composite(imported, (command["x"], command["y"]))
    return image


def render_layer(layer: dict[str, Any], scene: dict[str, Any], base_dir: Path) -> Image.Image:
    canvas = (scene["canvas"]["width"], scene["canvas"]["height"])
    image = Image.new("RGBA", canvas, (0, 0, 0, 0))
    for command in layer["commands"]:
        image.alpha_composite(_command_image(command, scene["palette"], base_dir, canvas))
    return image


def _render_frames(scene: dict[str, Any], base_dir: Path) -> tuple[list[list[Image.Image]], list[Image.Image]]:
    all_layers: list[list[Image.Image]] = []
    composited: list[Image.Image] = []
    for frame in scene["frames"]:
        layers = [render_layer(layer, scene, base_dir) for layer in frame["layers"]]
        merged = Image.new("RGBA", layers[0].size, (0, 0, 0, 0))
        for image, layer in zip(layers, frame["layers"]):
            if not layer.get("visible", True):
                continue
            merged = _aseprite_normal_composite(merged, image, layer.get("opacity", 255))
        all_layers.append(layers)
        composited.append(merged)
    return all_layers, composited


def _frame_qa(image: Image.Image, index: int) -> dict[str, Any]:
    alpha = image.getchannel("A")
    histogram = alpha.histogram()
    opaque = histogram[255]
    transparent = histogram[0]
    partial = sum(histogram[1:255])
    bbox = alpha.getbbox()
    return {
        "index": index,
        "empty": bbox is None,
        "alpha": {"transparent_pixels": transparent, "opaque_pixels": opaque, "partial_pixels": partial},
        "silhouette_bounds": list(bbox) if bbox else None,
    }


def build_qa(frames: Iterable[Image.Image], scene: dict[str, Any] | None = None) -> dict[str, Any]:
    rendered = list(frames)
    if not rendered:
        raise PixelartError("cannot review an empty frame list")
    frame_rows = [_frame_qa(image, index) for index, image in enumerate(rendered)]
    colors = sorted(
        {_hex(pixel) for image in rendered for pixel in _pixels(image) if pixel[3] > 0}
    )
    payload: dict[str, Any] = {
        "technical": {
            "canvas": {"width": rendered[0].width, "height": rendered[0].height},
            "frame_count": len(rendered),
            "alpha": {
                "transparent_pixels": sum(row["alpha"]["transparent_pixels"] for row in frame_rows),
                "opaque_pixels": sum(row["alpha"]["opaque_pixels"] for row in frame_rows),
                "partial_pixels": sum(row["alpha"]["partial_pixels"] for row in frame_rows),
            },
            "colors_used": colors,
            "colors_used_count": len(colors),
            "empty_frames": [row["index"] for row in frame_rows if row["empty"]],
            "frames": frame_rows,
        }
    }
    if scene:
        declared_colors = {_hex(parse_color(color, [])) for color in scene["palette"]}
        out_of_palette = [color for color in colors if color not in declared_colors]
        payload["technical"]["declared_palette"] = scene["palette"]
        payload["technical"]["declared_palette_count"] = len(scene["palette"])
        payload["technical"]["actual_palette_limit_ok"] = len(colors) <= 256
        payload["technical"]["palette_limit_ok"] = len(colors) <= 256
        payload["technical"]["out_of_declared_palette_colors"] = out_of_palette
        payload["technical"]["colors_used_within_declared_palette"] = not out_of_palette
        payload["technical"]["frame_durations_ms"] = [frame.get("duration", 100) for frame in scene["frames"]]
        payload["technical"]["tags"] = scene.get("tags", [])
    return payload


def _nearest_scale(image: Image.Image, minimum: int = 384, maximum: int = 8) -> tuple[Image.Image, int]:
    scale = min(maximum, max(1, (minimum + max(image.width, image.height) - 1) // max(image.width, image.height)))
    return image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST), scale


def _write_review_images(
    frames: list[Image.Image],
    palette: list[str],
    destination: Path,
    *,
    layer_frames: list[list[Image.Image]] | None = None,
    layer_names: list[str] | None = None,
) -> dict[str, Any]:
    review_dir = destination / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        enlarged, _ = _nearest_scale(frame)
        enlarged.save(review_dir / f"frame-{index:03d}.png")
    enlarged_frames = [_nearest_scale(frame)[0] for frame in frames]
    cell_w = max(frame.width for frame in enlarged_frames)
    cell_h = max(frame.height for frame in enlarged_frames)
    columns = min(4, len(enlarged_frames))
    rows = (len(enlarged_frames) + columns - 1) // columns
    contact = Image.new("RGBA", (cell_w * columns, cell_h * rows), (18, 20, 29, 255))
    for index, frame in enumerate(enlarged_frames):
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        contact.alpha_composite(frame, (x, y))
    contact.save(review_dir / "contact.png")
    silhouettes: list[Image.Image] = []
    for frame in frames:
        alpha = frame.getchannel("A")
        silhouette = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        silhouette.putalpha(alpha)
        # White RGB is set separately so transparency remains meaningful.
        white = Image.new("RGBA", frame.size, (255, 255, 255, 0))
        white.putalpha(alpha)
        silhouettes.append(_nearest_scale(white)[0])
    silhouette_sheet = Image.new("RGBA", (cell_w * columns, cell_h * rows), (18, 20, 29, 255))
    for index, frame in enumerate(silhouettes):
        silhouette_sheet.alpha_composite(frame, ((index % columns) * cell_w, (index // columns) * cell_h))
    silhouette_sheet.save(review_dir / "silhouette.png")
    swatch = 24
    palette_image = Image.new("RGBA", (max(1, len(palette)) * swatch, swatch), (0, 0, 0, 0))
    palette_draw = ImageDraw.Draw(palette_image)
    for index, hex_color in enumerate(palette):
        palette_draw.rectangle((index * swatch, 0, (index + 1) * swatch - 1, swatch - 1), fill=parse_color(hex_color, []))
    palette_image.resize((palette_image.width * 2, palette_image.height * 2), Image.Resampling.NEAREST).save(review_dir / "palette.png")
    layer_silhouettes: dict[str, str] = {}
    if layer_frames and layer_names:
        layer_dir = review_dir / "layers"
        layer_dir.mkdir()
        for layer_index, name in enumerate(layer_names):
            per_frame = [frame_layers[layer_index] for frame_layers in layer_frames]
            per_frame_silhouettes: list[Image.Image] = []
            for frame in per_frame:
                mask = frame.getchannel("A")
                silhouette = Image.new("RGBA", frame.size, (255, 255, 255, 0))
                silhouette.putalpha(mask)
                per_frame_silhouettes.append(_nearest_scale(silhouette)[0])
            sheet = Image.new("RGBA", (cell_w * columns, cell_h * rows), (18, 20, 29, 255))
            for index, silhouette in enumerate(per_frame_silhouettes):
                sheet.alpha_composite(silhouette, ((index % columns) * cell_w, (index // columns) * cell_h))
            safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or f"layer-{layer_index:02d}"
            relative = f"review/layers/{layer_index:02d}-{safe_name}-silhouette.png"
            sheet.save(destination / relative)
            layer_silhouettes[name] = relative
    return {
        "frame_images": [f"review/frame-{index:03d}.png" for index in range(len(frames))],
        "contact_sheet": "review/contact.png",
        "silhouette_sheet": "review/silhouette.png",
        "palette_strip": "review/palette.png",
        "layer_silhouettes": layer_silhouettes,
        "scale": _nearest_scale(frames[0])[1],
    }


def _write_sheet(frames: list[Image.Image], destination: Path) -> None:
    sheet = Image.new("RGBA", (frames[0].width * len(frames), frames[0].height), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * frame.width, 0))
    sheet.save(destination / "sheet.png")


def _write_preview(frames: list[Image.Image], durations: list[int], destination: Path) -> dict[str, Any]:
    preview, scale = _nearest_scale(frames[0])
    preview.save(destination / "preview.png")
    # Reserve index 255 explicitly: assigning transparency=0 to Pillow's
    # automatic palette can make an opaque scene's most common color vanish.
    animated = []
    has_transparency = any(frame.getchannel("A").getextrema()[0] < 128 for frame in frames)
    for frame in frames:
        enlarged = _nearest_scale(frame)[0]
        indexed = enlarged.convert("RGB").quantize(colors=255, dither=Image.Dither.NONE)
        if has_transparency:
            mask = enlarged.getchannel("A").point(lambda alpha: 255 if alpha < 128 else 0)
            indexed.paste(255, mask=mask)
        animated.append(indexed)
    gif_options = {"transparency": 255} if has_transparency else {}
    animated[0].save(
        destination / "preview.gif",
        save_all=True,
        append_images=animated[1:],
        loop=0,
        duration=durations,
        disposal=2,
        optimize=False,
        **gif_options,
    )
    return {"preview": "preview.png", "animated_preview": "preview.gif", "nearest_scale": scale}


def _assemble_manifest(scene: dict[str, Any], layer_paths: list[list[Path]], output: Path) -> dict[str, Any]:
    return {
        "width": scene["canvas"]["width"],
        "height": scene["canvas"]["height"],
        "palette": scene["palette"],
        "output": str(output),
        "layers": [
            {
                "name": layer["name"],
                "visible": layer.get("visible", True),
                "opacity": layer.get("opacity", 255),
            }
            for layer in scene["frames"][0]["layers"]
        ],
        "frames": [
            {
                "duration": frame.get("duration", 100),
                "cels": [str(path) for path in paths],
            }
            for frame, paths in zip(scene["frames"], layer_paths)
        ],
        "tags": scene.get("tags", []),
    }


def _assemble_aseprite(scene: dict[str, Any], layer_paths: list[list[Path]], destination: Path, executable: str) -> None:
    build_dir = destination / "build"
    build_dir.mkdir(exist_ok=True)
    source = destination / "source.aseprite"
    manifest = _assemble_manifest(scene, layer_paths, source)
    manifest_path = build_dir / "aseprite-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    script = Path(resources.files("pixelart.lua").joinpath("import_layers.lua"))
    if not script.is_file():
        raise PixelartError("required packaged Aseprite import script is missing: pixelart/lua/import_layers.lua")
    process = subprocess.run(
        [executable, "--batch", "--script-param", f"manifest={manifest_path}", "--script", str(script)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    (build_dir / "aseprite.log").write_text(process.stdout + process.stderr, encoding="utf-8")
    if process.returncode != 0 or not source.is_file():
        detail = (process.stderr or process.stdout).strip().replace("\n", " ")[-800:]
        raise PixelartError(
            "Aseprite could not assemble the editable source "
            f"(exit={process.returncode}): {detail or 'no process output'}"
        )


def _verify_native_roundtrip(
    expected: list[Image.Image], exported: list[Image.Image], export_data: dict[str, Any], durations: list[int]
) -> dict[str, Any]:
    """Reject a source document whose exported composite diverges from staging PNGs."""
    if len(expected) != len(exported):
        raise PixelartError(f"native Aseprite roundtrip exported {len(exported)} frames; expected {len(expected)}")
    for index, (reference, actual) in enumerate(zip(expected, exported)):
        if reference.size != actual.size:
            raise PixelartError(
                f"native Aseprite roundtrip frame {index} is {actual.width}x{actual.height}; "
                f"expected {reference.width}x{reference.height}"
            )
        if reference.tobytes() != actual.tobytes():
            raise PixelartError(f"native Aseprite roundtrip pixels differ from the staged composite in frame {index}")
    entries = export_data.get("frames", [])
    if isinstance(entries, dict):
        entries = list(entries.values())
    actual_durations = [entry.get("duration") for entry in entries]
    if actual_durations != durations:
        raise PixelartError(
            f"native Aseprite roundtrip durations are {actual_durations}; expected integer milliseconds {durations}"
        )
    return {"pixel_match": True, "durations_ms": actual_durations, "frame_count": len(exported)}


def render_scene(
    scene: dict[str, Any],
    scene_path: str | Path,
    output: str | Path,
    *,
    aseprite: str | None = None,
    raster_only: bool = False,
) -> dict[str, Any]:
    """Render a validated scene into a new atomically published output directory."""
    scene = validate_scene(scene)
    scene_path = Path(scene_path).resolve()
    output = Path(output).resolve()
    executable = None if raster_only else require_aseprite(aseprite)
    stage = _create_stage(output)
    try:
        all_layers, frames = _render_frames(scene, scene_path.parent)
        frame_dir = stage / "frames"
        layer_dir = stage / "layers"
        frame_dir.mkdir()
        layer_dir.mkdir()
        layer_paths: list[list[Path]] = []
        for frame_index, layer_images in enumerate(all_layers):
            current_paths: list[Path] = []
            for layer_index, image in enumerate(layer_images):
                path = layer_dir / f"frame-{frame_index:03d}-layer-{layer_index:02d}.png"
                image.save(path)
                current_paths.append(path)
            layer_paths.append(current_paths)
        durations = [frame.get("duration", 100) for frame in scene["frames"]]
        native_roundtrip: dict[str, Any] | None = None
        if executable:
            _assemble_aseprite(scene, layer_paths, stage, executable)
            native_stage = stage / "build" / "native-roundtrip"
            native_stage.mkdir()
            native_frames, native_export = _extract_aseprite(stage / "source.aseprite", executable, native_stage)
            native_roundtrip = _verify_native_roundtrip(frames, native_frames, native_export, durations)
            frames = native_frames
        for frame_index, merged in enumerate(frames):
            merged.save(frame_dir / f"frame-{frame_index:03d}.png")
        _write_sheet(frames, stage)
        previews = _write_preview(frames, durations, stage)
        review_files = _write_review_images(
            frames,
            scene["palette"],
            stage,
            layer_frames=all_layers,
            layer_names=[layer["name"] for layer in scene["frames"][0]["layers"]],
        )
        qa = build_qa(frames, scene)
        qa["technical"]["aseprite_source"] = "source.aseprite" if executable else None
        qa["technical"]["production_ready"] = executable is not None
        qa["technical"]["native_roundtrip"] = native_roundtrip
        (stage / "qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
        review = {
            "technical": qa["technical"],
            "visual_review": {
                "status": "pending_agent_or_human_review",
                "findings": [],
                "revisions": [],
                "checklist": [
                    "Check readable silhouette at native size and in review/silhouette.png.",
                    "Check frame-to-frame motion in preview.gif and review/contact.png.",
                    "Check palette hierarchy, focal contrast, and unintended tangencies.",
                    "Record concrete findings and resulting scene revisions here; do not infer aesthetics from technical QA.",
                ],
            },
            "artifacts": review_files,
        }
        (stage / "review.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
        metadata = {
            "format": "aseprite-pixelart-harness/v1",
            "source_scene": scene_path.name,
            "canvas": scene["canvas"],
            "frame_count": len(frames),
            "frames": [
                {"index": index, "name": frame.get("name", f"frame-{index:03d}"), "duration_ms": frame.get("duration", 100)}
                for index, frame in enumerate(scene["frames"])
            ],
            "layers": [layer["name"] for layer in scene["frames"][0]["layers"]],
            "palette": scene["palette"],
            "tags": scene.get("tags", []),
            "exports": {
                "sheet": "sheet.png",
                "frames": "frames/",
                "layer_cels": "layers/",
                "qa": "qa.json",
                "review": "review.json",
                **previews,
            },
            "editable_source": "source.aseprite" if executable else None,
            "production_ready": executable is not None,
            "raster_only": raster_only,
        }
        (stage / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (stage / "scene.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")
        shutil.rmtree(stage / "build", ignore_errors=True)
        _publish(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return json.loads((output / "metadata.json").read_text(encoding="utf-8"))


def _extract_aseprite(source: Path, executable: str, stage: Path) -> tuple[list[Image.Image], dict[str, Any]]:
    export = stage / "extracted-sheet.png"
    metadata = stage / "extracted-sheet.json"
    process = subprocess.run(
        [executable, "--batch", str(source), "--sheet", str(export), "--data", str(metadata), "--format", "json-array", "--sheet-type", "horizontal"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    (stage / "aseprite-extract.log").write_text(process.stdout + process.stderr, encoding="utf-8")
    if process.returncode != 0 or not export.is_file() or not metadata.is_file():
        raise PixelartError(f"Aseprite could not export {source} (exit={process.returncode}): "
                            + (process.stderr or process.stdout).strip()[-800:])
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    entries = payload.get("frames", [])
    if isinstance(entries, dict):
        entries = list(entries.values())
    frames: list[Image.Image] = []
    with Image.open(export) as sheet:
        sheet = sheet.convert("RGBA")
        for entry in entries:
            frame = entry["frame"]
            frames.append(sheet.crop((frame["x"], frame["y"], frame["x"] + frame["w"], frame["y"] + frame["h"])))
    if not frames:
        raise PixelartError("Aseprite export contained no frames")
    return frames, payload


def inspect_file(path: str | Path, *, aseprite: str | None = None) -> dict[str, Any]:
    source = Path(path).resolve()
    if not source.is_file():
        raise PixelartError(f"input file not found: {source}")
    if source.suffix.lower() != ".aseprite":
        with Image.open(source) as image:
            frame = image.convert("RGBA")
        qa = build_qa([frame])
        return {"input": str(source), "kind": "raster", **qa}
    executable = require_aseprite(aseprite)
    with tempfile.TemporaryDirectory(prefix="pixelart-inspect-") as temporary:
        stage = Path(temporary)
        frames, export_data = _extract_aseprite(source, executable, stage)
        listing = subprocess.run(
            [executable, "--batch", "--list-layers", "--list-tags", str(source)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        qa = build_qa(frames)
    return {
        "input": str(source),
        "kind": "aseprite",
        "aseprite_listing": listing.stdout.strip(),
        "aseprite_listing_stderr": listing.stderr.strip(),
        "aseprite_export": export_data,
        **qa,
    }


def review_file(path: str | Path, output: str | Path, *, aseprite: str | None = None) -> dict[str, Any]:
    source = Path(path).resolve()
    output = Path(output).resolve()
    if not source.is_file():
        raise PixelartError(f"input file not found: {source}")
    stage = _create_stage(output)
    try:
        source_info: dict[str, Any] = {"input": str(source), "kind": "raster"}
        if source.suffix.lower() == ".aseprite":
            frames, exported = _extract_aseprite(source, require_aseprite(aseprite), stage)
            source_info = {"input": str(source), "kind": "aseprite", "aseprite_export": exported}
        else:
            with Image.open(source) as image:
                frames = [image.convert("RGBA")]
        frame_dir = stage / "frames"
        frame_dir.mkdir()
        for index, frame in enumerate(frames):
            frame.save(frame_dir / f"frame-{index:03d}.png")
        palette = sorted({_hex(pixel) for frame in frames for pixel in _pixels(frame) if pixel[3] > 0})
        review_files = _write_review_images(frames, palette, stage)
        qa = build_qa(frames)
        (stage / "qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
        result = {
            **source_info,
            "technical": qa["technical"],
            "visual_review": {
                "status": "pending_agent_or_human_review",
                "findings": [],
                "revisions": [],
                "checklist": [
                    "Review native-size readability and enlarged frame images.",
                    "Review silhouette separation and animation continuity.",
                    "Add only observations supported by viewing the review image artifacts.",
                ],
            },
            "artifacts": review_files,
        }
        (stage / "review.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        _publish(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return result


def run_lua(
    source: str | Path,
    script: str | Path,
    output: str | Path,
    *,
    aseprite: str | None = None,
    params: list[str] | None = None,
) -> dict[str, Any]:
    """Apply Lua to a staged copy. Scripts retain arbitrary host filesystem access."""
    source = Path(source).resolve()
    script = Path(script).resolve()
    output = Path(output).resolve()
    if source.suffix.lower() != ".aseprite" or not source.is_file():
        raise PixelartError("run-lua SOURCE must be an existing .aseprite file")
    if not script.is_file():
        raise PixelartError(f"Lua script not found: {script}")
    executable = require_aseprite(aseprite)
    stage = _create_stage(output)
    try:
        edited = stage / "source.aseprite"
        shutil.copy2(source, edited)
        command = [executable, "--batch", str(edited)]
        for parameter in params or []:
            if "=" not in parameter:
                raise PixelartError(f"--param must have key=value form: {parameter}")
            command.extend(["--script-param", parameter])
        command.extend(["--script", str(script), "--save-as", str(edited)])
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
        (stage / "aseprite.log").write_text(process.stdout + process.stderr, encoding="utf-8")
        if process.returncode != 0 or not edited.is_file():
            raise PixelartError(f"Lua edit failed (exit={process.returncode}): "
                                + (process.stderr or process.stdout).strip()[-800:])
        inspection = inspect_file(edited, aseprite=executable)
        (stage / "inspection.json").write_text(json.dumps(inspection, indent=2), encoding="utf-8")
        _publish(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {"source": str(source), "edited": "source.aseprite", "inspection": "inspection.json"}
