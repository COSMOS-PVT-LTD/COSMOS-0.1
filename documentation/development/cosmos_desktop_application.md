# COSMOS 0.1 Desktop Application

Local installable engineering platform — **native desktop window** (like Rocket Propulsion Lab / SolidWorks), not a browser tab.

## Quick start (native application)

```bash
cd /path/to/COSMOS_0.1
./scripts/run_cosmos_desktop.sh
```

This installs `pywebview` if needed and opens **COSMOS 0.1 in its own application window** (macOS WebKit).

### One-time setup

```bash
pip install -r requirements-desktop.txt
python main.py
```

### macOS `.app` bundle (double-click in Finder)

```bash
./scripts/build_macos_app.sh
open "dist/COSMOS 0.1.app"
```

Drag `COSMOS 0.1.app` to **Applications** to install like RPL.

> **Do not use Chrome for normal use.** Browser mode is developer-only: `python main.py --browser`

### Bootstrap administrator

| Field | Value |
|-------|-------|
| Login ID | `cosmos-admin` |
| Password | `COSMOS-Dev-2026!` |

Credentials are stored locally under `cosmos_app_data/auth/users.sqlite` on first launch.

## Application flow

1. **Login page** — company-issued login ID and password (`/`).
2. **Workbench hub** — paginated engineering modules (`/app/workbenches`).
3. **Module workbenches** — Rocket Engine, Turbopumps, Structures, etc. (`/app/workbench/<id>`).
4. **Knowledge Workspace** — governed intake, review, and chat (`/app/workbench/knowledge`).
5. **Audit trail** — company action log for reviewers/approvers/admins (`/app/audit`).
6. **User administration** — register employees and roles (`/app/admin`, ADMIN only).

## Branding

- The COSMOS logo (`gui/assets/cosmos_logo.png`) is used as a **background watermark** on every shell page via `gui/static/cosmos.css`.
- Generated text exports can include a footer watermark through `infrastructure/watermark.py`.

## Data layout (local)

```
cosmos_app_data/
  auth/          # users.sqlite, session.secret
  audit/         # append-only app_audit.sqlite
  workspace_data/ # Knowledge Workspace persistence
```

## Registering company users

Administrators can register users from **Admin → Register Company User** or via API:

```bash
curl -X POST http://127.0.0.1:8780/api/admin/users \
  -H "Content-Type: application/json" \
  -b "cosmos_session=<token>" \
  -d '{
    "login_id": "engineer.one",
    "password": "Change-Me-2026!",
    "display_name": "Engineer One",
    "designation": "Propulsion Engineer",
    "employee_id": "EMP-101",
    "team": "Rocket Engine",
    "role": "ENGINEER"
  }'
```

Every login, navigation, knowledge API call, and admin action is recorded in `app_audit.sqlite`.

## Optional native window

```bash
pip install pywebview
python main.py
```

Force browser mode:

```bash
python main.py --browser
```

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | `cosmos_app_data` | Local application data directory |
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8780` | HTTP port |
| `--browser` | off | Use browser instead of pywebview |
| `--no-open` | off | Do not auto-open UI |

## Architecture notes

- **Desktop shell:** `gui/server.py`, `gui/application.py`, `main.py`
- **Authentication:** `api/authentication.py` (PBKDF2 passwords, HTTP-only session cookie)
- **Audit:** `infrastructure/security/audit.py` (append-only SQLite)
- **Workbenches:** `gui/workbenches/registry.py`
- **Knowledge backend:** existing `knowledge/workspace/` mounted behind authenticated `/api/*` routes

`PRODUCTION-READY = NO` — qualified for development; packaging/installer signing is a follow-on step.

## Workbench roadmap

Active today:

- **Rocket Engine** — module shell (Engine Design, Nozzle, Injectors, …)
- **Knowledge Workspace** — full intake / review / chat backend

Planned workbenches (registered, UI placeholders): Rocket Staging, Manufacturing, Simulation, Visualization, Turbopumps, P&ID, Structures, Documentation, Code Comparison, PLM.

Separate workbenches will be added as solvers and CAD integrations are wired through governed backend APIs.
