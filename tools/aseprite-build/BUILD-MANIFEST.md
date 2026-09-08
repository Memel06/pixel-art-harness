# Local Aseprite build manifest

This directory builds the standalone harness's local, native Apple Silicon Aseprite CLI. Run `./tools/aseprite-build/build-macos-arm64.sh`, then `./tools/aseprite-build/run-smoke-test.sh` from the repository root.

## Pinned inputs

| Component | Value |
| --- | --- |
| Aseprite source | `https://github.com/aseprite/aseprite.git` at `56757b5fc5f00cf5833fb68d5e864ba7f91059a3` (`main`, observed 2026-09-04; reports `1.3.18.3-13-g56757b5fc-dev`) |
| Source submodules | The commits recorded by that Aseprite revision; initialized recursively by the build script |
| Skia | `m124-08a5439a6b`, `Skia-macOS-Release-arm64.zip` from the official `aseprite/skia` release |
| Skia archive SHA-256 | `22663000967fc2c3f1a78190082228474955de02ffd13a352b39a48b204dac9a` |
| Build type | `RelWithDebInfo`, native `arm64`, deployment target `macOS 11.0` |
| Build system | CMake + Ninja |

The script uses the active Command Line Tools or Xcode macOS SDK reported by `xcrun`; it does not install global packages. The verified local build used Apple clang 15.0.0, macOS SDK 14.4, CMake 4.4.2, and Ninja 1.13.2 on macOS 14.7.4.

## Locations and version

- Stable CLI path: `vendor/aseprite/build/bin/aseprite`
- App bundle: `vendor/aseprite/build/bin/Aseprite.app`
- Downloaded Skia: `vendor/aseprite/.deps/skia-m124/`
- Local logs: `tools/aseprite-build/logs/`

The root `.gitignore` excludes `vendor/`, and this directory ignores logs, isolated preferences, and temporary smoke artifacts. Do not commit or distribute the built app, the Aseprite source checkout, Skia archive, or other downloaded build outputs with this harness.

## Host execution requirement

This is a native macOS Cocoa executable. Restricted process sandboxes can abort it during Cocoa startup, even for `--version`. That failure says nothing about the build itself: run Aseprite from a normal user shell, or grant the sandbox the permissions your host documents for native applications.

## License and distribution boundary

Aseprite is not covered by this harness's MIT license. Its source checkout carries `vendor/aseprite/EULA.txt`, and bundled third-party notices are in `vendor/aseprite/docs/LICENSES.md`. The downloaded Skia package includes its own `vendor/aseprite/.deps/skia-m124/LICENSE`. Consult those source files and the upstream projects before any redistribution or publication of Aseprite, its source, its binaries, or Skia.

## Verification

`run-smoke-test.sh` sets `ASEPRITE_USER_FOLDER` to a local ignored folder. It executes Aseprite in batch mode, runs `smoke-test.lua` to create two named editable layers, saves a `.aseprite` file, exports an 8×8 PNG, reopens the source to list its layers, and checks the PNG type and dimensions.
