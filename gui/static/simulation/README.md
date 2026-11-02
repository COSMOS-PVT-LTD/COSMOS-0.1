# P09 local simulation preview

Default off. Enable `COSMOS_NEW_SHELL=1`, `COSMOS_NGG=1`, `COSMOS_NEW_SIM_UI=1` and the existing explicit qualified `COSMOS_NGG_RUNTIME_CONFIG`. No dependency auto-install or new native runtime version. Only authenticated IPv4 loopback is supported.

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
cosmos_p09_preview="$(mktemp -d /tmp/cosmos-p09-preview.XXXXXX)"
COSMOS_NEW_SHELL=1 COSMOS_NGG=1 COSMOS_NEW_SIM_UI=1 \
COSMOS_NGG_RUNTIME_CONFIG="$PWD/docs/implementation/evidence/P08_2026-10-09/local-runtime.json" \
.venv-remediation/bin/python -m gui --root "$cosmos_p09_preview" --port 8815 --browser
```

Use a separate preview data root. Sign in with local bootstrap Administrator profile, `cosmos-admin` / `COSMOS-Dev-2026!`. Build **Sphere / OCCT** in `/app/workbench/native-geometry`. Wait for independent QA acceptance. Open `/app/workbench/simulation`, select **Use current accepted sphere**, then **Run exact study**. Engineer/Admin may modify or run; other roles are read-only, not publication authorities.

Change maximum iterations to 1, explicitly save, and run to see genuine nonconvergence. Save creates an immutable new study. Unsaved edits block Run; Discard restores saved settings. Undo/redo activate existing actor-owned immutable studies. History inspection does not replace active study. Reload retains server-session history. Server restart clears ephemeral studies/runs. This does not read or mutate engineering DesignStore projects.

The model is a declared synthetic steady conduction reference. Mesh is 1D spherical symmetry reduction, not the P08 display triangulation, general 3D mesher or engine model. Exterior named selection is a fixture-specific semantic shell, not persistent OCCT face-ID remapping. Stale geometry blocks new runs and marks existing records stale without altering original data. Cancellation/failure produce no accepted result dataset. Reimport/source/hash checks and result checksum failures remain explicit refusals.

Separate execution, termination, numerical convergence, conservation, scoped positive-temperature checks and analytic software solution verification are displayed. Experimental validation is not performed; engineering review is pending; production simulation handoff is always blocked. An API error provides code, cause and recovery. No live hardware or manufacturing approval is implied.

The shared shell provides resizable/collapsible panels. **Focus simulation workspace** hides shell docks for inspection and automatically focuses at narrow viewport widths; this is presentation only. Theme/font/layout preferences are separate from studies. All science plots label quantity/unit, residual definition/scale, and temperature profile legend range/unit/clipping/color map. Histories are bounded samples; full dataset retains exact scientific snapshots and source hashes. Profile is not a 3D field map.

Rollback: unset `COSMOS_NEW_SIM_UI` or set it to `0`. The legacy Simulation placeholder and planned catalog entry return; `/api/simulation/*` is absent. No project migration or dependency change is needed. Stop the preview with Ctrl+C. Qualified native manifests use local temporary runtimes; missing/hash-mismatched binaries fail closed and must be requalified, not bypassed.

Evidence and limits: `docs/implementation/evidence/P09_2026-10-10/`.
