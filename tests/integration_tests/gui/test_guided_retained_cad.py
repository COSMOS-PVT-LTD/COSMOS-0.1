"""A small native pipe verifies saved-CAD discovery, not a new engine build."""

from uuid import uuid4

from tests.integration_tests.gui.test_component_projects_http import capture
from tests.integration_tests.gui.test_engine_nozzle_projects_http import wait
from tests.integration_tests.gui.test_pico_components_http import compose
from tests.integration_tests.gui.test_project_authority_http import request, running
from tests.unit_tests.systems_layer.test_pico_components import qa
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def test_guided_cad_listing_matches_exact_physics_without_running_another_job(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        compose(app)
        project, source, root, _, saved = capture(app, base, client, "pipe.circular")
        uri = root + "/picogk-component-builds"
        start = request(
            client,
            base,
            uri,
            {
                "model_commit_id": saved["authority"]["commit_id"],
                "expected_model": saved["authority"]["head"],
                "qa_specification": qa(),
                "output_formats": ["stl"],
                "operation_id": str(uuid4()),
            },
        )
        path = uri + "/" + start["object_id"] + "/jobs/" + start["job_id"]
        job = wait(client, base, path)
        assert job["state"] == "COMPLETED", job
        selection = request(
            client, base, root + "/guided-engine/retained-cad/" + source.commit_id
        )
        assert len(selection["candidates"]) == 1
        candidate = selection["candidates"][0]
        assert candidate["matches_selected_physics"]
        assert candidate["job_id"] == job["job_id"] and candidate["backend"] == "PicoGK"
        assert candidate["physics_commit_id"] == source.commit_id
        context = request(client, base, candidate["context_url"])
        assert context["model_commit_id"] == saved["authority"]["commit_id"]
        assert (
            len(
                request(client, base, root + "/guided-engine/retained-cad")[
                    "candidates"
                ]
            )
            == 1
        )
        # Discovery and display did not enqueue/retry any native construction.
        assert (
            len(
                request(client, base, uri + "/" + start["object_id"] + "/jobs")[
                    "attempts"
                ]
            )
            == 1
        )
        assert project["project_id"] in candidate["preview_url"]
