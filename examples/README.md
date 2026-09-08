# Scene DSL v1

`skywhale.json` is the showcase: a 320×208 flying whale with a lantern-lit
observatory town, eight layers, 24 declared colors and four 180 ms frames.
Render with `pixelart render examples/skywhale.json --out output/demo`.
The deterministic authoring script `python examples/build_skywhale.py` rebuilds
the scene from integer-grid shapes without external images. See the
[brief](skywhale-brief.md) and [visual review](../docs/visual-review.md).


`moonlit-courier.json` is a 96×96, six-layer, four-frame Aseprite source example. Run it with `pixelart render examples/moonlit-courier.json --out output/moonlit-courier` after `pixelart doctor` reports production ready.

The structural machine-readable contract is [scene.schema.json](scene.schema.json). The runtime also checks semantic rules such as palette indexes, matching layers and tag ranges. Coordinates are integer canvas pixels. A frame contains the same ordered layers as every other frame; layer `visible` and `opacity` are document properties and therefore must remain the same across frames. Per-frame variation belongs in each layer’s command list.

Commands are `pixel`, `line`, `rect`, `ellipse`, `polygon`, and `image`. Colors are either zero-based palette indexes or `#RRGGBB` / `#RRGGBBAA`; imported image paths are relative to the scene and cannot escape its directory. `image.scale` uses nearest-neighbor integer enlargement.

Each render produces `source.aseprite`, `sheet.png`, `frames/`, `layers/`, `preview.png`, `preview.gif`, `qa.json`, and `review/`. Before publication, the harness re-exports `source.aseprite` through Aseprite and refuses an output unless frame pixels and durations match the staged render.


Minimal scene (`scene.json`):

```json
{
  "version": 1,
  "canvas": {"width": 8, "height": 8},
  "palette": ["#00000000", "#f5b942"],
  "frames": [{
    "duration": 100,
    "layers": [{
      "name": "light",
      "commands": [{"op": "rect", "x": 2, "y": 2, "width": 4, "height": 4, "color": 1}]
    }]
  }]
}
```

Layers are ordered bottom to top. Shapes clip at the canvas edge; coordinates
can be negative. Rectangle dimensions count pixels, lines are one pixel wide,
and shapes default to filled. An empty command list gives an empty cel. Color
alpha and layer opacity can introduce colors outside the declared palette;
inspect `qa.json` when a strict palette is part of the brief.

GIF previews use binary transparency (alpha below 128 becomes transparent) and
at most 255 opaque colors per frame. PNGs and native sources retain full RGBA.
