# Pixel Art Harness

**A model-agnostic pixel-art workflow for Aseprite.**

Give an agent a brief, let it author a scene or Lua script, and deliver editable
sprites with review images. Pixel Art Harness handles integer-grid drawing, Aseprite
assembly and export checks. Your model handles art direction and visual revision.

![Skywhale observatory — a lantern-lit city traveling above a twilight cloud ocean](docs/demo-preview.png)

*Skywhale Observatory: an original 320×208 scene, eight editable layers, 24-color
palette and four animation frames. Authored entirely with the drawing DSL.

## What it does

- Draws pixels, lines, rectangles, ellipses, polygons and imported image cels.
- Produces layered `.aseprite` sources with frame durations and animation tags.
- Reopens native output and checks exported pixels and timing against staging.
- Exports PNG sheets, individual frames, previews, silhouettes and technical QA.
- Applies Lua edits to a staged copy of an existing document.

There is no model SDK, API key, subscription or hosted service in the harness.
An agent needs file access, command execution and an image-viewing tool. Visual
quality depends on the model, the brief and actual review; QA is not an art score.

## Quick start

Requires **Python 3.10+** and a separately installed **Lua-enabled Aseprite**.
From a downloaded or cloned checkout, create and activate a virtual environment:

| macOS / Linux | Windows PowerShell |
| --- | --- |
| `python3 -m venv .venv` | `py -m venv .venv` |
| `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |

Then, on any platform:

```sh
python -m pip install .
pixelart doctor
python -c "from pathlib import Path; Path('output').mkdir(exist_ok=True)"
pixelart render examples/skywhale.json --out output/demo
```

If Aseprite is not on PATH, set `ASEPRITE_BIN` to its executable or run
`pixelart --aseprite "path/to/executable" doctor`. See [setup](SETUP.md) for
platform-specific examples and troubleshooting. No package-index publication is
assumed; install from this checkout.

Open `output/demo/source.aseprite` in Aseprite. Inspect the individual
`frames/` at native size and `review/contact.png` enlarged. Each revision needs a
new output directory; existing output is refused.

Try the raster pipeline without Aseprite using `render ... --raster-only`.
This diagnostic mode does not produce an editable document.

## Connect your agent

Read the [integration guide](docs/integration.md) for a provider-neutral prompt,
tool contract, subprocess example and optional skill installation. The included
`aseprite-pixelart` skill adds an author → render → view → revise workflow.

```sh
python tools/install-skill.py --skills-dir path/to/your/agent/skills
```

The installer copies a self-contained skill, schema and example; it works without
symlinks. The CLI and Aseprite must be installed in the agent's execution environment.

## Documentation

- [Setup and platform support](SETUP.md)
- [Model and harness integration](docs/integration.md)
- [Scene format and examples](examples/README.md)
- [Architecture and limitations](docs/architecture.md)
- [Validation evidence](docs/validation.md)
- [Contributing](CONTRIBUTING.md)

## Status and license

Early release, with native validation on Apple Silicon macOS. Portable tests and
package checks are configured for Linux, macOS and Windows in GitHub Actions;
that configuration is not evidence of native Aseprite support on all three.

Original code, documentation and examples are [MIT licensed](LICENSE). Aseprite
is provided separately and has its own terms; see [third-party notices](THIRD_PARTY.md).
Pixel Art Harness is an independent project and is not affiliated with Aseprite.
