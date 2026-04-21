"""
_auth_init.py — Re-exports from _auth for backwards compatibility.

Merged into medrisk.fetch._auth.
"""

from medrisk.fetch._auth import (
    AppTokenAuth,
    AuthProvider,
    EnvVarTokenAuth,
    NoAuth,
    build_auth_provider,
)

__all__ = [
    "AuthProvider",
    "NoAuth",
    "EnvVarTokenAuth",
    "AppTokenAuth",
    "build_auth_provider",
]
