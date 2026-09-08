# Connect a model or agent harness

Pixel Art Harness is a local CLI, not an agent runtime. It does not select a model,
manage conversations or call an API. Use any host that can expose these capabilities:

| Capability | Purpose |
| --- | --- |
| Read/write files | Read the schema and references; author scene JSON or Lua. |
| Execute a process | Run the installed `pixelart` command and inspect its exit status. |
| View images | Send the actual exported PNGs to a vision model or human reviewer. |

A text-only model can author scenes, but needs a human or separate vision model
for visual acceptance. A browser-only chatbot needs a local execution bridge;
pasting the skill into a chat does not install Aseprite or add tools.

## Minimal integration

1. Install the package and configure Aseprite in the host's execution environment
   using [SETUP.md](../SETUP.md).
2. Give the model [the schema](../examples/scene.schema.json), the included example,
   and the instruction below. Make `pixelart --help` available through its command tool.
3. Let the model write a scene, run the CLI and inspect exported images. Feed
   tool errors back into the conversation so it can correct the input.
4. Retain the brief, source scene, revision outputs and visual findings together.

Suggested instruction (adapt dimensions, style and review budget to the task):

```text
Use Pixel Art Harness to create editable pixel art with Aseprite.
Establish dimensions, palette, layers, timing and intended use from the brief.
Read the scene schema before authoring JSON. Use Lua for edits beyond the DSL.
Run pixelart doctor, then render into a fresh output directory.
Open frames at native size and review/contact.png at integer enlargement.
Describe specific visible defects, revise the source and reopen affected images.
Keep technical QA and visual acceptance separate. If image viewing is unavailable,
say so. Deliver source.aseprite, sheet.png, metadata.json and a useful preview,
with a short account of the review and remaining limitations.
```

Example user request:

> Create a 32×32 brass lantern with a four-frame flame, a transparent background
> and separate metal/flame layers. Review readability at 1× and refine the flame.

## Tool execution contract

All commands emit JSON on success and human-readable errors on stderr with exit
code 2 on expected failure. Argument errors also use code 2. `doctor` emits a JSON
report even when it returns 2. Unexpected internal errors can return other nonzero
codes, so treat **any nonzero exit as failure**. Do not parse stdout after a failure
as a completed artifact. Global `--aseprite` belongs before the subcommand.

```sh
pixelart doctor
pixelart render scene.json --out output/v1
pixelart inspect output/v1/source.aseprite
pixelart review output/v1/source.aseprite --out output/review-v1
pixelart run-lua output/v1/source.aseprite edit.lua --out output/v2 --param amount=1
```

The output parent must exist; the output directory itself must not. `run-lua`
produces an edited source and inspection report; run `review` afterwards for
visual artifacts. Lua receives repeated `--param key=value` values through
`app.params`. Scripts have the application's filesystem capabilities; the staged
copy protects normal saves, but this command is not a Lua security sandbox.

A Python host can invoke the CLI without shell interpolation:

```python
import json
import subprocess
import sys
from pathlib import Path

Path("output").mkdir(exist_ok=True)
result = subprocess.run(
    [sys.executable, "-m", "pixelart", "render", "scene.json",
     "--out", "output/v1"],
    capture_output=True, text=True, timeout=300,
)
if result.returncode:
    raise RuntimeError(result.stderr or result.stdout)
metadata = json.loads(result.stdout)
# Now pass output/v1/frames/*.png and output/v1/review/contact.png
# to your host's image tool. Reading metadata is not visual inspection.
```

Use an interpreter containing the installed package. The CLI inherits
`ASEPRITE_BIN` from the process environment. No provider credentials belong in a
scene, skill or this repository. The external host controls model calls and cost.

## Optional agent skill

The included skill is an instruction adapter for hosts that discover `SKILL.md`
folders. Install from a complete checkout:

```sh
python tools/install-skill.py --skills-dir path/to/your/agent/skills
```

Without `--skills-dir`, the installer uses `$CODEX_HOME/skills`, or
`~/.codex/skills` when unset. This is a convenience destination, not a runtime
dependency on Codex. Consult your host for its discovery location and refresh
procedure. The skill name remains `aseprite-pixelart`.

The installer copies instructions, art-direction guidance, schema and example.
It requires no symlink privileges and refuses to overwrite an existing skill.
For updates, explicitly remove the old registration and rerun the installer.
The installed copy can survive relocating the checkout; install the CLI normally
with `pip install .` rather than an editable install if you plan to remove it.

For hosts without skills, use the prompt above or load `SKILL.md` as task
instructions, and provide the schema and example separately. There is no required
MCP server or proprietary tool naming convention.
