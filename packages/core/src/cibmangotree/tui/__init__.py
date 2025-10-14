"""
Terminal User Interface (TUI) Module

This module provides terminal-based UI components and utilities for
CIB Mango Tree CLI application.

Components:
- components: Interactive menu components, prompts, and views
- tools: Terminal utilities, progress bars, ANSI support
"""

# Re-export commonly used TUI components
from .components import (
    ViewContext,
    main_menu,
    splash,
)

__all__ = [
    "ViewContext",
    "main_menu",
    "splash",
]
