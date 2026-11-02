"""Check actual native Save output against the retained source, not a mock."""
from __future__ import annotations

import argparse
import base64
import io
import json
import sqlite3
import sys
import zipfile
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))

from infrastructure.persistence.legacy_import import original_file
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Principal
from systems.projects.evidence_authority import (
    LEDGER,
    LEDGER_ID,
    REPORT,
    decode,
    unpack_session,
)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--report',required=True)
    parser.add_argument('--observed-wrapper-sha',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    if not str(root).startswith('/private/tmp/cosmos-r05-finish-qa.'):
        raise SystemExit('Only the explicitly task-owned synthetic QA root is permitted.')
    connection=sqlite3.connect('file:'+str(root/'auth/users.sqlite')+'?mode=ro',uri=True)
    try:
        row=connection.execute("SELECT user_id,role,active FROM users WHERE login_id='r05-finish-qa'").fetchone()
    finally:
        connection.close()
    actor=Principal(row[0],row[1],bool(row[2]))
    actor.require()
    state=json.loads((root/'QA_STATE.json').read_text())
    repo=SQLiteProjectRepository(root/'engineering_state/v1')
    source=repo.get_snapshot(actor,state['project_id'],domain=REPORT,object_id=args.report)
    assert source.head.content_hash==args.observed_wrapper_sha
    value=decode(source,REPORT)
    report=value['canonical_json'].encode()
    assert sha256(report).hexdigest()==value['report_id']
    saved=original_file(root/'R05-native-retained-report.zip')
    expected=value['files']['package.zip']
    assert saved==base64.b64decode(expected['base64'],validate=True)
    assert sha256(saved).hexdigest()==expected['sha256']
    with zipfile.ZipFile(io.BytesIO(saved)) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        assert archive.read('report.json')==report
        for name,digest in manifest['files'].items():
            assert sha256(archive.read(name)).hexdigest()==digest
    ledger=repo.get_snapshot(actor,state['project_id'],domain=LEDGER,object_id=LEDGER_ID)
    session=unpack_session(decode(ledger,LEDGER))
    assessment=json.loads(json.loads(report)['comparison_canonical_json'])
    policy_order=session.policies[assessment['criteria_sha256']][1]
    exposure_order=session.first_seen[assessment['reference']['provenance']['source_sha256']]
    assert policy_order<exposure_order
    assert len(value['review_intents'])==1 and not value['review_intents'][0]['independent_acceptance']
    result={'scope':'Actual native software QA Save/restart only; not genuine human/physical validation','project_id':state['project_id'],
        'report_object_id':args.report,'saved_version':source.head.version,'commit_id':source.commit_id,'wrapper_sha256':source.head.content_hash,
        'wrapper_matches_before_restart_and_observed_native_view':True,'native_saved_package_bytes':len(saved),
        'native_saved_package_sha256':sha256(saved).hexdigest(),'exact_retained_package_bytes_match':True,'zip_members_hash_checked':True,
        'original_report_id':value['report_id'],'criteria_order':policy_order,'reference_first_exposure_order':exposure_order,
        'review_intent_retained_not_a_signature':True,'production_handoff':False,'physical_validation':False}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Native retained package: exact bytes/hash PASS; restart identity/order/review intent PASS.')


if __name__=='__main__':
    main()
