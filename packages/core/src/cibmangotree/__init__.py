"""
CIB Mango Tree - Social Media Data Analysis Tool

A modular CLI and library for analyzing social media data with support
for extensible analyzers, tokenizers, and export formats.
"""

from .meta import get_version, is_development, is_distributed

# Version information
__version__ = get_version() or "0.1.0-dev"
__all__ = [
    "__version__",
    "get_version",
    "is_development",
    "is_distributed",
    # Core application
    "App",
    "AppContext",
    # Analysis contexts
    "AnalysisContext",
    "AnalysisOutputContext",
    "AnalysisWebServerContext",
    "ProjectContext",
    "SettingsContext",
    # Analyzer interface
    "AnalyzerInterface",
    "PrimaryAnalyzerContext",
    "SecondaryAnalyzerContext",
    "ParamValue",
    "AnalyzerOutput",
    # Storage
    "Storage",
]

# Import core application components
from .app import (
    App,
    AppContext,
    AnalysisContext,
    AnalysisOutputContext,
    AnalysisWebServerContext,
    ProjectContext,
    SettingsContext,
)

# Import analyzer interface
from .analyzer_interface import (
    AnalyzerInterface,
    AnalyzerOutput,
    ParamValue,
)
from .analyzer_interface.context import (
    PrimaryAnalyzerContext,
    SecondaryAnalyzerContext,
)

# Import storage service
from .services.storage import Storage
