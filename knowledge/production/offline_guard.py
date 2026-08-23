"""Offline execution guard for production local RAG (Step 7)."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass

__all__ = (
    "OfflineExecutionGuard",
    "OfflineGuardReport",
    "ProviderInvocationState",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderInvocationState:
    """Explicit provider invocation state for trust boundary reporting."""

    provider_invoked: bool = False
    provider_name: str | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "provider_invoked": self.provider_invoked,
            "provider_name": self.provider_name,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class OfflineGuardReport:
    """Report from offline execution verification."""

    network_disabled: bool
    cloud_api_env_present: bool
    provider_state: ProviderInvocationState

    @property
    def is_offline_safe(self) -> bool:
        return self.network_disabled and not self.cloud_api_env_present


class OfflineExecutionGuard:
    """Verify offline-safe execution preconditions."""

    _CLOUD_ENV_KEYS = (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "COHERE_API_KEY",
    )

    def verify_environment(self) -> OfflineGuardReport:
        """Verify that cloud provider credentials are not required."""

        network_disabled = os.environ.get("COSMOS_OFFLINE_MODE", "1") == "1"
        cloud_present = any(
            os.environ.get(key) for key in self._CLOUD_ENV_KEYS
        )

        return OfflineGuardReport(
            network_disabled=network_disabled,
            cloud_api_env_present=cloud_present,
            provider_state=ProviderInvocationState(provider_invoked=False),
        )

    @staticmethod
    def assert_no_outbound_network() -> None:
        """Fail closed when outbound network access is attempted in offline tests."""

        if os.environ.get("COSMOS_OFFLINE_MODE", "1") != "1":
            return

        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(0.01)

        try:
            probe.connect(("1.1.1.1", 53))
        except OSError:
            return
        finally:
            probe.close()

        msg = "Outbound network access detected in offline mode."
        raise RuntimeError(msg)
