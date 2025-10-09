"""Example analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from .base.interface import interface as base_interface
from .report.interface import interface as report_interface
from .web.interface import interface as web_interface


def get_interface():
    """Return the analyzer interface for plugin discovery."""
    return {
        "base": base_interface,
        "report": report_interface,
        "web": web_interface,
    }


__all__ = ["get_interface", "__version__"]
