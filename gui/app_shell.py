"""P04 presentation-only rollout contract; no scientific configuration or storage."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

SHELL_ASSETS = frozenset({"model.js", "adapter.js", "shell.js", "styles.css"})
DESIGN_SYSTEM_ASSETS = frozenset({"tokens.css", "components.css", "components.js"})
ROCKET_WORKBENCH_ASSETS = frozenset({"model.js", "view.js", "styles.css"})


@dataclass(frozen=True, slots=True)
class ShellFlag:
    enabled: bool
    diagnostic: str | None = None


def shell_flag(value: str | None) -> ShellFlag:
    """Strict defaults-off evaluation. Malformed values never activate a UI/backend."""
    if value is None or value.strip().lower() in {"", "0", "false"}:
        return ShellFlag(False)
    if value.strip().lower() in {"1", "true"}:
        return ShellFlag(True)
    return ShellFlag(False, "INVALID_SHELL_FLAG")


def use_shell(flag: ShellFlag, request_path: str) -> bool:
    query = parse_qs(urlparse(request_path).query, keep_blank_values=True)
    # Conflicting, empty and unknown overrides fail closed to the legacy view.
    override = query.get("shell")
    return flag.enabled and (override is None or override == ["modern"])


def inject_shell(html: bytes, *, enabled: bool) -> bytes:
    """Flag off returns the exact original bytes; only opt-in assets are injected."""
    if not enabled:
        return html
    assets = b"""<meta name="cosmos-shell" content="p04-v1">
<link rel="stylesheet" href="/assets/design-system/tokens.css">
<link rel="stylesheet" href="/assets/design-system/components.css">
<link rel="stylesheet" href="/assets/app-shell/styles.css">
<script src="/assets/cosmos-api.js"></script>
<script src="/assets/design-system/components.js"></script>
<script src="/assets/app-shell/model.js"></script>
<script src="/assets/app-shell/adapter.js"></script>
<script src="/assets/app-shell/shell.js"></script>
"""
    # Route/body specific presentation only; original HTML is byte-identical off.
    if b'propulsion-workbench' in html:
        assets += b"""<link rel="stylesheet" href="/assets/rocket-workbench/styles.css">
<script src="/assets/rocket-workbench/model.js"></script>
<script src="/assets/rocket-workbench/view.js"></script>
"""
    return html.replace(b"</head>", assets + b"</head>", 1)
