#!/usr/bin/env python3
"""Exercise an installed wheel outside the checkout; set ASEPRITE_BIN for native checks."""
import hashlib
import json
import os
import subprocess
import tempfile
import venv
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheels = list((root / 'dist').glob('*.whl'))
if len(wheels) != 1:
    raise SystemExit('Expected exactly one wheel in dist/; clean old builds first.')
with zipfile.ZipFile(wheels[0]) as archive:
    assert 'pixelart/lua/import_layers.lua' in archive.namelist()
with tempfile.TemporaryDirectory(prefix='pixel-art-harness-wheel-') as temporary:
    work = Path(temporary)
    venv.create(work / 'venv', with_pip=True)
    bin_dir = work / 'venv' / ('Scripts' if os.name == 'nt' else 'bin')
    python = bin_dir / ('python.exe' if os.name == 'nt' else 'python')
    cli = bin_dir / ('pixelart.exe' if os.name == 'nt' else 'pixelart')
    subprocess.run([str(python), '-m', 'pip', 'install', str(wheels[0])], check=True, cwd=work)

    def run(*args):
        result = subprocess.run([str(cli), *map(str, args)], check=True, cwd=work, capture_output=True, text=True)
        return json.loads(result.stdout)

    for name in ('moonlit-courier', 'skywhale'):
        output = work / name
        result = run('render', root / 'examples' / f'{name}.json', '--out', output, '--raster-only')
        assert result['frame_count'] == 4
        assert result['raster_only'] and not result['production_ready']
        assert run('inspect', output / 'preview.png')['kind'] == 'raster'
        run('review', output / 'preview.png', '--out', work / f'{name}-review')

    if os.environ.get('ASEPRITE_BIN'):
        assert run('doctor')['production_ready']
        output = work / 'native'
        run('render', root / 'examples/skywhale.json', '--out', output)
        qa = json.loads((output / 'qa.json').read_text())['technical']
        assert qa['native_roundtrip']['pixel_match']
        source = output / 'source.aseprite'
        inspected = run('inspect', source)
        assert inspected['technical']['frame_count'] == 4
        assert 'lantern-drift' in inspected['aseprite_listing']
        run('review', source, '--out', work / 'native-review')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        script = work / 'edit.lua'
        script.write_text('app.activeSprite.layers[1].name = app.params.name\napp.command.SaveFile()\n')
        run('run-lua', source, script, '--out', work / 'edited', '--param', 'name=edited-sky')
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        assert 'edited-sky' in run('inspect', work / 'edited/source.aseprite')['aseprite_listing']
        print('Native installed CLI: doctor, render, inspect, review, run-lua and source preservation passed.')
print('Installed wheel: both examples rendered and reviewed outside checkout.')
