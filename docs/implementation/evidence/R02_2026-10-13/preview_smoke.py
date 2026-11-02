"""Disposable localhost UI fixture; never points at existing application data."""
import sys
from pathlib import Path

from api.authentication import UserRole
from api.propulsion_workflow import run_subsystems
from gui.server import CosmosApplication, CosmosApplicationHandler
from infrastructure.release.security import PreviewHTTPServer
from knowledge.workspace.access import WorkspaceRole
from tests.fixtures.propulsion_subsystems import cooling_inputs, nozzle_inputs, seeded_design

root = Path(sys.argv[1]).resolve()
if not root.name.startswith("cosmos-r02-preview.") or root.parent != Path("/private/tmp"):
    raise ValueError("This fixture must use its own mktemp root")
app = CosmosApplication(root)
app.auth.register_user(login_id="visualization-qa", password="isolated-visualization-qa", display_name="Visualization QA",
    designation="Synthetic fixture", employee_id="QA", team="Local UI QA", role=UserRole.VIEWER)
design = seeded_design()
design.name = "Synthetic scientific visualization QA — not hardware evidence"
result = run_subsystems(design, inputs={"nozzle": nozzle_inputs(), "cooling": cooling_inputs()},
    stages=("nozzle", "cooling"), store=app.design_store)
assert result["execution_ok"]
with app.knowledge_workspace().as_principal(WorkspaceRole.ADMIN, "synthetic-ui-fixture"):
    app.knowledge_workspace().ingest(b"# Synthetic graph inspection\nThis is UI QA, not experimental validation.\n\n## Cooling\nRegenerative cooling transfers heat to the coolant.", filename="synthetic-ui-qa.md")


class Handler(CosmosApplicationHandler):
    application = app


server = PreviewHTTPServer(("127.0.0.1", 8844), Handler)
print("Disposable QA preview on port 8844; synthetic VIEWER account only.", flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
