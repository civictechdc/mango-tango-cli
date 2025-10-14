"""Time coordination analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from cibmangotree.analyzer_interface import AnalyzerDeclaration

from .interface import interface
from .main import main

time_coordination = AnalyzerDeclaration(
    interface=interface, main=main, is_distributed=True
)


def get_interface():
    """Return the analyzer declarations for plugin discovery."""
    return {"base": time_coordination}


__all__ = ["get_interface", "__version__"]
