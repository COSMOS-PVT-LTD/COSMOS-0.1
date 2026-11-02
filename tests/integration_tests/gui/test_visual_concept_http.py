"""The artwork is served only as a display asset, outside project mutation APIs."""

from tests.integration_tests.gui.test_project_authority_http import running


def test_visual_concept_is_available_in_native_geometry_workbench(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        app.ngg_enabled = True
        with client.open(base + "/app/workbench/native-geometry") as response:
            html = response.read()
        assert b"/assets/visual-concept-data.js" in html
        assert b"/assets/visual-concept.js" in html
        for asset in ("visual-concept.js", "visual-concept-data.js"):
            with client.open(base + "/assets/" + asset) as response:
                assert response.status == 200
                assert len(response.read()) > 100
