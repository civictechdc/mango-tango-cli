"""Time coordination analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from .interface import interface


def get_interface():
    """Return the analyzer interface for plugin discovery."""
    return interface


__all__ = ["get_interface", "__version__"]
