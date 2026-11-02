"""Versioned engineering schemas. Opening never implicitly upgrades user data."""

from __future__ import annotations

import sqlite3
from hashlib import sha256

from systems.projects.authority import SchemaMismatch

APPLICATION_ID = 0x43534D35

SCHEMA = """
CREATE TABLE store_format (id INTEGER PRIMARY KEY CHECK(id=1), format TEXT NOT NULL);
INSERT INTO store_format VALUES(1, 'cosmos-engineering-authority-v1');
CREATE TABLE projects (
 project_id TEXT PRIMARY KEY, title TEXT NOT NULL, mission TEXT NOT NULL,
 owner_user_id TEXT NOT NULL, lifecycle TEXT NOT NULL CHECK(lifecycle IN ('ACTIVE','ARCHIVED','DELETED')),
 version INTEGER NOT NULL CHECK(version > 0), content_hash TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(project_id, owner_user_id) REFERENCES project_members(project_id,user_id) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE project_members (
 project_id TEXT NOT NULL REFERENCES projects(project_id), user_id TEXT NOT NULL,
 capability TEXT NOT NULL CHECK(capability IN ('OWNER','EDITOR','VIEWER')),
 PRIMARY KEY(project_id,user_id)
);
CREATE UNIQUE INDEX one_owner ON project_members(project_id) WHERE capability='OWNER';
CREATE TABLE objects (
 project_id TEXT NOT NULL REFERENCES projects(project_id), domain TEXT NOT NULL, object_id TEXT NOT NULL,
 head_commit_id TEXT, version INTEGER NOT NULL CHECK(version >= 0), content_hash TEXT NOT NULL,
 PRIMARY KEY(project_id,domain,object_id),
 FOREIGN KEY(project_id,domain,object_id,head_commit_id)
 REFERENCES commits(project_id,domain,object_id,commit_id) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE commits (
 commit_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, domain TEXT NOT NULL, object_id TEXT NOT NULL,
 parent_commit_id TEXT, version INTEGER NOT NULL CHECK(version > 0),
 input_revision INTEGER NOT NULL CHECK(input_revision >= 0), content_hash TEXT NOT NULL,
 byte_length INTEGER NOT NULL CHECK(byte_length >= 0), schema_id TEXT NOT NULL, source_namespace TEXT NOT NULL,
 creator_user_id TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(project_id,domain,object_id,commit_id), UNIQUE(project_id,domain,object_id,version),
 FOREIGN KEY(project_id,domain,object_id) REFERENCES objects(project_id,domain,object_id),
 FOREIGN KEY(project_id,domain,object_id,parent_commit_id) REFERENCES commits(project_id,domain,object_id,commit_id)
);
CREATE TABLE project_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL REFERENCES projects(project_id),
 actor_user_id TEXT NOT NULL, action TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE operations (
 actor_user_id TEXT NOT NULL, operation_id TEXT NOT NULL, project_id TEXT NOT NULL REFERENCES projects(project_id),
 request_hash TEXT NOT NULL, result_json TEXT NOT NULL,
 PRIMARY KEY(actor_user_id,operation_id)
);
CREATE TRIGGER no_project_purge BEFORE DELETE ON projects BEGIN SELECT RAISE(ABORT,'recoverable tombstones only'); END;
CREATE TRIGGER keep_owner BEFORE DELETE ON project_members
 WHEN OLD.capability='OWNER' BEGIN SELECT RAISE(ABORT,'owner removal requires explicit recovery'); END;
CREATE TRIGGER keep_owner_role BEFORE UPDATE ON project_members
 WHEN OLD.capability='OWNER' BEGIN SELECT RAISE(ABORT,'owner transfer requires explicit recovery'); END;
"""
for _table in ("commits", "project_events", "operations", "store_format"):
    for _verb in ("UPDATE", "DELETE"):
        SCHEMA += (
            f"CREATE TRIGGER immutable_{_table}_{_verb.lower()} BEFORE {_verb} ON {_table} "
            "BEGIN SELECT RAISE(ABORT,'immutable authority record'); END;\n"
        )


