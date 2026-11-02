# View/reproduce the task-only pressure-fed integration

No live application root was switched. The feature is in **managed Projects → Pressure-fed assessment** when the existing durable-project authority is explicitly enabled. The rocket inspector links there. A normal legacy preview does not silently migrate into managed authority.

To reopen the already-created synthetic QA environment (if its temporary folder still exists):

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
.venv-release-p12/bin/python tests/ui/r06_2b/preview.py --root /private/tmp/cosmos-r06_2b-qa.I5szyB --resume
```

Visit `http://127.0.0.1:8867/app/projects?project=80cdb6c3-9adb-4465-877f-21ef8b98840d`. Choose the Engineer profile and use the explicitly synthetic account defined in that QA helper (not company/owner credentials). Inspect final assessment `1db42afc-1cbb-59ee-af84-eb79841c2b5c`. Enter no real engine data by copying the synthetic values: its density/loss/pressure constants are software-verification fixtures, not defaults, hardware recommendations or validated properties.

For a new isolated QA copy, use `mktemp -d /tmp/cosmos-r06_2b-qa.XXXXXX` and pass the returned folder without `--resume`. Never substitute the owner `cosmos_app_data` or reset a store. No live import/root switch follows from this command. Stop only this helper with Ctrl+C.

Input flow: choose an exact saved PRESSURE_FED assumed-state design; explicitly select scope/regime/phase; enter all SI values and source/condition annotations. Zeros must be entered deliberately. New evaluation captures inputs before calculation. A received terminal failure is retained and has no numeric answer; correct data and issue a new explicit command. A lost response may be retried unchanged with the same local operation; do not change inputs under an unresolved operation. Explicit abandon keeps typed inputs and leaves server records untouched. A no-terminal input capture may be retried by its original authorized actor from retained history; exact original command/source/methods are used. Source changes require a new reconciled command, not overwriting old captures.

Read currentness and execution separately. Historical originals/CSV remain inspectable and explicitly labelled. Even balanced rows do not complete the cycle, solve feed flow or validate hardware. All old workflow cycle flags remain NOT_IMPLEMENTED.

Focused automated checks:

```sh
.venv-release-p12/bin/python -m pytest -q tests/unit_tests/infrastructure/test_managed_pressure_fed.py tests/integration_tests/gui/test_pressure_fed_projects_http.py
node --test tests/js/managed_pressure_fed.test.cjs
```

Full pytest needs the existing exact-copy/restore/compare guard around `cache/cea/test_key.json`; it intentionally mutates that test cache. Native campaigns need fresh evidence output destinations and verified pinned runtimes, not reused receipt folders or weakened hashes.
