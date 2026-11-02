"""Reuse the unchanged qualified geometry runtime in a new evidence directory."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
original = BASE.parent / 'R05_3_2026-10-18/runtime-config.json'
config = json.loads(original.read_text())
config['evidence_directory'] = str(BASE / 'native-regression')
Path(config['evidence_directory']).mkdir(exist_ok=True)
(BASE / 'runtime-config.json').write_text(json.dumps(config, indent=2)+'\n')
print('Copied runtime policy unchanged; only new test output directory differs. No old receipt resealed.')
