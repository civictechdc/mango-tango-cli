"""
Plugin System for CIB Mango Tree

This module provides plugin discovery and loading functionality for:
- Analyzer plugins (via cibmangotree.analyzers entry point)
- Tokenizer plugins (via cibmangotree.tokenizers entry point)

Supports both normal (entry point) and frozen (PyInstaller) environments.
"""

import importlib
import logging
import sys
from typing import TYPE_CHECKING, Union

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata  # type: ignore

if TYPE_CHECKING:
    from cibmangotree.analyzer_interface import (
        AnalyzerDeclaration,
        SecondaryAnalyzerDeclaration,
        WebPresenterDeclaration,
    )

logger = logging.getLogger(__name__)

__all__ = ["discover_analyzers"]


def _is_frozen():
    """Check if running in a frozen (PyInstaller) environment."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _load_plugin_interface(module_path: str, attr_name: str):
    """
    Load a plugin interface by importing the module and calling the getter.

    Args:
        module_path: Module path (e.g., "cibmangotree_analyzer_hashtags")
        attr_name: Attribute name (e.g., "get_interface")

    Returns:
        The result of calling the interface getter function
    """
    try:
        module = importlib.import_module(module_path)
        getter = getattr(module, attr_name)
        return getter()
    except Exception as e:
        logger.error(
            f"Failed to load plugin {module_path}:{attr_name}",
            exc_info=True,
            extra={"plugin_module": module_path, "attr": attr_name, "error": str(e)},
        )
        return None


def discover_analyzers() -> list[
    Union[
        "AnalyzerDeclaration",
        "SecondaryAnalyzerDeclaration",
        "WebPresenterDeclaration",
    ]
]:
    """
    Discover all analyzer plugins and return their declarations.

    Works in both normal and frozen (PyInstaller) environments:
    - In normal mode: Uses importlib.metadata entry points
    - In frozen mode: Uses _frozen_plugins.ANALYZER_PLUGINS

    Returns:
        List of all analyzer declarations (primary, secondary, and web presenters)
    """
    all_declarations = []

    if _is_frozen():
        # Frozen environment: Load from _frozen_plugins
        logger.info("Running in frozen environment, loading plugins from _frozen_plugins")
        try:
            from cibmangotree._frozen_plugins import ANALYZER_PLUGINS

            for plugin_name, plugin_spec in ANALYZER_PLUGINS.items():
                module_path, attr_name = plugin_spec.split(":")
                logger.debug(
                    f"Loading frozen plugin: {plugin_name}",
                    extra={"plugin_module": module_path, "attr": attr_name},
                )
                interface_dict = _load_plugin_interface(module_path, attr_name)
                if interface_dict:
                    # Each plugin returns {"base": ..., "web": ...}
                    if "base" in interface_dict:
                        all_declarations.append(interface_dict["base"])
                    if "web" in interface_dict:
                        all_declarations.append(interface_dict["web"])
        except ImportError as e:
            logger.error(
                "Failed to import _frozen_plugins in frozen environment",
                exc_info=True,
                extra={"error": str(e)},
            )
    else:
        # Normal environment: Load from entry points
        logger.info("Running in normal environment, loading plugins from entry points")
        try:
            eps = importlib_metadata.entry_points()
            # Handle both old (dict) and new (SelectableGroups) API
            if hasattr(eps, "select"):
                analyzer_eps = eps.select(group="cibmangotree.analyzers")
            else:
                # Old API - eps is a dict
                analyzer_eps = eps.get("cibmangotree.analyzers", [])  # type: ignore[attr-defined]

            for ep in analyzer_eps:
                logger.debug(
                    f"Loading plugin from entry point: {ep.name}",
                    extra={"name": ep.name, "value": ep.value},
                )
                try:
                    # Load the entry point (calls get_interface())
                    interface_dict = ep.load()()
                    # Each plugin returns {"base": ..., "web": ...}
                    if "base" in interface_dict:
                        all_declarations.append(interface_dict["base"])
                    if "web" in interface_dict:
                        all_declarations.append(interface_dict["web"])
                except Exception as e:
                    logger.error(
                        f"Failed to load plugin entry point: {ep.name}",
                        exc_info=True,
                        extra={"name": ep.name, "error": str(e)},
                    )
        except Exception as e:
            logger.error(
                "Failed to discover analyzer plugins",
                exc_info=True,
                extra={"error": str(e)},
            )

    logger.info(
        f"Discovered {len(all_declarations)} analyzer declarations",
        extra={"count": len(all_declarations)},
    )
    return all_declarations
