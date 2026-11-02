"""Authorized immutable component cooling-geometry inspection; GET only."""

import json
from dataclasses import asdict
from hashlib import sha256

from systems.geometry.component_authority import DOMAIN, from_source
from systems.geometry.component_cooling import geometry_handoff
from systems.projects.authority import InvalidRecord, RecordNotFound


def handle(components, actor, method, project, parts, query, body):
    if method != "GET" or len(parts) != 1:
        raise RecordNotFound("Cooling geometry handoff is read-only for one exact saved component model")
    if body or set(query) != {"commit"} or len(query["commit"]) != 1 or not query["commit"][0]:
        raise InvalidRecord("An exact saved model commit is required; unknown/duplicate queries and posted overrides are forbidden")
    repo = components.repository
    source = repo.get_snapshot(actor, project, domain=DOMAIN, object_id=parts[0], commit_id=query["commit"][0])
    value = json.loads(source.payload)
    report = geometry_handoff(from_source(source))
    report.update(ok=True, persisted=False,
                  authority={"project_id": project, "object_id": source.object_id,
                             "commit_id": source.commit_id, "head": asdict(source.head)},
                  baseline_commit_id=value["baseline_commit_id"],
                  baseline_sha256=sha256(value["baseline_canonical_json"].encode()).hexdigest(),
                  upstream_current=components.models.current(actor, source),
                  source_snapshot_sha256=sha256(value["snapshot_json"].encode()).hexdigest(),
                  source_graph_sha256=sha256(value["graph_json"].encode()).hexdigest())
    return report
