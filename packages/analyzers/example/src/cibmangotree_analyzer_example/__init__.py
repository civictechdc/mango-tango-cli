"""Example analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from .base import example_base
from .report import example_report
from .web import example_web


def get_interface():
    """Return the analyzer declarations for plugin discovery."""
    return {
        "base": example_base,
        "report": example_report,
        "web": example_web,
    }


__all__ = ["get_interface", "__version__"]
