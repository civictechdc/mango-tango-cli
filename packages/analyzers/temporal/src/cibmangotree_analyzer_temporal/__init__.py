"""Temporal analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from .base import temporal
from .web import temporal_web


def get_interface():
    """Return the analyzer declarations for plugin discovery."""
    return {
        "base": temporal,
        "web": temporal_web,
    }


__all__ = ["get_interface", "__version__"]
