# Contributing

Small, focused improvements are welcome. For larger changes, open an issue
explaining the user problem and proposed scope before building a new subsystem.

## Development

Create a virtual environment as described in [SETUP.md](SETUP.md), then:

```sh
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m build
```

Portable tests do not require Aseprite. For native pipeline changes, also run the
opt-in suite with `ASEPRITE_NATIVE_TEST=1` and report your OS and Aseprite version.
For visual changes, include an actual inspected export and concrete review notes.
Tests should verify observable behavior, especially source preservation, export
agreement, scene validation and installation outside the checkout.

Keep runtime dependencies small. Avoid host-specific paths and provider SDKs in
the core. Update the schema, examples and integration documentation when changing
the scene or command contract. Preserve the distinction between technical checks
and visual acceptance.

## Issues and pull requests

Include a minimal scene or reproduction, expected/actual behavior, CLI output,
Python/Pillow/Aseprite versions and operating system. For a PR, explain the user
problem, resulting behavior and validation performed. State checks you could not
run. AI-assisted contributions are welcome and receive the same review standard;
authors remain responsible for understanding and validating submitted changes.

Contributions are provided under the repository's MIT license. Include provenance
and appropriate terms for external assets or code. Keep downloaded applications,
private references, credentials, environments and generated work out of commits.