SCHEMA_V1 = SCHEMA
SCHEMA += """
CREATE TABLE commit_contexts (
 commit_id TEXT PRIMARY KEY REFERENCES commits(commit_id),
 purpose TEXT NOT NULL CHECK(purpose IN ('save','create','calculation','calculation_input','activate','branch')),
 source_commit_id TEXT REFERENCES commits(commit_id), input_commit_id TEXT REFERENCES commits(commit_id),
 selected_at_commit INTEGER NOT NULL CHECK(selected_at_commit IN (0,1)), response_json TEXT
);
CREATE TRIGGER context_project_scope BEFORE INSERT ON commit_contexts
 WHEN EXISTS(SELECT 1 FROM commits c JOIN commits s ON s.commit_id=NEW.source_commit_id
             WHERE c.commit_id=NEW.commit_id AND c.project_id!=s.project_id)
 OR EXISTS(SELECT 1 FROM commits c JOIN commits i ON i.commit_id=NEW.input_commit_id
           WHERE c.commit_id=NEW.commit_id AND c.project_id!=i.project_id)
 BEGIN SELECT RAISE(ABORT,'cross-project context reference'); END;
CREATE INDEX project_event_index ON project_events(project_id,sequence);
CREATE INDEX actor_memberships ON project_members(user_id,project_id);
CREATE INDEX project_operations ON operations(project_id);
"""
for _verb in ("UPDATE", "DELETE"):
    SCHEMA += (
        f"CREATE TRIGGER immutable_commit_contexts_{_verb.lower()} BEFORE {_verb} ON commit_contexts "
        "BEGIN SELECT RAISE(ABORT,'immutable authority record'); END;\n"
    )
SCHEMA_V2 = SCHEMA
SCHEMA += """
CREATE TABLE durable_jobs (
 ordinal INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL UNIQUE,
 project_id TEXT NOT NULL REFERENCES projects(project_id), domain TEXT NOT NULL, object_id TEXT NOT NULL,
 source_commit_id TEXT NOT NULL REFERENCES commits(commit_id), creator_user_id TEXT NOT NULL,
 retry_of TEXT REFERENCES durable_jobs(job_id), created_at TEXT NOT NULL,
 FOREIGN KEY(project_id,domain,object_id) REFERENCES objects(project_id,domain,object_id)
);
CREATE TABLE durable_job_events (
 job_id TEXT NOT NULL REFERENCES durable_jobs(job_id), sequence INTEGER NOT NULL CHECK(sequence>=0),
 state TEXT NOT NULL CHECK(state IN ('QUEUED','RUNNING','CANCEL_REQUESTED','COMPLETED','FAILED','CANCELLED','INTERRUPTED')),
 content_hash TEXT NOT NULL, byte_length INTEGER NOT NULL CHECK(byte_length>=0), created_at TEXT NOT NULL,
 PRIMARY KEY(job_id,sequence)
);
CREATE TABLE durable_job_blobs (
 job_id TEXT NOT NULL REFERENCES durable_jobs(job_id), name TEXT NOT NULL, content_hash TEXT NOT NULL,
 byte_length INTEGER NOT NULL CHECK(byte_length>=0), kind TEXT NOT NULL CHECK(kind IN ('source','artifact','diagnostic')),
 PRIMARY KEY(job_id,name)
);
CREATE TABLE durable_job_selections (
 project_id TEXT NOT NULL, domain TEXT NOT NULL, object_id TEXT NOT NULL,
 admitted_job_id TEXT NOT NULL REFERENCES durable_jobs(job_id), selected_job_id TEXT REFERENCES durable_jobs(job_id),
 PRIMARY KEY(project_id,domain,object_id),
 FOREIGN KEY(project_id,domain,object_id) REFERENCES objects(project_id,domain,object_id)
);
CREATE INDEX durable_project_jobs ON durable_jobs(project_id,object_id,ordinal);
CREATE TRIGGER durable_job_scope BEFORE INSERT ON durable_jobs
 WHEN NOT EXISTS(SELECT 1 FROM commits c WHERE c.commit_id=NEW.source_commit_id AND c.project_id=NEW.project_id
 AND c.domain=NEW.domain AND c.object_id=NEW.object_id)
 OR (NEW.retry_of IS NOT NULL AND NOT EXISTS(SELECT 1 FROM durable_jobs j WHERE j.job_id=NEW.retry_of
 AND j.project_id=NEW.project_id AND j.source_commit_id=NEW.source_commit_id))
 BEGIN SELECT RAISE(ABORT,'cross-source job reference'); END;
CREATE TRIGGER durable_event_order BEFORE INSERT ON durable_job_events
 WHEN NEW.sequence!=(SELECT COUNT(*) FROM durable_job_events WHERE job_id=NEW.job_id)
 OR (NEW.sequence=0 AND NEW.state!='QUEUED')
 OR (NEW.sequence>0 AND NOT EXISTS(SELECT 1 FROM durable_job_events e WHERE e.job_id=NEW.job_id
 AND e.sequence=NEW.sequence-1 AND
 ((e.state='QUEUED' AND NEW.state IN ('RUNNING','CANCEL_REQUESTED','FAILED','INTERRUPTED'))
 OR (e.state='RUNNING' AND NEW.state IN ('CANCEL_REQUESTED','COMPLETED','FAILED','INTERRUPTED'))
 OR (e.state='CANCEL_REQUESTED' AND NEW.state IN ('CANCELLED','INTERRUPTED')))))
 BEGIN SELECT RAISE(ABORT,'invalid durable attempt transition'); END;
CREATE TRIGGER durable_blob_gate BEFORE INSERT ON durable_job_blobs
 WHEN NOT EXISTS(SELECT 1 FROM durable_job_events e WHERE e.job_id=NEW.job_id AND e.state='COMPLETED')
 BEGIN SELECT RAISE(ABORT,'only completed attempts retain exchange blobs'); END;
"""
for _table in ("durable_jobs", "durable_job_events", "durable_job_blobs"):
    for _verb in ("UPDATE", "DELETE"):
        SCHEMA += (
            f"CREATE TRIGGER immutable_{_table}_{_verb.lower()} BEFORE {_verb} ON {_table} "
            "BEGIN SELECT RAISE(ABORT,'immutable authority record'); END;\n"
        )
