"""
CIB Mango Tree CLI Entry Point

This module provides the main entry point for the CIB Mango Tree CLI application.
It handles command-line argument parsing, logging setup, and application initialization.
"""

import argparse
import logging
import sys
from multiprocessing import freeze_support
from pathlib import Path

from rich.console import Console
from rich.text import Text

from .tui.tools import enable_windows_ansi_support


def main():
    """Main entry point for the CIB Mango Tree CLI."""
    freeze_support()
    enable_windows_ansi_support()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="CIB Mango Tree CLI - Social Media Data Analysis Tool"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )
    parser.add_argument(
        "--noop", action="store_true", help="No-operation mode for testing"
    )

    args = parser.parse_args()

    # Handle no-op mode
    if args.noop:
        print("No-op flag detected. Exiting successfully.")
        sys.exit(0)

    # Show loading message early
    console = Console()
    loading_msg = Text("🥭 CIB Mango Tree is starting", style="orange1 bold")
    loading_msg.append("... This may take a moment.", style="dim")
    console.print(loading_msg)

    # Import heavy modules after loading message
    try:
        from .app import App, AppContext
        from .app.logger import setup_logging
        from .meta import get_version
        from .services.storage import Storage
        from .tui.components import ViewContext, main_menu, splash
        from .tui.tools.inception import TerminalContext

        # Initialize storage
        storage = Storage(app_name="MangoTango", app_author="Civic Tech DC")

        # Set up logging
        log_level = getattr(logging, args.log_level)
        log_file_path = Path(storage.user_data_dir) / "logs" / "mangotango.log"
        app_version = get_version() or "development"
        setup_logging(log_file_path, log_level, app_version)

        # Get logger for main module
        logger = logging.getLogger(__name__)
        logger.info(
            "Starting CIB Mango Tree application",
            extra={"log_level": args.log_level, "log_file": str(log_file_path)},
        )

        # Initialize app context
        from .analyzer_interface.suite import AnalyzerSuite
        from .plugin_system import discover_analyzers

        all_analyzers = discover_analyzers()
        suite = AnalyzerSuite(all_analyzers=all_analyzers)

        # Start the application
        splash()
        main_menu(
            ViewContext(
                terminal=TerminalContext(),
                app=App(context=AppContext(storage=storage, suite=suite)),
            )
        )
    except ImportError as e:
        # Expected during Phase 2-4 of reorganization
        console.print(
            f"[yellow]Note:[/yellow] Import paths not yet updated. Error: {e}",
            style="dim",
        )
        console.print(
            "[yellow]This is expected during monorepo reorganization (Phase 2-4).[/yellow]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
