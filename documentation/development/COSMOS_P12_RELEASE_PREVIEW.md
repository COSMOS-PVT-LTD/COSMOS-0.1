# COSMOS P12 local release preview

This is an opt-in, source-linked **macOS arm64 research preview**, not a standalone installer or production release. No Windows/Linux/native redistribution, physical validation or signed engineering acceptance is approved. Legacy development mode is preserved and still uses known development credentials; do not expose it as production.

## Build a separate preview

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
python3 -m venv .venv-release-p12
.venv-release-p12/bin/python -m pip install -r requirements-release-macos.txt
PYTHON="$PWD/.venv-release-p12/bin/python" bash scripts/build_macos_app.sh --release-preview --output "$PWD/dist/P12-release-preview"
```

The output must not exist; the builder refuses overwrite. Existing `dist/COSMOS 0.1.app`, environments, projects and results are not replaced. The bundle checks its recorded source files before launch and needs the exact existing checkout and Python environment. Moving or editing either requires rebuilding and verification. Native dependencies are not bundled. The dependency lock preserves CEA/NumPy scientific versions while using patched image/PDF/development packages. The interpreter/native vulnerability and distribution closure still require release review.

## Launch and first login

Double-click the preview app for the native window, or use an explicit isolated root:

```sh
cosmos_p12_data="$(mktemp -d /tmp/cosmos-p12-user-preview.XXXXXX)"
"$PWD/dist/P12-release-preview/COSMOS 0.1 Release Preview.app/Contents/MacOS/cosmos-launcher" --root "$cosmos_p12_data" --port 8840 --modern --native-runtime "$PWD/docs/implementation/evidence/P08_2026-10-09/local-runtime.json"
```

The launcher creates `first-login.json` inside that root, with login ID `cosmos-admin` and a unique password, readable only by the local user (mode 0600). Open that file locally to obtain your first password; never commit, upload or paste it into evidence. The terminal prints its path, not its contents. The old shared development password is not accepted for a fresh preview. The root is private (0700). A root containing legacy authentication data without a preview record is refused; no silent password reset or data migration occurs. After changing the password, the first-login file is historical, not a password-recovery service.

Use `--headless` only for HTTP/browser diagnostics. The profile always binds `127.0.0.1`, bounds connections and bodies, rejects ambiguous framing/Host/cross-origin mutations and uses strict JSON. It does not implement enterprise identity, remote TLS, multi-tenant hosting or physical acceptance. Modern workbenches require explicit `--modern`; default flags stay off. A native preview also needs the separately qualified, hash-checked Mac-local manifest. Missing/changed native runtime bytes fail closed.

## Rollback and retention

Stop the preview with Ctrl-C, retain needed report/geometry evidence, then restart the **same preview launcher and private root without `--modern`/`--native-runtime`**. Legacy routes return, modern APIs are absent and persistent project/source/auth bytes are retained. Simulation/comparison/report history is intentionally ephemeral across restart; this is documented behavior, not durable engineering publication. Do not run a new root over the user's original data to simulate a migration test.

The existing development app can still be launched separately. It is not promoted or overwritten by the P12 builder. No destructive rollback or schema down-migration is performed. Code signing must distinguish unsigned/ad-hoc integrity tests from Developer ID identity and Apple notarization; successful local execution does not clear those release requirements.

## Company security reporting

Recommended address: `security@cosmospvtltd.com`. It is not confirmed active. Set up a monitored mailbox with the company's email provider, verify the domain/mail records, enable MFA, assign an owner and backup, and test delivery from an outside account. A website/domain alone does not activate email. Only after that should SECURITY.md and a security-reporting website page advertise the address. Provider instructions: [custom-domain email setup](https://support.google.com/a/answer/6142901); security practice: [CISA MFA guidance](https://www.cisa.gov/audiences/small-and-medium-businesses/secure-your-business/require-multifactor-authentication). No DNS, mailbox, website or paid service was changed by P12.
