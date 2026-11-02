"""Disposable R03 render acceptance; no existing application storage is used."""
import sys
from pathlib import Path

from api.authentication import UserRole
from api.propulsion_workflow import run_subsystems
from gui.server import CosmosApplication, CosmosApplicationHandler
from infrastructure.release.security import PreviewHTTPServer
from tests.fixtures.propulsion_subsystems import (
    cooling_inputs,
    nozzle_inputs,
    seeded_design,
)

root = Path(sys.argv[1]).resolve()
if not root.name.startswith("cosmos-r03-preview.") or root.parent != Path("/private/tmp"):
    raise ValueError("This fixture must use its own mktemp root")
app = CosmosApplication(root, new_shell=True, simulation_enabled=True,
    comparison_enabled=True, knowledge_reports_enabled=True, ngg_enabled=False)
app.auth.register_user(login_id="presentation-qa", password="isolated-presentation-qa",
    display_name="Synthetic Presentation QA", designation="Synthetic fixture",
    employee_id="QA", team="Local UI QA", role=UserRole.ENGINEER)
for name in ("Synthetic presentation fixture A", "Synthetic presentation fixture B"):
    design = seeded_design()
    design.name = name + " — not hardware evidence"
    result = run_subsystems(design, inputs={"nozzle": nozzle_inputs(), "cooling": cooling_inputs()},
        stages=("nozzle", "cooling"), store=app.design_store)
    assert result["execution_ok"]


class Handler(CosmosApplicationHandler):
    application = app


server = PreviewHTTPServer(("127.0.0.1", 8845), Handler)
print("Disposable R03 QA on port 8845; synthetic ENGINEER fixture only.", flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
