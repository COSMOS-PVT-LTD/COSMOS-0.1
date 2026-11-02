"""Copy real prior task-owned native histories, never a live owner root."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pytest

from infrastructure.persistence.application_authority import ApplicationAuthority
from infrastructure.persistence.durable_jobs import SQLiteJobRepository
from infrastructure.persistence.files import CoordinatorLease
from infrastructure.persistence.portability import backup_store, restore_store
from infrastructure.persistence.schema import CURRENT_VERSION
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Principal


@pytest.mark.parametrize('index',[0,1])
def test_actual_retained_native_schema_copy_keeps_all_original_bytes(native_config,tmp_path,index):
    config=os.environ.get('COSMOS_R05_COPY_CASES')
    if not config:
        pytest.skip('Explicit task-owned prior QA copy cases required; never autodetect owner data')
    case=json.loads(Path(config).read_text())[index]
    root=Path(case['root']).resolve()
    assert str(root).startswith('/private/tmp/cosmos-r05_') and 'preview.' in root.name
    if not (root/'engineering_state/v1/metadata.sqlite3').is_file():
        pytest.skip('Explicit prior task-owned QA source no longer exists')
    auth=sqlite3.connect('file:'+str(root/'auth/users.sqlite')+'?mode=ro',uri=True)
    try:
        account=auth.execute('SELECT user_id,role,active FROM users WHERE login_id=?',(case['login_id'],)).fetchone()
    finally:
        auth.close()
    assert account is not None
    actor=Principal(account[0],account[1],bool(account[2]))
    actor.require()
    store=root/'engineering_state/v1'
    before=sha256((store/'metadata.sqlite3').read_bytes()).hexdigest()
    with CoordinatorLease(store):
        source=SQLiteProjectRepository(store)
        project=source.get_project(actor,case['project_id'])
        source_jobs=SQLiteJobRepository(source)
        with source._transaction() as connection:
            commits=[tuple(row) for row in connection.execute('SELECT * FROM commits ORDER BY commit_id')]
        originals={row[0]:source.resolve_snapshot(actor,project.project_id,row[0]).payload for row in commits}
        ids=source_jobs.list_ids(actor,project.project_id,limit=100)
        assert ids
        jobs={key:source_jobs.get(actor,project.project_id,key) for _,key in ids}
        blobs={(key,b.name):source_jobs.blob(actor,project.project_id,key,b.name) for key,job in jobs.items() for b in job.blobs}
        backup=tmp_path/'backup'
        backup_store(source,backup)
        manifest=sha256((backup/'manifest.json').read_bytes()).hexdigest()
    application=tmp_path/'restored-application'
    (application/'engineering_state').mkdir(mode=0o700,parents=True)
    receipt=restore_store(backup,application/'engineering_state/v1',confirmed_manifest=manifest,upgrade=True)
    assert receipt['source_schema']==case['schema'] and receipt['target_schema']==CURRENT_VERSION
    with closing(ApplicationAuthority(application,enabled=False)) as reopened:
        assert reopened.repository.get_project(actor,project.project_id)==project
        with reopened.repository._transaction() as connection:
            assert [tuple(row) for row in connection.execute('SELECT * FROM commits ORDER BY commit_id')]==commits
        for key,raw in originals.items():
            assert reopened.repository.resolve_snapshot(actor,project.project_id,key).payload==raw
        for key,job in jobs.items():
            assert reopened.jobs.get(actor,project.project_id,key)==job
        for (key,name),raw in blobs.items():
            assert reopened.jobs.blob(actor,project.project_id,key,name)==raw
    assert sha256((store/'metadata.sqlite3').read_bytes()).hexdigest()==before
    destination=os.environ.get('COSMOS_R05_COPY_EVIDENCE')
    if destination:
        folder=Path(destination);folder.mkdir(parents=True,exist_ok=True)
        (folder/f'schema{case["schema"]}.json').write_text(json.dumps({'source_root':str(root),'source_schema':case['schema'],
            'target_schema':CURRENT_VERSION,'original_metadata_sha256':before,'original_unchanged':True,'exact_commits':len(commits),
            'exact_native_or_solver_attempts':len(jobs),'exact_source_export_blobs':len(blobs),'read_only_authority_reopened':True,
            'receipt':receipt,'scope':'Actual retained software QA histories; no live owner migration, new physical evidence or whole-app auth backup'},indent=2)+'\n')
