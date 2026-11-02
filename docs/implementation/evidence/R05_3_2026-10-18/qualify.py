"""Issue a new local software-only receipt from completed current native tests."""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for name, expected in (('native-tests.xml', 62), ('native-final-tests.xml', 6)):
    suites = ET.parse(BASE / name).getroot().findall('testsuite')
    assert sum(int(item.attrib['tests']) for item in suites) == expected
    assert all(int(item.attrib.get(key, 0)) == 0 for item in suites for key in ('failures', 'errors', 'skipped'))
initial = json.loads((BASE / 'runtime-initial-config.json').read_text())
config = json.loads((BASE / 'runtime-config.json').read_text())
changed = [name for name, value in initial['sha256'].items() if config['sha256'][name] != value]
assert changed == [str(ROOT / 'systems/geometry/authority.py')], changed
for name, value in config['sha256'].items():
    assert digest(Path(name)) == value, name
decision = {'gate': 'R05_3_RESTORED_NATIVE_SOFTWARE_FIXTURES', 'software_g5_pass': True,
    'p08_may_begin': True, 'legacy_p08_key_is_runtime_policy_not_phase_approval': True,
    'native_tests_passed': 62, 'final_coordinator_native_tests_passed': 6,
    'native_test_log_sha256': digest(BASE / 'native-tests.log'),
    'final_coordinator_log_sha256': digest(BASE / 'native-final-tests.log'),
    'qa_tolerances_relaxed': False, 'historical_g5_modified': False,
    'engineering_publication_approved': False, 'production_native_distribution_approved': False,
    'physical_validation_claimed': False,
    'candidate_change_after_initial_run': changed}
receipt = BASE / 'native-software-decision.json'
receipt.write_text(json.dumps(decision, indent=2) + '\n')
config['g5_receipt'] = str(receipt)
config['g5_receipt_sha256'] = digest(receipt)
(BASE / 'runtime-config.json').write_text(json.dumps(config, indent=2) + '\n')
print('New scoped software receipt issued; no historical gate changed and no engineering publication approved.')
