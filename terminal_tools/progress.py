"""
Progress reporting functionality for terminal-based analysis workflows.

This module provides various progress reporting implementations:
- ProgressReporter: Basic progress reporting with start/finish lifecycle
- RichProgressManager: Advanced progress manager with Rich library integration

The RichProgressManager is the recommended progress reporting solution for analyzers,
providing hierarchical step and sub-step support with Rich terminal visualization.
"""

import gc
import logging
import time
from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Spinner frames for activity indication
_spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class ProgressReporter:
    """Basic progress reporter with simple start/finish lifecycle."""

    def __init__(self, title: str):
        """Initialize progress reporter.

        Args:
            title: Title to display for this progress operation
        """
        self.title = title
        self._start_time = None
        self._last_update = None

    def __enter__(self):
        """Context manager entry - records start time."""
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - records finish time."""
        pass

    def update(self, current: int, total: Optional[int] = None, message: str = ""):
        """Update progress (basic implementation for compatibility)."""
        self._last_update = time.time()


class RichProgressManager:
    """Rich-based multi-step progress manager using proper Live display patterns.

    This implementation follows Rich's documented best practices:
    - Uses a mutable Table object that gets modified in-place
    - No generator patterns or complex layouts
    - Each instance has its own Live display
    - Rich automatically detects table changes

    Step states:
    - pending (⏸): Not yet started
    - active (⏳): Currently running
    - completed (✓): Successfully finished
    - failed (❌): Failed with optional error message

    Example:
        with RichProgressManager("N-gram Analysis Progress") as manager:
            manager.add_step("preprocess", "Preprocessing data", 1000)
            manager.add_step("tokenize", "Tokenizing text", 500)

            manager.start_step("preprocess")
            for i in range(1000):
                manager.update_step("preprocess", i + 1)
            manager.complete_step("preprocess")
    """

    def __init__(self, title: str, memory_manager: Optional["MemoryManager"] = None):
        """Initialize the progress manager.

        Args:
            title: The overall title for the progress display
            memory_manager: Optional MemoryManager for memory monitoring
        """
        self.title = title
        self.memory_manager = memory_manager
        self.last_memory_warning = None if memory_manager else None

        # Progress tracking
        self.steps: Dict[str, dict] = {}
        self.substeps: Dict[str, Dict[str, dict]] = {}
        self.step_order: List[str] = []
        self.active_step: Optional[str] = None
        self.active_substeps: Dict[str, Optional[str]] = {}

        # Rich components - each instance gets its own
        self.console = Console()
        self.table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
        self.table.add_column("Status", style="bold", width=3, justify="center")
        self.table.add_column("Task", ratio=1)

        self.live: Optional[Live] = None
        self._started = False

        # Symbols for different states
        self.SYMBOLS = {
            "pending": "⏸",
            "active": "⏳",
            "completed": "✓",
            "failed": "❌",
        }

    def add_step(self, step_id: str, title: str, total: int = None):
        """Add a new step to the checklist.

        Args:
            step_id: Unique identifier for the step
            title: Display title for the step
            total: Total number of items for progress tracking (optional)
        """
        if step_id in self.steps:
            raise ValueError(f"Step '{step_id}' already exists")

        self.steps[step_id] = {
            "title": title,
            "total": total,
            "progress": 0,
            "state": "pending",
            "error_msg": None,
            "substep_progress": 0.0,  # Percentage of substeps completed (0-100)
        }
        self.step_order.append(step_id)

        # If this is the first step and we're started, create the Live display
        if self._started and self.live is None and len(self.step_order) == 1:
            self._rebuild_table()
            self.live = Live(
                self._create_panel(),
                console=self.console,
                refresh_per_second=4,
                auto_refresh=True,
            )
            self.live.start()
        elif self._started and self.live:
            # Update existing display
            self._rebuild_table()

    def add_substep(
        self, parent_step_id: str, substep_id: str, description: str, total: int = None
    ):
        """Add a new substep to a parent step.

        Args:
            parent_step_id: ID of the parent step
            substep_id: Unique identifier for the substep (unique within parent)
            description: Display description for the substep
            total: Total number of items for progress tracking (optional)
        """
        if parent_step_id not in self.steps:
            raise ValueError(f"Parent step '{parent_step_id}' not found")

        # Initialize substeps dict for parent if not exists
        if parent_step_id not in self.substeps:
            self.substeps[parent_step_id] = {}

        if substep_id in self.substeps[parent_step_id]:
            raise ValueError(
                f"Substep '{substep_id}' already exists in parent '{parent_step_id}'"
            )

        # Store substep info
        self.substeps[parent_step_id][substep_id] = {
            "description": description,
            "total": total,
            "progress": 0,
            "state": "pending",
            "error_msg": None,
            "parent_step_id": parent_step_id,
        }

        # Update display if already started
        if self._started:
            self._rebuild_table()

    def start_step(self, step_id: str):
        """Start/activate a specific step.

        Args:
            step_id: ID of the step to start
        """
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        # Complete any currently active step first
        if self.active_step and self.steps[self.active_step]["state"] == "active":
            self.complete_step(self.active_step)

        self.active_step = step_id
        step_info = self.steps[step_id]
        step_info["state"] = "active"

        # Update display and create Live if needed
        if self._started:
            if self.live is None:
                self._rebuild_table()
                self.live = Live(
                    self._create_panel(),
                    console=self.console,
                    refresh_per_second=4,
                    auto_refresh=True,
                )
                self.live.start()
            else:
                self._rebuild_table()

    def update_step(self, step_id: str, progress: float, total: int = None):
        """Update the progress of a specific step.

        Args:
            step_id: ID of the step to update
            progress: Current progress value
            total: Optional new total to update for this step
        """
        # Validate step_id
        if not step_id or not isinstance(step_id, str):
            raise ValueError("Invalid step_id: must be a non-empty string")

        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        # Validate progress type
        if not isinstance(progress, (int, float)):
            raise TypeError("Progress must be a number")

        step_info = self.steps[step_id]

        # Handle optional total update
        if total is not None:
            if not isinstance(total, int) or total <= 0:
                raise ValueError(f"total must be a positive integer, got {total}")
            if progress > total:
                raise ValueError(f"Progress {progress} exceeds new total {total}")
            step_info["total"] = total

        # Validate progress bounds
        if progress < 0:
            raise ValueError(f"Progress cannot be negative, got {progress}")

        if step_info["total"] is not None and progress > step_info["total"]:
            raise ValueError(f"Progress {progress} exceeds total {step_info['total']}")

        # Update progress
        step_info["progress"] = progress

        # Update display
        if self._started:
            self._rebuild_table()

    def complete_step(self, step_id: str):
        """Mark a step as completed.

        Args:
            step_id: ID of the step to complete
        """
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step_info = self.steps[step_id]
        step_info["state"] = "completed"

        # If total was specified, ensure progress is at 100%
        if step_info["total"] is not None:
            step_info["progress"] = step_info["total"]

        # Clear active step if this was the active step
        if step_id == self.active_step:
            self.active_step = None

        # Update display
        if self._started:
            self._rebuild_table()

    def fail_step(self, step_id: str, error_msg: str = None):
        """Mark a step as failed.

        Args:
            step_id: ID of the step to mark as failed
            error_msg: Optional error message to display
        """
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step_info = self.steps[step_id]
        step_info["state"] = "failed"
        step_info["error_msg"] = error_msg

        # Clear active step if this was the active step
        if step_id == self.active_step:
            self.active_step = None

        # Update display
        if self._started:
            self._rebuild_table()

    def start_substep(self, parent_step_id: str, substep_id: str):
        """Start/activate a specific substep.

        Args:
            parent_step_id: ID of the parent step
            substep_id: ID of the substep to start
        """
        if parent_step_id not in self.steps:
            raise ValueError(f"Parent step '{parent_step_id}' not found")

        if (
            parent_step_id not in self.substeps
            or substep_id not in self.substeps[parent_step_id]
        ):
            raise ValueError(
                f"Substep '{substep_id}' not found in parent '{parent_step_id}'"
            )

        # Make sure parent step is active
        if self.steps[parent_step_id]["state"] != "active":
            step_info = self.steps[parent_step_id]
            step_info["state"] = "active"
            if not self.active_step:
                self.active_step = parent_step_id

        # Complete any currently active substep for this parent first
        if parent_step_id in self.active_substeps:
            current_active = self.active_substeps[parent_step_id]
            if (
                current_active
                and current_active in self.substeps[parent_step_id]
                and self.substeps[parent_step_id][current_active]["state"] == "active"
            ):
                self.complete_substep(parent_step_id, current_active)

        # Set new active substep
        self.active_substeps[parent_step_id] = substep_id
        substep_info = self.substeps[parent_step_id][substep_id]
        substep_info["state"] = "active"

        # Update display
        if self._started:
            self._rebuild_table()

    def update_substep(
        self, parent_step_id: str, substep_id: str, progress: int, total: int = None
    ):
        """Update the progress of a specific substep.

        Args:
            parent_step_id: ID of the parent step
            substep_id: ID of the substep to update
            progress: Current progress value
            total: Optional new total to update for this substep
        """
        if parent_step_id not in self.steps:
            raise ValueError(f"Parent step '{parent_step_id}' not found")

        if (
            parent_step_id not in self.substeps
            or substep_id not in self.substeps[parent_step_id]
        ):
            raise ValueError(
                f"Substep '{substep_id}' not found in parent '{parent_step_id}'"
            )

        substep_info = self.substeps[parent_step_id][substep_id]

        # Handle optional total update
        if total is not None:
            if not isinstance(total, int) or total <= 0:
                raise ValueError(f"total must be a positive integer, got {total}")
            if progress > total:
                raise ValueError(f"Progress {progress} exceeds new total {total}")
            substep_info["total"] = total

        # Validate progress bounds
        if progress < 0:
            raise ValueError(f"Progress cannot be negative, got {progress}")

        if substep_info["total"] is not None and progress > substep_info["total"]:
            raise ValueError(
                f"Progress {progress} exceeds total {substep_info['total']}"
            )

        # Update substep progress
        substep_info["progress"] = progress

        # Update parent step progress based on substep completion
        self._update_parent_progress(parent_step_id)

        # Update display
        if self._started:
            self._rebuild_table()

    def complete_substep(self, parent_step_id: str, substep_id: str):
        """Mark a substep as completed.

        Args:
            parent_step_id: ID of the parent step
            substep_id: ID of the substep to complete
        """
        if parent_step_id not in self.steps:
            raise ValueError(f"Parent step '{parent_step_id}' not found")

        if (
            parent_step_id not in self.substeps
            or substep_id not in self.substeps[parent_step_id]
        ):
            raise ValueError(
                f"Substep '{substep_id}' not found in parent '{parent_step_id}'"
            )

        substep_info = self.substeps[parent_step_id][substep_id]
        substep_info["state"] = "completed"

        # If total was specified, ensure progress is at 100%
        if substep_info["total"] is not None:
            substep_info["progress"] = substep_info["total"]

        # Clear active substep if this was the active substep
        if (
            parent_step_id in self.active_substeps
            and self.active_substeps[parent_step_id] == substep_id
        ):
            self.active_substeps[parent_step_id] = None

        # Update parent step progress
        self._update_parent_progress(parent_step_id)

        # Update display
        if self._started:
            self._rebuild_table()

    def fail_substep(self, parent_step_id: str, substep_id: str, error_msg: str = None):
        """Mark a substep as failed.

        Args:
            parent_step_id: ID of the parent step
            substep_id: ID of the substep to mark as failed
            error_msg: Optional error message to display
        """
        if parent_step_id not in self.steps:
            raise ValueError(f"Parent step '{parent_step_id}' not found")

        if (
            parent_step_id not in self.substeps
            or substep_id not in self.substeps[parent_step_id]
        ):
            raise ValueError(
                f"Substep '{substep_id}' not found in parent '{parent_step_id}'"
            )

        substep_info = self.substeps[parent_step_id][substep_id]
        substep_info["state"] = "failed"
        substep_info["error_msg"] = error_msg

        # Clear active substep if this was the active substep
        if (
            parent_step_id in self.active_substeps
            and self.active_substeps[parent_step_id] == substep_id
        ):
            self.active_substeps[parent_step_id] = None

        # Update display
        if self._started:
            self._rebuild_table()

    def _update_parent_progress(self, parent_step_id: str):
        """Update parent step progress based on substep completion."""
        if parent_step_id not in self.substeps:
            return

        substeps = self.substeps[parent_step_id]
        if not substeps:
            return

        # Calculate parent progress based on substep completion
        completed_substeps = sum(
            1 for substep in substeps.values() if substep["state"] == "completed"
        )
        total_substeps = len(substeps)

        # Update parent step progress
        if total_substeps > 0:
            parent_step = self.steps[parent_step_id]

            # Calculate substep progress percentage (0-100)
            substep_progress_percentage = (completed_substeps / total_substeps) * 100
            parent_step["substep_progress"] = substep_progress_percentage

            if parent_step["total"] is not None:
                # Update progress relative to the parent step's total
                parent_progress = (completed_substeps / total_substeps) * parent_step[
                    "total"
                ]
                parent_step["progress"] = parent_progress

    def _rebuild_table(self):
        """Rebuild the table with current step information.

        This is the core method that implements Rich's mutable object pattern.
        We create a fresh table each time to avoid Rich's internal state issues.
        """
        # Create a fresh table
        self.table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
        self.table.add_column("Status", style="bold", width=3, justify="center")
        self.table.add_column("Task", ratio=1)

        # Add rows for each step (if any)
        for step_id in self.step_order:
            step_info = self.steps[step_id]

            # Build main step row
            symbol = self.SYMBOLS[step_info["state"]]
            title = step_info["title"]

            # Build step text with progress information
            if step_info["total"] is not None and step_info["state"] in [
                "active",
                "completed",
            ]:
                percentage = (
                    (step_info["progress"] / step_info["total"]) * 100
                    if step_info["total"] > 0
                    else 0
                )
                step_text = f"{title} ({step_info['progress']}/{step_info['total']} - {percentage:.0f}%)"
            else:
                step_text = title

            # Add substep summary if exists
            if step_id in self.substeps and self.substeps[step_id]:
                substeps = self.substeps[step_id]
                completed_substeps = sum(
                    1 for s in substeps.values() if s["state"] == "completed"
                )
                total_substeps = len(substeps)
                if step_info["state"] == "active" and total_substeps > 0:
                    substep_percent = (completed_substeps / total_substeps) * 100
                    step_text += f" [{substep_percent:.0f}% substeps]"

            # Add error message if failed
            if step_info["state"] == "failed" and step_info["error_msg"]:
                step_text += f" - [red]{step_info['error_msg']}[/red]"

            # Style based on state
            style = {
                "completed": "green",
                "failed": "red",
                "active": "yellow",
                "pending": "dim white",
            }.get(step_info["state"], "dim white")

            # Add main step row
            self.table.add_row(symbol, Text(step_text, style=style))

            # Add substep rows
            if step_id in self.substeps and self.substeps[step_id]:
                for substep_id, substep_info in self.substeps[step_id].items():
                    substep_description = substep_info["description"]

                    # Build substep text with progress
                    if substep_info["total"] is not None and substep_info["state"] in [
                        "active",
                        "completed",
                    ]:
                        substep_percentage = (
                            (substep_info["progress"] / substep_info["total"]) * 100
                            if substep_info["total"] > 0
                            else 0
                        )
                        if substep_info["state"] == "active":
                            # Show inline progress bar for active substeps
                            bar_width = 20
                            filled_width = int((substep_percentage / 100) * bar_width)
                            bar = "█" * filled_width + "░" * (bar_width - filled_width)
                            substep_text = (
                                f"  └─ {substep_description} [{bar}] "
                                f"({substep_info['progress']}/{substep_info['total']} - {substep_percentage:.0f}%)"
                            )
                        else:
                            substep_text = (
                                f"  └─ {substep_description} "
                                f"({substep_info['progress']}/{substep_info['total']} - {substep_percentage:.0f}%)"
                            )
                    else:
                        substep_text = f"  └─ {substep_description}"

                    # Add error message if failed
                    if substep_info["state"] == "failed" and substep_info["error_msg"]:
                        substep_text += f" - [red]{substep_info['error_msg']}[/red]"

                    # Style based on state
                    sub_style = {
                        "completed": "green",
                        "failed": "red",
                        "active": "yellow",
                        "pending": "dim white",
                    }.get(substep_info["state"], "dim white")

                    # Add substep row
                    self.table.add_row("", Text(substep_text, style=sub_style))

        # Update the Live display with the new table if it exists
        if self._started and self.live:
            self.live.update(self._create_panel())

    def start(self):
        """Start the progress display."""
        if self._started:
            return

        self._started = True

        # Create empty table structure but don't start Live display yet
        self.table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
        self.table.add_column("Status", style="bold", width=3, justify="center")
        self.table.add_column("Task", ratio=1)

        # Don't create Live display until we have actual content to show
        self.live = None

    def _create_panel(self):
        """Create a panel with the current table."""
        return Panel(self.table, title=self.title, border_style="blue")

    def refresh_display(self):
        """Force a refresh of the display.

        With the new architecture, this just rebuilds the table.
        Rich handles the actual display refresh automatically.
        """
        if self._started:
            self._rebuild_table()

    def finish(self):
        """Finish the progress display and cleanup."""
        if not self._started:
            return

        if self.live:
            self.live.stop()
            self.live = None

        self._started = False

    def __enter__(self):
        """Context manager entry - starts the display."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit - finishes the display."""
        # Display memory summary if memory manager is active
        if exc_type is None and self.memory_manager is not None:
            try:
                self.display_memory_summary()
            except Exception:
                # Don't let memory summary failures crash the exit
                pass

        # Handle KeyboardInterrupt specially to ensure clean terminal state
        if exc_type is KeyboardInterrupt:
            try:
                if self.live:
                    self.live.stop()
                    self.live = None
                self.console.clear()
                self._started = False
            except Exception:
                try:
                    self.console.clear()
                except Exception:
                    pass
        else:
            # Normal cleanup
            self.finish()

    def update_step_with_memory(
        self, step_id: str, current: int, memory_context: str = ""
    ) -> None:
        """Update progress step with current memory usage information.

        This method combines standard progress updates with memory monitoring.
        Only active when memory_manager is provided during initialization.
        """
        if self.memory_manager is None:
            # Fallback to standard update when no memory manager
            self.update_step(step_id, current)
            return

        # Get current memory stats
        try:
            memory_stats = self.memory_manager.get_current_memory_usage()
        except Exception as e:
            # If memory monitoring fails, continue with standard progress update
            from app.logger import get_logger

            logger = get_logger(__name__)
            logger.warning(
                "Memory monitoring failed, continuing with standard progress update",
                extra={
                    "step_id": step_id,
                    "current": current,
                    "memory_context": memory_context,
                    "error": str(e),
                },
            )
            self.update_step(step_id, current)
            return

        # Update the progress step
        self.update_step(step_id, current)

        # Check for memory pressure and warn if necessary
        try:
            from app.utils import MemoryPressureLevel

            pressure_level_str = memory_stats["pressure_level"]
            pressure_level = next(
                (
                    level
                    for level in MemoryPressureLevel
                    if level.value == pressure_level_str
                ),
                MemoryPressureLevel.LOW,
            )

            if pressure_level in [
                MemoryPressureLevel.HIGH,
                MemoryPressureLevel.CRITICAL,
            ]:
                self._display_memory_warning(
                    pressure_level, memory_stats, memory_context
                )

        except Exception as e:
            from app.logger import get_logger

            logger = get_logger(__name__)
            logger.warning(
                "Failed to process memory pressure level in progress reporting",
                extra={
                    "step_id": step_id,
                    "pressure_level_str": memory_stats.get("pressure_level", "unknown"),
                    "memory_context": memory_context,
                    "error": str(e),
                },
            )

        # Trigger GC if needed
        try:
            if self.memory_manager.should_trigger_gc():
                cleanup_stats = self.memory_manager.enhanced_gc_cleanup()
                if cleanup_stats["memory_freed_mb"] > 50:  # Significant cleanup
                    self.console.print(
                        f"[green]Freed {cleanup_stats['memory_freed_mb']:.1f}MB memory[/green]"
                    )
        except Exception as e:
            from app.logger import get_logger

            logger = get_logger(__name__)
            logger.warning(
                "Failed to trigger garbage collection in progress reporting",
                extra={
                    "step_id": step_id,
                    "memory_context": memory_context,
                    "error": str(e),
                },
            )

    def _display_memory_warning(
        self, pressure_level: "MemoryPressureLevel", memory_stats: Dict, context: str
    ) -> None:
        """Display memory pressure warning to user."""
        if self.memory_manager is None:
            return

        # Avoid spam - only show warning every 30 seconds
        current_time = time.time()
        if self.last_memory_warning and current_time - self.last_memory_warning < 30:
            return

        self.last_memory_warning = current_time

        try:
            from app.utils import MemoryPressureLevel

            memory_mb = memory_stats["rss_mb"]
            pressure_color = {
                MemoryPressureLevel.HIGH: "yellow",
                MemoryPressureLevel.CRITICAL: "red",
            }.get(pressure_level, "yellow")

            warning_text = f"Memory Usage: {memory_mb:.1f}MB ({memory_stats['process_memory_percent']:.1f}% of limit)"
            if context:
                warning_text += f" during {context}"

            # Suggest actions based on pressure level
            if pressure_level == MemoryPressureLevel.CRITICAL:
                warning_text += (
                    "\n⚠️  Critical memory pressure - switching to disk-based processing"
                )
            elif pressure_level == MemoryPressureLevel.HIGH:
                warning_text += "\n⚠️  High memory pressure - reducing chunk sizes"

            panel = Panel(
                warning_text, title="Memory Monitor", border_style=pressure_color
            )
            self.console.print(panel)

        except Exception as e:
            from app.logger import get_logger

            logger = get_logger(__name__)
            logger.warning(
                "Failed to display memory warning",
                extra={
                    "pressure_level": (
                        pressure_level.value
                        if hasattr(pressure_level, "value")
                        else str(pressure_level)
                    ),
                    "memory_mb": memory_stats.get("rss_mb", "unknown"),
                    "context": context,
                    "error": str(e),
                },
            )

    def display_memory_summary(self) -> None:
        """Display final memory usage summary."""
        if self.memory_manager is None:
            return

        try:
            final_memory = self.memory_manager.get_current_memory_usage()
            memory_trend = self.memory_manager.get_memory_trend()

            summary_panel = Panel(
                f"Analysis completed successfully!\n"
                f"Peak memory usage: {final_memory['rss_mb']:.1f}MB\n"
                f"Memory trend: {memory_trend}\n"
                f"Final pressure level: {final_memory['pressure_level']}",
                title="Memory Summary",
                border_style="green",
            )
            self.console.print(summary_panel)

        except Exception as e:
            from app.logger import get_logger

            logger = get_logger(__name__)
            logger.warning("Failed to display memory summary", extra={"error": str(e)})


# Backward compatibility alias
ChecklistProgressManager = RichProgressManager

# Advanced progress reporter (not currently used, but defined for future use)
AdvancedProgressReporter = ProgressReporter
