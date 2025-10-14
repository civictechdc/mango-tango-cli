"""Hashtag analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from .base import hashtags
from .web import hashtags_web


def get_interface():
    """Return the analyzer declarations for plugin discovery."""
    return {
        "base": hashtags,
        "web": hashtags_web,
    }


__all__ = ["get_interface", "__version__"]
