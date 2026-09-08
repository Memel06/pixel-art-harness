# Architecture and limits

The pipeline is deliberately small:

```text
Brief + references → model-authored scene JSON
                  → schema/semantic validation
                  → Pillow layer cels and composite frames
                  → Aseprite Lua assembly
                  → reopen and compare native pixels + durations
                  → source, exports, technical QA
                  → model/human image review → revised scene
```

`pixelart/scene.py` validates the integer-grid DSL. `pixelart/renderer.py` stages
PNG cels with Pillow, assembles a native document using packaged
`pixelart/lua/import_layers.lua`, then re-exports through Aseprite. The compositor
matches Aseprite's normal-layer integer alpha arithmetic. Native round-trip
checks reject mismatched pixels, dimensions, frame counts or durations.

Output is built in a temporary sibling directory and renamed after successful
checks. Failures remove staging; process errors include diagnostic text.
One writer should own each output path. Concurrent publication to the same path
is not a supported coordination mechanism.

## Artifact contract

| Artifact | Purpose |
| --- | --- |
| `source.aseprite` | Editable native document; omitted in diagnostic raster mode. |
| `scene.json` | Snapshot of the input specification. Imported images still belong to the original scene directory. |
| `sheet.png`, `frames/` | Full-color horizontal sheet and native-size frames. |
| `layers/` | Per-frame layer cels before document visibility/opacity. |
| `metadata.json` | Canvas, layers, palette, frame timing, tags and export locations. |
| `preview.png`, `preview.gif` | Convenient enlarged still and animation preview. |
| `qa.json` | Technical measurements and native round-trip results. |
| `review.json`, `review/` | Pending visual-review record, contacts, silhouettes and palette. |

The metadata format identifier is `aseprite-pixelart-harness/v1`. The Python
module and CLI are named `pixelart`; Pixel Art Harness is the project name.

## Known limits

- JSON rendering uses RGBA, flat layers and normal blending. It does not model
  every Aseprite feature (groups, tilemaps, blend modes or linked cels). Use Lua
  or the application for richer edits.
- Layer names, order, visibility and opacity must stay constant across frames.
  Frame variation lives in cels. Tags use inclusive zero-based frame indexes.
- QA reports colors outside the declared palette; it does not quantize imports
  or reject an otherwise valid render for that report alone.
- Preview GIFs are viewing aids: GIF palette, transparency and timing constraints
  make the native source and PNG exports the authoritative assets.
- Pixel agreement does not prove artistic quality, and exported composite checks
  alone do not prove every internal Aseprite property. Native tests exercise
  selected layer, opacity and editing behavior.
- Imported image paths use forward slashes and stay within the scene directory,
  including after symlink resolution. Keep references beside the authored scene.
- Layer compositing is pure Python, roughly 0.15 s per 512×512 layer. Large
  canvases with many layers and frames take minutes rather than seconds.
- Canvas dimensions are bounded, but total scene complexity is not a resource
  sandbox. Run untrusted scripts and workloads under your host's isolation rules.
- Reproduction depends on the scene, imported images and tool versions. Record
  Python, Pillow and Aseprite versions when reporting a rendering discrepancy.