SCHEMA_V3 = SCHEMA
SCHEMA += """
CREATE TABLE durable_geometry_stages (
 job_id TEXT NOT NULL REFERENCES durable_jobs(job_id), sequence INTEGER NOT NULL CHECK(sequence>=0),
 native_job_id TEXT NOT NULL, state TEXT NOT NULL, stage TEXT NOT NULL,
 content_hash TEXT NOT NULL, byte_length INTEGER NOT NULL CHECK(byte_length>=0), created_at TEXT NOT NULL,
 PRIMARY KEY(job_id,sequence)
);
CREATE TRIGGER geometry_stage_order BEFORE INSERT ON durable_geometry_stages
 WHEN NEW.sequence!=(SELECT COUNT(*) FROM durable_geometry_stages WHERE job_id=NEW.job_id)
 OR EXISTS(SELECT 1 FROM durable_geometry_stages s WHERE s.job_id=NEW.job_id AND s.native_job_id!=NEW.native_job_id)
 OR NOT EXISTS(SELECT 1 FROM durable_job_events e WHERE e.job_id=NEW.job_id
 AND e.sequence=(SELECT MAX(sequence) FROM durable_job_events WHERE job_id=NEW.job_id)
 AND e.state IN ('RUNNING','CANCEL_REQUESTED'))
 BEGIN SELECT RAISE(ABORT,'invalid native stage order or terminal attempt'); END;
"""
for _verb in ("UPDATE", "DELETE"):
    SCHEMA += (
        f"CREATE TRIGGER immutable_geometry_stages_{_verb.lower()} BEFORE {_verb} ON durable_geometry_stages "
        "BEGIN SELECT RAISE(ABORT,'immutable authority record'); END;\n"
    )
