"""
_auth.py — Authentication provider hierarchy.

Each provider supplies HTTP headers and/or query params for requests.
Credentials are always read from environment variables -- never hard-coded.

Merged from cohort_fetch.auth.__init__ and cohort_fetch.auth.providers.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


class AuthProvider(ABC):
    @abstractmethod
    def get_headers(self) -> dict[str, str]: ...

    @abstractmethod
    def get_params(self) -> dict[str, str]: ...

    @property
    @abstractmethod
    def is_configured(self) -> bool: ...


class NoAuth(AuthProvider):
    """For fully public sources that require no credentials."""

    def get_headers(self) -> dict[str, str]:
        return {}

    def get_params(self) -> dict[str, str]:
        return {}

    @property
    def is_configured(self) -> bool:
        return True


class EnvVarTokenAuth(AuthProvider):
    """
    Bearer token read from a named environment variable.
    Used for Zenodo personal access tokens.
    """

    def __init__(
        self,
        env_var: str,
        header_name: str = "Authorization",
        prefix: str = "Bearer",
    ) -> None:
        self._env_var = env_var
        self._header_name = header_name
        self._prefix = prefix

    def get_headers(self) -> dict[str, str]:
        token = os.environ.get(self._env_var, "")
        if token:
            return {self._header_name: f"{self._prefix} {token}"}
        return {}

    def get_params(self) -> dict[str, str]:
        return {}

    @property
    def is_configured(self) -> bool:
        return bool(os.environ.get(self._env_var))


class AppTokenAuth(AuthProvider):
    """
    Socrata App Token passed as a query parameter.
    Used for CDC PLACES and data.gov Socrata APIs.
    """

    def __init__(self, env_var: str = "SOCRATA_APP_TOKEN") -> None:
        self._env_var = env_var

    def get_headers(self) -> dict[str, str]:
        return {}

    def get_params(self) -> dict[str, str]:
        token = os.environ.get(self._env_var, "")
        return {"$$app_token": token} if token else {}

    @property
    def is_configured(self) -> bool:
        return bool(os.environ.get(self._env_var))


def build_auth_provider(source_config: dict) -> AuthProvider:
    """
    Factory: construct the correct AuthProvider from a sources.yml stanza.

    source_config keys:
      auth: "none" | "env_var_token" | "app_token" | "local_path"
      token_env: <env var name>     (for env_var_token)
      app_token_env: <env var name> (for app_token)
    """
    auth_type = source_config.get("auth", "none")
    if auth_type == "none":
        return NoAuth()
    if auth_type == "env_var_token":
        env_var = source_config.get("token_env", "")
        return EnvVarTokenAuth(env_var)
    if auth_type == "app_token":
        env_var = source_config.get("app_token_env", "SOCRATA_APP_TOKEN")
        return AppTokenAuth(env_var)
    if auth_type == "local_path":
        # Local-path sources (UKB, BioLINCC) use NoAuth for HTTP;
        # the path is read by the adapter directly from env.
        return NoAuth()
    raise ValueError(f"Unknown auth type: {auth_type!r}")
