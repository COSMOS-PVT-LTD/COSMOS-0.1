from tests.integration_tests.gui.test_r01_authorization_http import call, cookie

pytest_plugins = ["tests.integration_tests.gui.test_release_preview_http"]
import json

from api.authentication import UserRole


def test_visualization_authenticated_readonly_route_assets(preview):
    app, server = preview
    assert call(server, "/api/visualization/context")[0] == 401
    token = cookie(app, server, UserRole.VIEWER)
    assert call(server, "/api/visualization/context", token=token)[0] == 200
    status, _, catalog = call(server, "/api/workbenches", token=token)
    assert status == 200
    item = next(item for page in json.loads(catalog)["pages"] for item in page["items"] if item["workbench_id"] == "visualization")
    assert item["status"] == "active" and item["validation_state"] == "SOURCE_VIEW_ONLY"
    status, _, body = call(server, "/app/workbench/visualization", token=token)
    assert status == 200 and b"viz-chart" in body and b"physical or production acceptance" in body
    for path in ("/assets/vendor/echarts/echarts.min.js", "/assets/vendor/three/three.module.js", "/assets/vendor/three/OrbitControls.js"):
        status, headers, _ = call(server, path)
        assert status == 200 and headers["X-Content-Type-Options"] == "nosniff"
    assert call(server, "/assets/vendor/three/LICENSE")[0] == 404
    assert call(server, "/api/visualization/designs/missing", token=token)[0] == 400
    assert call(server, "/api/visualization/context", {}, token=token)[0] == 404
