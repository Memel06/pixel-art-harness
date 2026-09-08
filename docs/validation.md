# Validation

## End-to-end check — 8 September 2026

Checked on Apple Silicon macOS with Python 3.14.6, Pillow 12.3.0 and
Aseprite `1.3.18.3-13-g56757b5fc-dev`.

- **24 tests passed, zero skips** with `ASEPRITE_NATIVE_TEST=1` and
  `ASEPRITE_BIN` configured. Both examples passed JSON Schema validation.
- Release regressions additionally verify that `doctor` rejects non-Aseprite executables
  and missing Lua support, and that similar layer names cannot overwrite review images.
- Native integration verified imported image pixels, partial layer opacity,
  hidden layers and Lua SaveFile edits that preserve the original source hash.
- Skywhale rendered through Aseprite: 320×208, eight layers, four 180 ms frames,
  22 used colors within its 24-color palette. Every exported frame and duration
  matched staging exactly.
- Found and fixed a GIF palette-transparency bug. The new regression covers
  opaque backgrounds, transparent frame clearing, colors and timing. All four
  Skywhale GIF frames decode to exactly the corresponding PNG preview pixels.
- Built the source distribution and wheel. Installed the wheel into a fresh
  temporary virtual environment and ran the actual `pixelart` entry point from
  outside the checkout. Both examples passed raster render, inspect and review.
- The installed wheel also passed native `doctor`, `render`, `inspect`, `review`
  and `run-lua`, including tag inspection, a named Lua parameter and original
  source hash preservation. The packaged Lua assembly resource was present.
- Skill-copy installation and overwrite refusal passed in the test suite.
  README, documentation and example local links resolve.
- Opened the final native image, enlarged preview, contact sheet and isolated
  whale silhouette. See the [visual review](visual-review.md) for observations
  and artistic limitations; real-time playback was not reviewed.

The locally built Cocoa executable aborts with exit -6 when launched inside a
restricted process sandbox. From a normal user shell it passed `doctor` and
every native check.
Aseprite is separately installed and must be discoverable through PATH,
`ASEPRITE_BIN`, or `--aseprite`; the repository does not bundle it.

## Platform coverage

These are local macOS results. Linux and Windows native Aseprite behavior has
not been verified here. GitHub Actions defines portable tests and package checks
for Linux, macOS and Windows; this local check did not run those remote jobs.
These checks cover the documented workflow and selected edge cases, not every
possible scene or arbitrary Lua script.

## Reproduce

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), configure your Aseprite executable,
then run:

```sh
python -m unittest discover -s tests -v
# Enable ASEPRITE_NATIVE_TEST=1 in your shell to include native integration tests.
python -m build
python tools/check-wheel.py
```

`tools/check-wheel.py` always checks both raster examples. When `ASEPRITE_BIN`
is set, it additionally exercises every native CLI command outside the checkout.
The temporary installation may download Pillow.
