"""Capture the actual inherited candidate before R06 edits."""
import json
import subprocess
from hashlib import sha256
from pathlib import Path

root = Path(__file__).resolve().parents[4]
base = Path(__file__).resolve().parent
previous = json.loads((base.parent / 'R05_FINISH_2026-10-19/source-final.json').read_text())['sha256']
actual = {name: sha256((root / name).read_bytes()).hexdigest() for name in previous}
changes = [name for name in previous if previous[name] != actual[name]]
value = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'entry_dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).splitlines(),
    'sha256': actual, 'differences_from_r05_final': changes, 'owner_data_not_accessed': True}
with (base / 'entry.json').open('x') as stream:
    stream.write(json.dumps(value, indent=2) + '\n')
print(f'Captured {len(actual)} source identities; differences from R05 final: {changes}')
