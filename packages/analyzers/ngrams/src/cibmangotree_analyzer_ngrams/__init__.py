"""N-gram analyzer package for CIBMangoTree."""

__version__ = "0.1.0"

from .base import ngrams
from .stats import ngram_stats
from .web import ngrams_web


def get_interface():
    """Return the analyzer declarations for plugin discovery."""
    return {
        "base": ngrams,
        "stats": ngram_stats,
        "web": ngrams_web,
    }


__all__ = ["get_interface", "__version__"]
