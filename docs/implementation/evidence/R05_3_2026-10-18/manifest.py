"""Generate a new scoped runtime inventory, never an old G5 reseal/decision."""
import hashlib
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NATIVE = Path('/private/tmp/cosmos-r05_3-native.IcKKdc')
EVIDENCE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run-label', default='native')
args = parser.parse_args()
assert args.run_label in {'native', 'native-final'}

python = str(ROOT / '.venv-release-p12/bin/python')
dotnet = str(NATIVE / 'dotnet9/dotnet')
environment = {'PYTHONPATH': f'{ROOT}:{NATIVE / "cad-tools"}', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'}
dotnet_env = {'DOTNET_ROOT': str(NATIVE / 'dotnet9'), 'DOTNET_CLI_TELEMETRY_OPTOUT': '1',
              'DOTNET_CLI_HOME': str(NATIVE / 'dotnet-home')}
config = {'qualification': 'local-software-fixtures-only', 'production_enabled': False,
          'evidence_directory': str(EVIDENCE / args.run_label),
          'occt': {'argv': [python, str(ROOT / 'plugins/geometry/workers/occt_worker.py')], 'environment': environment},
          'step_reader': {'argv': [python, str(ROOT / 'plugins/geometry/workers/step_reader.py')], 'environment': environment},
          'preview_reader': {'argv': [python, str(ROOT / 'plugins/geometry/workers/preview_reader.py')], 'environment': environment},
          'picogk': {'argv': [dotnet, str(NATIVE / 'pico-worker/PicoWorker.dll')], 'environment': dotnet_env},
          'wire_probe': {'argv': [dotnet, str(NATIVE / 'wire-worker/WireProbe.dll')], 'environment': dotnet_env}}
paths = [ROOT / name for name in (
    'plugins/geometry/workers/occt_worker.py', 'plugins/geometry/workers/step_reader.py',
    'plugins/geometry/workers/preview_reader.py', 'plugins/geometry/workers/Program.cs',
    'plugins/geometry/workers/PicoWorker.csproj', 'plugins/geometry/workers/probes/Program.cs',
    'plugins/geometry/workers/patches/picogk-vdb-disposal.patch',
    'systems/geometry/workbench.py', 'systems/geometry/service.py', 'systems/geometry/authority.py',
    'systems/geometry/qa.py', 'systems/geometry/step_qa.py', 'api/ngg_workbench.py')]
paths += [NATIVE / 'cad-tools/gmsh.py', NATIVE / 'cad-tools/OCP/__init__.py',
          NATIVE / 'PicoGK/IO/OpenVdbFile.cs', NATIVE / 'dotnet9/dotnet']
for folder in ('pico-worker', 'wire-worker', 'native-deps/lib'):
    paths += [path for path in (NATIVE / folder).iterdir() if path.is_file() and not path.is_symlink()]
paths += [NATIVE / 'cad-tools/libgmsh.4.15.dylib']
# The direct OCP worker does not import CadQuery/VTK; do not hash unrelated VTK modules.
paths += [path for path in (NATIVE / 'cad-tools/OCP').rglob('*')
          if path.is_file() and path.suffix in {'.so', '.dylib'} and not path.is_symlink()]
config['sha256'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(paths))}
assert 4 <= len(config['sha256']) <= 256
(EVIDENCE / args.run_label).mkdir(exist_ok=True)
(EVIDENCE / 'runtime-config.json').write_text(json.dumps(config, indent=2) + '\n')
print(f"Recorded {len(config['sha256'])} runtime/source hashes; no qualification decision added.")
