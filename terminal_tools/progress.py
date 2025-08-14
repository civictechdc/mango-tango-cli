"""
Progress reporting functionality for terminal-based analysis workflows.

Provides hierarchical progress tracking with real-time terminal display:
- ProgressReporter: Basic progress reporting with context manager support
- ProgressManager: Full-featured progress manager with step and substep tracking
- ProgressStateManager: Core progress state management and validation
- TextualInlineProgressDisplay: Textual-based inline progress display
- SimpleProgressApp: Minimal Textual app for inline progress visualization
"""

import queue
import threading
import time
from typing import Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from app.utils import MemoryPressureLevel, MemoryManager

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Static
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


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


class ProgressStateManager:
    """Core progress state management with validation and tracking.
    
    Manages hierarchical progress tracking with steps and substeps,
    including state transitions, validation, and Rich table generation.
    """

    def __init__(self):
        """Initialize progress state tracking."""
        # Progress tracking data structures
        self.steps: Dict[str, dict] = {}
        self.substeps: Dict[str, Dict[str, dict]] = {}
        self.step_order: List[str] = []
        self.active_step: Optional[str] = None
        self.active_substeps: Dict[str, Optional[str]] = {}

        # State symbols for different progress states
        self.SYMBOLS = {
            "pending": "⏸",
            "active": "⏳",
            "completed": "✓",
            "failed": "❌",
        }

    def add_step(
        self,
        step_id: str,
        title: str,
        total: int = None,
        insert_at: Union[None, int, str] = None,
    ):
        """Add a new step to the progress tracking.

        Args:
            step_id: Unique identifier for the step
            title: Display title for the step
            total: Total number of items for progress tracking (optional)
            insert_at: Position to insert step (None=append, int=index, str=after_step_id)
        """
        if step_id in self.steps:
            raise ValueError(f"Step '{step_id}' already exists")

        self.steps[step_id] = {
            "title": title,
            "total": total,
            "progress": 0,
            "state": "pending",
            "error_msg": None,
            "substep_progress": 0.0,
        }

        # Handle positional insertion
        if insert_at is None:
            self.step_order.append(step_id)
        elif isinstance(insert_at, int):
            if 0 <= insert_at <= len(self.step_order):
                self.step_order.insert(insert_at, step_id)
            else:
                self.step_order.append(step_id)
        elif isinstance(insert_at, str):
            try:
                target_index = self.step_order.index(insert_at)
                self.step_order.insert(target_index + 1, step_id)
            except ValueError:
                self.step_order.append(step_id)
        else:
            self.step_order.append(step_id)

    def add_substep(
        self,
        parent_step_id: str,
        substep_id: str,
        description: str,
        total: int = None,
        insert_at: Union[None, int, str] = None,
    ):
        """Add a new substep to a parent step.

        Args:
            parent_step_id: ID of the parent step
            substep_id: Unique identifier for the substep
            description: Display description for the substep
            total: Total number of items for progress tracking (optional)
            insert_at: Position to insert substep within parent
        """
        if parent_step_id not in self.steps:
            raise ValueError(f"Parent step '{parent_step_id}' not found")

        if parent_step_id not in self.substeps:
            self.substeps[parent_step_id] = {}

        if substep_id in self.substeps[parent_step_id]:
            raise ValueError(
                f"Substep '{substep_id}' already exists in parent '{parent_step_id}'"
            )

        substep_data = {
            "description": description,
            "total": total,
            "progress": 0,
            "state": "pending",
            "error_msg": None,
            "parent_step_id": parent_step_id,
        }

        # Handle positional insertion for substeps
        parent_substeps = self.substeps[parent_step_id]
        if insert_at is None:
            parent_substeps[substep_id] = substep_data
        elif isinstance(insert_at, int):
            substep_items = list(parent_substeps.items())
            if 0 <= insert_at <= len(substep_items):
                substep_items.insert(insert_at, (substep_id, substep_data))
            else:
                substep_items.append((substep_id, substep_data))
            self.substeps[parent_step_id] = dict(substep_items)
        elif isinstance(insert_at, str):
            substep_items = list(parent_substeps.items())
            try:
                target_index = next(
                    i for i, (k, v) in enumerate(substep_items) if k == insert_at
                )
                substep_items.insert(target_index + 1, (substep_id, substep_data))
                self.substeps[parent_step_id] = dict(substep_items)
            except (StopIteration, ValueError):
                parent_substeps[substep_id] = substep_data
        else:
            parent_substeps[substep_id] = substep_data

    def start_step(self, step_id: str):
        """Start/activate a specific step."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        # Complete any currently active step first
        if self.active_step and self.steps[self.active_step]["state"] == "active":
            self.complete_step(self.active_step)

        self.active_step = step_id
        self.steps[step_id]["state"] = "active"

    def update_step(self, step_id: str, progress: float, total: int = None):
        """Update the progress of a specific step."""
        if not step_id or not isinstance(step_id, str):
            raise ValueError("Invalid step_id: must be a non-empty string")

        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

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

        step_info["progress"] = progress

    def complete_step(self, step_id: str):
        """Mark a step as completed."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step_info = self.steps[step_id]
        step_info["state"] = "completed"

        if step_info["total"] is not None:
            step_info["progress"] = step_info["total"]

        if step_id == self.active_step:
            self.active_step = None

    def fail_step(self, step_id: str, error_msg: str = None):
        """Mark a step as failed."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step_info = self.steps[step_id]
        step_info["state"] = "failed"
        step_info["error_msg"] = error_msg

        if step_id == self.active_step:
            self.active_step = None

    def start_substep(self, parent_step_id: str, substep_id: str):
        """Start/activate a specific substep."""
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
            self.steps[parent_step_id]["state"] = "active"
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

        self.active_substeps[parent_step_id] = substep_id
        self.substeps[parent_step_id][substep_id]["state"] = "active"

    def update_substep(
        self, parent_step_id: str, substep_id: str, progress: int, total: int = None
    ):
        """Update the progress of a specific substep."""
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

        substep_info["progress"] = progress
        self._update_parent_progress(parent_step_id)

    def complete_substep(self, parent_step_id: str, substep_id: str):
        """Mark a substep as completed."""
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

        if substep_info["total"] is not None:
            substep_info["progress"] = substep_info["total"]

        if (
            parent_step_id in self.active_substeps
            and self.active_substeps[parent_step_id] == substep_id
        ):
            self.active_substeps[parent_step_id] = None

        self._update_parent_progress(parent_step_id)

    def fail_substep(self, parent_step_id: str, substep_id: str, error_msg: str = None):
        """Mark a substep as failed."""
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

        if (
            parent_step_id in self.active_substeps
            and self.active_substeps[parent_step_id] == substep_id
        ):
            self.active_substeps[parent_step_id] = None

    def _update_parent_progress(self, parent_step_id: str):
        """Update parent step progress based on substep completion."""
        if parent_step_id not in self.substeps or not self.substeps[parent_step_id]:
            return

        substeps = self.substeps[parent_step_id]
        completed_substeps = sum(
            1 for s in substeps.values() if s["state"] == "completed"
        )
        total_substeps = len(substeps)

        if total_substeps > 0:
            parent_step = self.steps[parent_step_id]
            substep_progress_percentage = (completed_substeps / total_substeps) * 100
            parent_step["substep_progress"] = substep_progress_percentage

            if parent_step["total"] is not None:
                parent_progress = (completed_substeps / total_substeps) * parent_step[
                    "total"
                ]
                parent_step["progress"] = parent_progress

    def build_progress_table(self) -> Table:
        """Build a Rich Table with current progress state."""
        table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
        table.add_column("Status", style="bold", width=3, justify="center")
        table.add_column("Task", ratio=1)

        for step_id in self.step_order:
            if step_id not in self.steps:
                continue

            step_info = self.steps[step_id]
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

            table.add_row(symbol, Text(step_text, style=style))

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

                    table.add_row("", Text(substep_text, style=sub_style))

        return table


class RichProgressDisplay:
    """Rich Live-based progress display for hierarchical progress tracking.
    
    Provides smooth progress updates using Rich Live display
    with table rendering for hierarchical progress visualization.
    """

    def __init__(self, title: str):
        """Initialize Rich progress display.

        Args:
            title: Title for the progress display
        """
        self.title = title
        self.console = Console()
        self.live: Optional[Live] = None
        self._running = False

    def start(self) -> None:
        """Start the Rich Live display."""
        if not self._running:
            self._running = True
            # Create initial empty table
            initial_table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
            initial_table.add_column("Status", style="bold", width=3, justify="center")
            initial_table.add_column("Task", ratio=1)
            
            panel = Panel(initial_table, title=self.title, border_style="blue")
            self.live = Live(panel, console=self.console, refresh_per_second=10)
            self.live.start()

    def update_table(self, table: Table) -> None:
        """Update the progress table (thread-safe)."""
        if self._running and self.live:
            panel = Panel(table, title=self.title, border_style="blue")
            self.live.update(panel)

    def stop(self) -> None:
        """Stop the Rich Live display."""
        if self._running and self.live:
            self._running = False
            self.live.stop()
            self.live = None


if TEXTUAL_AVAILABLE:
    class SimpleProgressApp(App):
        """Minimal Textual app for displaying progress inline.
        
        Uses inline=True mode to display progress below inquirer prompts
        without terminal conflicts. Provides hierarchical progress display
        with symbols and progress bars.
        """

        def __init__(self, title: str, **kwargs):
            """Initialize the Simple Progress App.

            Args:
                title: Title for the progress display
                **kwargs: Additional Textual App arguments
            """
            super().__init__(**kwargs)
            self.title = title
            self.progress_display: Optional[Static] = None
            self.update_queue: queue.Queue = queue.Queue()
            self._should_exit = False

        def compose(self) -> ComposeResult:
            """Compose the app layout with minimal widgets."""
            with Vertical():
                self.progress_display = Static("", id="progress_display")
                yield self.progress_display

        def on_mount(self) -> None:
            """Called when app is mounted - start update processing."""
            self.set_interval(0.1, self.process_updates)

        def process_updates(self) -> None:
            """Process queued updates from background thread."""
            try:
                while True:
                    try:
                        update_data = self.update_queue.get_nowait()
                        if update_data == "EXIT":
                            self._should_exit = True
                            self.exit()
                            break
                        elif isinstance(update_data, str):
                            # Update display content
                            if self.progress_display:
                                self.progress_display.update(update_data)
                    except queue.Empty:
                        break
            except Exception:
                # Ignore errors in update processing to prevent crashes
                pass

        def update_content(self, content: str) -> None:
            """Thread-safe method to update progress content."""
            try:
                self.update_queue.put(content)
            except Exception:
                # Ignore queue errors to prevent crashes
                pass

        def shutdown(self) -> None:
            """Shutdown the app safely."""
            try:
                self.update_queue.put("EXIT")
            except Exception:
                # Ignore queue errors during shutdown
                pass

    class TextualInlineProgressDisplay:
        """Textual-based inline progress display for hierarchical progress tracking.
        
        Uses Rich Live display with reduced refresh rate to provide smooth updates
        while being compatible with inquirer prompts. This approach provides
        non-conflicting progress display that appears inline.
        """

        def __init__(self, title: str):
            """Initialize inline progress display.

            Args:
                title: Title for the progress display
            """
            self.title = title
            self.console = Console()
            self.live: Optional[Live] = None
            self._running = False
            self._update_lock = threading.Lock()

        def start(self) -> None:
            """Start the inline progress display."""
            if not self._running:
                self._running = True
                # Create initial empty table
                initial_table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
                initial_table.add_column("Status", style="bold", width=3, justify="center")
                initial_table.add_column("Task", ratio=1)
                
                # Use Live display with very low refresh rate to avoid conflicts
                self.live = Live(
                    Panel(initial_table, title=f"📊 {self.title}", border_style="blue"),
                    console=self.console,
                    refresh_per_second=2,  # Low refresh rate to avoid conflicts
                    auto_refresh=True
                )
                self.live.start()

        def update_table(self, table: Table) -> None:
            """Update the progress table (thread-safe)."""
            if not self._running or not self.live:
                return

            with self._update_lock:
                try:
                    panel = Panel(table, title=f"📊 {self.title}", border_style="blue")
                    self.live.update(panel)
                except Exception:
                    # Ignore update errors to prevent crashes
                    pass

        def stop(self) -> None:
            """Stop the inline progress display."""
            if not self._running:
                return

            self._running = False

            with self._update_lock:
                try:
                    if self.live:
                        self.live.stop()
                        self.live = None
                    # Print completion message
                    self.console.print("✅ [green]Progress completed[/green]\n")
                except Exception:
                    # Ignore cleanup errors
                    pass

else:
    # If Textual is not available, create stub classes that fall back to Rich
    class SimpleProgressApp:
        """Stub class when Textual is not available."""
        def __init__(self, *args, **kwargs):
            pass

    class TextualInlineProgressDisplay:
        """Fallback to Rich display when Textual is not available."""
        
        def __init__(self, title: str):
            self.rich_display = RichProgressDisplay(title)

        def start(self) -> None:
            self.rich_display.start()

        def update_table(self, table: Table) -> None:
            self.rich_display.update_table(table)

        def stop(self) -> None:
            self.rich_display.stop()


class ProgressManager:
    """Full-featured progress manager with hierarchical tracking and memory monitoring.
    
    Features:
    - Hierarchical progress (steps with optional substeps)
    - Real-time terminal display with 60fps updates
    - Positional insertion for dynamic step ordering
    - Memory pressure monitoring and reporting
    - Context manager support for automatic lifecycle
    - Rich formatting with progress bars and status indicators
    """

    def __init__(
        self,
        title: str,
        memory_manager: Optional["MemoryManager"] = None,
    ):
        """Initialize the unified progress manager.

        Args:
            title: The overall title for the progress display
            memory_manager: Optional MemoryManager for memory monitoring
        """
        self.title = title
        self.memory_manager = memory_manager
        self.last_memory_warning = None if memory_manager is None else 0

        self.state_manager = ProgressStateManager()
        self.display: Optional[TextualInlineProgressDisplay] = None
        self._started = False

    def add_step(
        self,
        step_id: str,
        title: str,
        total: int = None,
        insert_at: Union[None, int, str] = None,
    ):
        """Add a new step to the progress display."""
        self.state_manager.add_step(step_id, title, total, insert_at)
        if self._started:
            self._update_display()

    def add_substep(
        self,
        parent_step_id: str,
        substep_id: str,
        description: str,
        total: int = None,
        insert_at: Union[None, int, str] = None,
    ):
        """Add a new substep to a parent step."""
        self.state_manager.add_substep(
            parent_step_id, substep_id, description, total, insert_at
        )
        if self._started:
            self._update_display()

    def start_step(self, step_id: str):
        """Start/activate a specific step."""
        self.state_manager.start_step(step_id)
        if self._started:
            self._update_display()

    def update_step(self, step_id: str, progress: float, total: int = None):
        """Update the progress of a specific step."""
        self.state_manager.update_step(step_id, progress, total)
        if self._started:
            self._update_display()

    def complete_step(self, step_id: str):
        """Mark a step as completed."""
        self.state_manager.complete_step(step_id)
        if self._started:
            self._update_display()

    def fail_step(self, step_id: str, error_msg: str = None):
        """Mark a step as failed."""
        self.state_manager.fail_step(step_id, error_msg)
        if self._started:
            self._update_display()

    def start_substep(self, parent_step_id: str, substep_id: str):
        """Start/activate a specific substep."""
        self.state_manager.start_substep(parent_step_id, substep_id)
        if self._started:
            self._update_display()

    def update_substep(
        self, parent_step_id: str, substep_id: str, progress: int, total: int = None
    ):
        """Update the progress of a specific substep."""
        self.state_manager.update_substep(parent_step_id, substep_id, progress, total)
        if self._started:
            self._update_display()

    def complete_substep(self, parent_step_id: str, substep_id: str):
        """Mark a substep as completed."""
        self.state_manager.complete_substep(parent_step_id, substep_id)
        if self._started:
            self._update_display()

    def fail_substep(self, parent_step_id: str, substep_id: str, error_msg: str = None):
        """Mark a substep as failed."""
        self.state_manager.fail_substep(parent_step_id, substep_id, error_msg)
        if self._started:
            self._update_display()

    def _update_display(self):
        """Update the display with current progress state."""
        if self._started and self.display:
            table = self.state_manager.build_progress_table()
            self.display.update_table(table)

    # Lifecycle management
    def start(self):
        """Start the progress display."""
        if not self._started:
            self._started = True
            self.display = TextualInlineProgressDisplay(self.title)
            self.display.start()
            self._update_display()

    def finish(self):
        """Finish and cleanup the progress display."""
        if not self._started:
            return

        self._started = False

        if self.display:
            self.display.stop()
            self.display = None

        time.sleep(0.1)


    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None and self.memory_manager is not None:
            try:
                self.display_memory_summary()
            except Exception:
                pass

        if exc_type is KeyboardInterrupt:
            try:
                self.finish()
            except Exception:
                pass
        else:
            self.finish()

    # API compatibility properties - delegate to state manager
    @property
    def steps(self) -> Dict[str, dict]:
        """Access to steps for backward compatibility."""
        return self.state_manager.steps

    @property
    def substeps(self) -> Dict[str, Dict[str, dict]]:
        """Access to substeps for backward compatibility."""
        return self.state_manager.substeps

    @property
    def step_order(self) -> List[str]:
        """Access to step order for backward compatibility."""
        return self.state_manager.step_order

    @property
    def active_step(self) -> Optional[str]:
        """Access to active step for backward compatibility."""
        return self.state_manager.active_step

    @property
    def active_substeps(self) -> Dict[str, Optional[str]]:
        """Access to active substeps for backward compatibility."""
        return self.state_manager.active_substeps

    @property
    def SYMBOLS(self) -> Dict[str, str]:
        """Access to symbols for backward compatibility."""
        return self.state_manager.SYMBOLS

    # Additional compatibility properties for tests
    @property
    def live(self):
        """Live display object for backward compatibility."""
        return None

    @property
    def table(self):
        """Current progress table for backward compatibility."""
        return self.state_manager.build_progress_table()

    def _rebuild_table(self):
        """Rebuild table for backward compatibility."""
        pass

    def refresh_display(self):
        """Refresh the display manually."""
        if self._started:
            self._update_display()

    @property
    def console(self):
        """Rich Console instance for direct printing."""
        if self.display and self.display.console:
            return self.display.console
        if not hasattr(self, "_console"):
            from rich.console import Console
            self._console = Console()
        return self._console

    # Memory integration methods
    def update_step_with_memory(
        self, step_id: str, current: int, memory_context: str = ""
    ) -> None:
        """Update progress step with current memory usage information."""
        if self.memory_manager is None:
            self.update_step(step_id, current)
            return

        # Get current memory stats
        try:
            memory_stats = self.memory_manager.get_current_memory_usage()
        except Exception as e:
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

        try:
            if self.memory_manager.should_trigger_gc():
                cleanup_stats = self.memory_manager.enhanced_gc_cleanup()
                if cleanup_stats["memory_freed_mb"] > 50:  # Significant cleanup
                    console = Console()
                    console.print(
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
        self, pressure_level: "MemoryPressureLevel", memory_stats: dict, context: str
    ):
        """Display memory pressure warning with context."""
        current_time = time.time()

        # Rate limit warnings to avoid spam (minimum 30 seconds between warnings)
        if (
            self.last_memory_warning is not None
            and current_time - self.last_memory_warning < 30
        ):
            return

        self.last_memory_warning = current_time

        # Create warning message
        console = Console()

        rss_mb = memory_stats.get("rss_mb", "unknown")
        available_mb = memory_stats.get("available_mb", "unknown")
        pressure_level_str = pressure_level.value.upper()

        warning_color = "yellow" if pressure_level.name == "HIGH" else "red"

        warning_text = (
            f"[{warning_color}]Memory Pressure: {pressure_level_str}[/{warning_color}]\n"
            f"Current usage: {rss_mb}MB | Available: {available_mb}MB"
        )

        if context:
            warning_text += f"\nContext: {context}"

        warning_panel = Panel(
            warning_text,
            title="⚠️ Memory Alert",
            border_style=warning_color,
        )

        console.print(warning_panel)

    def display_memory_summary(self):
        """Display memory usage summary at the end of analysis."""
        if self.memory_manager is None:
            return

        try:
            final_memory = self.memory_manager.get_current_memory_usage()
            memory_trend = self.memory_manager.get_memory_trend()
            console = Console()

            summary_text = (
                f"Analysis completed successfully!\n"
                f"Peak memory usage: {final_memory.get('peak_rss_mb', 'unknown')}MB\n"
                f"Final memory usage: {final_memory.get('rss_mb', 'unknown')}MB\n"
                f"Available memory: {final_memory.get('available_mb', 'unknown')}MB\n"
                f"Memory trend: {memory_trend}\n"
                f"Final pressure level: {final_memory['pressure_level']}"
            )

            summary_panel = Panel(
                summary_text,
                title="Memory Summary",
                border_style="green",
            )
            console.print(summary_panel)

        except Exception as e:
            from app.logger import get_logger

            logger = get_logger(__name__)
            logger.warning("Failed to display memory summary", extra={"error": str(e)})


