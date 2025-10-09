"""N-gram analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from .base.interface import interface as base_interface
from .stats.interface import interface as stats_interface
from .web.interface import interface as web_interface


def get_interface():
    """Return the analyzer interface for plugin discovery."""
    return {
        "base": base_interface,
        "stats": stats_interface,
        "web": web_interface,
    }


__all__ = ["get_interface", "__version__"]
