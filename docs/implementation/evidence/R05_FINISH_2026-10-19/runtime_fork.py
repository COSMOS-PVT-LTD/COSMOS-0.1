"""Fork only test output location; never regenerate native qualification."""
import json
from pathlib import Path

base = Path(__file__).resolve().parent
source = base.parent / 'R05_4_2026-10-18/runtime-config.json'
config = json.loads(source.read_text())
config['evidence_directory'] = str(base / 'native-regression')
Path(config['evidence_directory']).mkdir(exist_ok=True)
with (base / 'runtime-config.json').open('x') as stream:
    stream.write(json.dumps(config, indent=2)+'\n')
print('Native identities and existing geometry software qualification unchanged; new test output location only.')
