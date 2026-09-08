---
name: aseprite-pixelart
description: Create, edit, visually critique, and refine native pixel-art assets with Aseprite, including layered sprites, animation, and reference-assisted art. Use for pixel-art requests; deliver editable sources and inspected exports.
---

Use the installed `pixelart` CLI (or `python -m pixelart`). Run `pixelart doctor` before native work. If it is unavailable, ask the host to provision Pixel Art Harness and a Lua-enabled Aseprite executable; configuration belongs to the host environment. The harness has no model API dependency. The host must provide file writing, command execution and image viewing.

For scene authoring, read `references/scene.schema.json` and `references/moonlit-courier.json` when present (the installer bundles them); in a source checkout they live under `../../examples/`. No repository location is needed at runtime. See `pixelart --help` and each command's help for arguments. Use `--aseprite` before the subcommand, or configure `ASEPRITE_BIN` / PATH. If Aseprite fails to start, report its actual error and use the host's supported execution permissions.

## Work from brief to inspected asset

1. Read relevant project art direction and supplied references. Establish native dimensions, camera, palette, transparency, animation timing and anchor; infer reasonable defaults when unspecified. Write a brief in the output working area. Read [art-direction.md](references/art-direction.md) for cluster design, reference handling and review criteria.
2. Choose original native-grid drawing or reference-assisted design. Optional image-generation tools may create concept references if the host supplies them. The harness itself needs no image API key. Inspect references, then deliberately author pixel clusters; a resized concept image is not a finished sprite.
3. Author a scene JSON using the documented schema, or use Aseprite Lua for work beyond the drawing DSL. Keep meaningful layers, frame durations and tags. Use new versioned output directories so previous art survives. `render` produces the native editable source and review exports. `run-lua` enables expressive changes to existing sources; read its CLI help before use.
4. **Open the actual output images with the host's image-viewing tool.** Inspect a native frame, the nearest-neighbor preview, silhouette and animation contact sheet. For motion, inspect playback if the environment supports it; otherwise state that only the frames/timing were reviewed. When the viewer scales small images, use the integer-upscaled view to inspect exact clusters, and assess composition separately at intended display size. Reading `qa.json` or generating images without viewing them does not complete this step.
5. Record an honest visual critique: concrete strengths, visible defects, and the next edit. Address the most consequential weakness, re-render, then open the affected outputs again. Evaluate the requested subject and style, not just generic neatness. Do not describe quality as verified when visual tools are unavailable. Technical QA cannot establish artistic merit.
6. Deliver `source.aseprite`, the PNG sheet and metadata, and a useful preview. Explain what was visually checked and any material weakness or untested behavior. Keep the brief and critique with the asset. Do not call a diagnostic raster-only export a completed Aseprite asset.

Original code and examples are MIT licensed. External reference rights and the downloaded Aseprite application have separate terms; keep their attribution and license terms with any distributed assets.
