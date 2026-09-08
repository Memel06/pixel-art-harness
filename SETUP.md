# Setup

## Install the Python package

Download or clone this repository and open a terminal in it. Use Python 3.10+.

macOS / Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\python.exe -m pixelart --help
```

Activation is optional. If PowerShell restricts activation, use the explicit
Python path above for all `python -m pixelart` commands. On macOS/Linux the
corresponding path is `.venv/bin/python`.

## Connect Aseprite

Provide your own Lua-enabled Aseprite executable. The CLI selects exactly one
configuration, in order: `--aseprite`, then `ASEPRITE_BIN`, then `aseprite` on
PATH. An invalid configured path fails rather than falling back to another build.
Paths containing spaces work when quoted. Configuration must exist in the same
machine/container/session where the agent runs commands.

macOS, for a typical application installation:

```sh
export ASEPRITE_BIN="/Applications/Aseprite.app/Contents/MacOS/aseprite"
```

Linux, substituting your installation path:

```sh
export ASEPRITE_BIN="/opt/aseprite/aseprite"
```

Windows PowerShell, substituting your installation path:

```powershell
$env:ASEPRITE_BIN = "C:\Program Files\Aseprite\aseprite.exe"
```

These are examples, not locations the harness assumes. Steam and custom installs
can be elsewhere. A `.app` directory is not the executable inside it.

```sh
python -m pixelart doctor
python -c "from pathlib import Path; Path('output').mkdir(exist_ok=True)"
python -m pixelart render examples/moonlit-courier.json --out output/first-render
```

`doctor` checks executable resolution, `--version` startup and a Lua probe; its
`production_ready` field means only that those checks passed. The example render
is the end-to-end check for native import and export compatibility.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Command not found | Use the virtual environment's Python with `-m pixelart`. |
| Doctor cannot resolve Aseprite | Point at the executable, check spelling and permissions. |
| Startup fails inside an agent sandbox | Run in a normal terminal or use the host's supported execution permissions. |
| Linux reports a display/startup error | Check the requirements of your Aseprite build; batch mode does not guarantee a display-free build. |
| Lua/import fails | Read the CLI error and verify that your Aseprite build supports Lua scripting. |
| Output already exists | Choose a new revision directory. Create its parent first. |
| Agent cannot view images | Technical generation can continue; visual acceptance remains incomplete. |

## Optional source build

`tools/aseprite-build/` retains an optional, pinned Apple Silicon build recipe
and its historical manifest. It is not required for installation and is not a
cross-platform build system. To use that build, explicitly set `ASEPRITE_BIN`
to the resulting executable. Source downloads, dependencies and build outputs
stay in ignored `vendor/`. Consult upstream build instructions for other systems.

## Verify an installation

```sh
python -m unittest discover -s tests -v
```

Native tests are opt-in. Set `ASEPRITE_NATIVE_TEST=1` in your shell before running
the same command (`export ASEPRITE_NATIVE_TEST=1` in POSIX shells;
`$env:ASEPRITE_NATIVE_TEST = "1"` in PowerShell). See [validation](docs/validation.md)
for the distinction between portable and native checks.