SCHEMA_V4 = SCHEMA
SCHEMA += """
CREATE TABLE record_dependencies (
 commit_id TEXT NOT NULL REFERENCES commits(commit_id), relation TEXT NOT NULL,
 source_commit_id TEXT NOT NULL REFERENCES commits(commit_id), source_job_id TEXT REFERENCES durable_jobs(job_id),
 PRIMARY KEY(commit_id,relation)
);
CREATE TRIGGER dependency_scope BEFORE INSERT ON record_dependencies
 WHEN NEW.commit_id=NEW.source_commit_id
 OR NOT EXISTS(SELECT 1 FROM commits c JOIN commits s ON c.project_id=s.project_id
               WHERE c.commit_id=NEW.commit_id AND s.commit_id=NEW.source_commit_id)
 OR (NEW.source_job_id IS NOT NULL AND NOT EXISTS(
     SELECT 1 FROM durable_jobs j WHERE j.job_id=NEW.source_job_id AND j.source_commit_id=NEW.source_commit_id))
 BEGIN SELECT RAISE(ABORT,'invalid dependency scope or attempt source'); END;
CREATE TABLE durable_simulation_monitors (
 job_id TEXT NOT NULL REFERENCES durable_jobs(job_id), sequence INTEGER NOT NULL CHECK(sequence>=0),
 run_id TEXT NOT NULL, content_hash TEXT NOT NULL, byte_length INTEGER NOT NULL CHECK(byte_length>=0), created_at TEXT NOT NULL,
 PRIMARY KEY(job_id,sequence)
);
CREATE TRIGGER simulation_monitor_order BEFORE INSERT ON durable_simulation_monitors
 WHEN NEW.sequence!=(SELECT COUNT(*) FROM durable_simulation_monitors WHERE job_id=NEW.job_id)
 OR EXISTS(SELECT 1 FROM durable_simulation_monitors m WHERE m.job_id=NEW.job_id AND m.run_id!=NEW.run_id)
 OR NOT EXISTS(SELECT 1 FROM durable_jobs j JOIN durable_job_events e ON e.job_id=j.job_id
               WHERE j.job_id=NEW.job_id AND j.domain='simulation-benchmark'
               AND e.sequence=(SELECT MAX(sequence) FROM durable_job_events WHERE job_id=NEW.job_id)
               AND e.state IN ('RUNNING','CANCEL_REQUESTED'))
 BEGIN SELECT RAISE(ABORT,'invalid simulation monitor order or attempt'); END;
CREATE INDEX dependency_sources ON record_dependencies(source_commit_id);
"""
for _table in ("record_dependencies", "durable_simulation_monitors"):
    for _verb in ("UPDATE", "DELETE"):
        SCHEMA += (
            f"CREATE TRIGGER immutable_{_table}_{_verb.lower()} BEFORE {_verb} ON {_table} "
            "BEGIN SELECT RAISE(ABORT,'immutable authority record'); END;\n"
        )
SCHEMA_V5 = SCHEMA
SCHEMA += """
CREATE TABLE transfer_receipts (
 receipt_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id), kind TEXT NOT NULL,
 content_hash TEXT NOT NULL, byte_length INTEGER NOT NULL CHECK(byte_length>=0), actor_user_id TEXT NOT NULL, created_at TEXT NOT NULL
);
"""
for _verb in ("UPDATE", "DELETE"):
    SCHEMA += (
        f"CREATE TRIGGER immutable_transfer_receipts_{_verb.lower()} BEFORE {_verb} ON transfer_receipts "
        "BEGIN SELECT RAISE(ABORT,'immutable transfer receipt'); END;\n"
    )
CURRENT_VERSION = 6


def signature(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name",
    ).fetchall()
    return sha256(repr([tuple(row) for row in rows]).encode()).hexdigest()


def check_schema(connection: sqlite3.Connection) -> int:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version not in {1, 2, 3, 4, 5, CURRENT_VERSION}:
        raise SchemaMismatch(
            "Unknown engineering schema; do not downgrade/reset existing data."
        )
    if connection.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
        raise SchemaMismatch("This is not a COSMOS engineering authority database.")
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript({1: SCHEMA_V1, 2: SCHEMA_V2, 3: SCHEMA_V3, 4: SCHEMA_V4, 5: SCHEMA_V5, 6: SCHEMA}[version])
        if signature(reference) != signature(connection):
            raise SchemaMismatch(
                f"Engineering schema/immutability guards differ from version {version}."
            )
        rows = connection.execute("SELECT id,format FROM store_format").fetchall()
        if [tuple(row) for row in rows] != [(1, "cosmos-engineering-authority-v1")]:
            raise SchemaMismatch("Unknown engineering format marker.")
    finally:
        reference.close()
    return int(version)
