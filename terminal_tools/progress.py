import sys
import threading
import time
from multiprocessing import Event, Manager, Process, Value

_spinner_frames = [
    "▁",
    "▁",
    "▂",
    "▂",
    "▃",
    "▃",
    "▂",
    "▂",
    "▁",  # bouncy bouncy
    "▁",
    "▂",
    "▃",
    "▄",
    "▅",
    "▆",
    "▇",
    "█",
    "▇",
    "▆",
    "▅",
    "▄",
    "▃",
    "▂",
]


class ProgressReporter:
    def __init__(self, title: str):
        self.title = title
        self.progress = Value("d", -1)
        self.done_text = Manager().dict()
        self.process = Process(target=self._run)
        self.done_event = Event()
        self.spinner_frame_index = 0
        self.last_output_length = 0
        self._start_time = None
        self._last_update = None

    def start(self):
        self._start_time = time.time()
        self.process.start()

    def update(self, value: float):
        with self.progress.get_lock():
            self.progress.value = max(min(value, 1), 0)
        self._last_update = time.time()

    def finish(self, done_text: str = "Done!"):
        self.done_text["done"] = done_text
        self.done_event.set()
        self.process.join()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.finish()

    def _run(self):
        try:
            while not self.done_event.is_set():
                with self.progress.get_lock():
                    current_progress = self.progress.value
                self.spinner_frame_index = (self.spinner_frame_index + 1) % len(
                    _spinner_frames
                )
                progress_text = (
                    f"{current_progress * 100:.2f}%" if current_progress >= 0 else "..."
                )
                self._draw(progress_text)
                time.sleep(0.1)
            self._draw(self.done_text.get("done", "Done!"), "✅")
        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _draw(self, text: str, override_spinner_frame: str = None):
        output = (
            f"{override_spinner_frame or _spinner_frames[self.spinner_frame_index]} "
            f"{self.title} {text}"
        )
        output_with_spaces = output.ljust(self.last_output_length)
        sys.stdout.write("\r" + output_with_spaces)
        sys.stdout.flush()
        self.last_output_length = len(output)


class RichProgressManager:
    """Rich-based multi-step progress manager with visual indicators and progress bars.

    Manages multiple progress steps simultaneously with visual state indicators
    and progress bars for the currently active step. Uses Rich library components
    for enhanced terminal display with better formatting and responsive layout.

    Step states:
    - pending (⏸): Not yet started
    - active (⏳): Currently running with progress bar
    - completed (✓): Successfully finished
    - failed (❌): Failed with optional error message

    Example:
        with RichProgressManager("N-gram Analysis Progress") as manager:
            manager.add_step("preprocess", "Preprocessing and filtering messages", 1000)
            manager.add_step("tokenize", "Tokenizing text data", 500)
            manager.add_step("ngrams", "Generating n-grams", 200)

            manager.start_step("preprocess")
            for i in range(1000):
                manager.update_step("preprocess", i + 1)
            manager.complete_step("preprocess")

            manager.start_step("tokenize")
            # ... etc
    """

    def __init__(self, title: str):
        """Initialize the rich progress manager.

        Args:
            title: The overall title for the progress checklist
        """
        from rich.console import Console
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
            TimeRemainingColumn,
        )

        self.title = title
        self.steps = {}  # step_id -> step_info dict
        self.substeps = {}  # step_id -> {substep_id -> substep_info} dict
        self.step_order = []  # ordered list of step_ids
        self.active_step = None
        self.active_substeps = {}  # step_id -> active_substep_id mapping
        self._started = False

        # Rich components - use a single console and progress instance
        self.console = Console()
        self.live = None

        # Create custom progress with appropriate columns for hierarchical display
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )

        # Rich task management - use Rich's native task IDs
        self.rich_task_ids = {}  # step_id -> Rich TaskID mapping
        self.rich_substep_task_ids = {}  # (step_id, substep_id) -> Rich TaskID mapping

        # State symbols
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
        }
        self.step_order.append(step_id)

        # Create Rich progress task if total is specified
        if total is not None:
            task_id = self.progress.add_task(
                description=title,
                total=total,
                visible=False,  # Will show when step becomes active
                start=False,  # Timer starts when step is activated
            )
            self.rich_task_ids[step_id] = task_id

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

        # Create Rich progress task if total is specified
        if total is not None:
            task_id = self.progress.add_task(
                description=f"  └─ {description}",  # Indent substeps visually
                total=total,
                visible=False,  # Will show when substep becomes active
                start=False,  # Timer starts when substep is activated
            )
            self.rich_substep_task_ids[(parent_step_id, substep_id)] = task_id

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

        # Make sure parent step is active (allow concurrent active steps for hierarchical usage)
        if self.steps[parent_step_id]["state"] != "active":
            # Set parent step as active without disrupting other active steps
            # This change supports concurrent active steps when using hierarchical features
            step_info = self.steps[parent_step_id]
            step_info["state"] = "active"

            # Make Rich progress task visible and start it if it exists
            if parent_step_id in self.rich_task_ids:
                task_id = self.rich_task_ids[parent_step_id]
                self.progress.update(task_id, visible=True)
                self.progress.start_task(task_id)

            # Only update active_step if there isn't one already (maintain backward compatibility)
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

        # Make Rich progress task visible and start it if it exists
        task_key = (parent_step_id, substep_id)
        if task_key in self.rich_substep_task_ids:
            task_id = self.rich_substep_task_ids[task_key]
            self.progress.update(task_id, visible=True)
            self.progress.start_task(task_id)

        # Update display to show substep activation
        self._update_display()

    def update_substep(self, parent_step_id: str, substep_id: str, progress: int):
        """Update the progress of a specific substep.

        Args:
            parent_step_id: ID of the parent step
            substep_id: ID of the substep to update
            progress: Current progress value
        """
        # Validate inputs
        if not isinstance(parent_step_id, str) or not parent_step_id:
            raise ValueError(
                f"Invalid parent_step_id: must be a non-empty string, got {parent_step_id!r}"
            )

        if not isinstance(substep_id, str) or not substep_id:
            raise ValueError(
                f"Invalid substep_id: must be a non-empty string, got {substep_id!r}"
            )

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

        # Validate progress value type and bounds
        if not isinstance(progress, (int, float)):
            raise TypeError(
                f"Progress must be a number, got {type(progress).__name__}: {progress!r}"
            )

        progress = int(progress)
        if progress < 0:
            raise ValueError(f"Progress cannot be negative, got {progress}")

        # Check against total if specified
        if substep_info["total"] is not None:
            if progress > substep_info["total"]:
                raise ValueError(
                    f"Progress {progress} exceeds total {substep_info['total']} for substep '{parent_step_id}.{substep_id}'"
                )

        # Update substep progress
        substep_info["progress"] = progress

        # Update Rich progress task if it exists
        task_key = (parent_step_id, substep_id)
        if task_key in self.rich_substep_task_ids:
            task_id = self.rich_substep_task_ids[task_key]
            self.progress.update(task_id, completed=progress)

        # Update parent step progress based on substep completion
        self._update_parent_progress(parent_step_id)

        # Update display to show substep progress
        self._update_display()

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

            # Update and hide Rich progress task
            task_key = (parent_step_id, substep_id)
            if task_key in self.rich_substep_task_ids:
                task_id = self.rich_substep_task_ids[task_key]
                self.progress.update(task_id, completed=substep_info["total"])
                self.progress.stop_task(task_id)
                self.progress.update(task_id, visible=False)

        # Clear active substep if this was the active substep
        if (
            parent_step_id in self.active_substeps
            and self.active_substeps[parent_step_id] == substep_id
        ):
            self.active_substeps[parent_step_id] = None

        # Update parent step progress
        self._update_parent_progress(parent_step_id)

        # Update display to show substep completion
        self._update_display()

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

        # Hide and stop Rich progress task if it exists
        task_key = (parent_step_id, substep_id)
        if task_key in self.rich_substep_task_ids:
            task_id = self.rich_substep_task_ids[task_key]
            self.progress.stop_task(task_id)
            self.progress.update(task_id, visible=False)

        # Clear active substep if this was the active substep
        if (
            parent_step_id in self.active_substeps
            and self.active_substeps[parent_step_id] == substep_id
        ):
            self.active_substeps[parent_step_id] = None

        # Update display to show substep failure
        self._update_display()

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

        # Update parent step progress (this affects display but not Rich task)
        if total_substeps > 0:
            parent_progress_percent = (completed_substeps / total_substeps) * 100
            self.steps[parent_step_id]["substep_progress"] = parent_progress_percent

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

        # Make Rich progress task visible and start it if it exists
        if step_id in self.rich_task_ids:
            task_id = self.rich_task_ids[step_id]
            self.progress.update(task_id, visible=True)
            self.progress.start_task(task_id)

        # Update display to show new state
        self._update_display()

    def update_step(self, step_id: str, progress: float):
        """Update the progress of a specific step.

        Args:
            step_id: ID of the step to update
            progress: Current progress value
        """
        # Validate step_id exists
        if not isinstance(step_id, str) or not step_id:
            raise ValueError(
                f"Invalid step_id: must be a non-empty string, got {step_id!r}"
            )

        if step_id not in self.steps:
            raise ValueError(
                f"Step '{step_id}' not found. Available steps: {list(self.steps.keys())}"
            )

        step_info = self.steps[step_id]

        # Validate progress value type and bounds
        if not isinstance(progress, (int, float)):
            raise TypeError(
                f"Progress must be a number, got {type(progress).__name__}: {progress!r}"
            )

        # Keep as float for precise progress tracking
        progress = float(progress)

        # Validate progress bounds
        if progress < 0:
            raise ValueError(f"Progress cannot be negative, got {progress}")

        # Check against total if specified
        if step_info["total"] is not None:
            if progress > step_info["total"]:
                raise ValueError(
                    f"Progress {progress} exceeds total {step_info['total']} for step '{step_id}'"
                )

        # Update step progress in our tracking
        step_info["progress"] = progress

        # Update Rich progress task if it exists
        if step_id in self.rich_task_ids:
            task_id = self.rich_task_ids[step_id]
            self.progress.update(task_id, completed=progress)

        # Update display to show progress changes
        self._update_display()

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

            # Update and hide Rich progress task
            if step_id in self.rich_task_ids:
                task_id = self.rich_task_ids[step_id]
                self.progress.update(task_id, completed=step_info["total"])
                self.progress.stop_task(task_id)
                self.progress.update(task_id, visible=False)

        # Clear active step if this was the active step
        if step_id == self.active_step:
            self.active_step = None

        # Update display to show completion
        self._update_display()

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

        # Hide and stop Rich progress task if it exists
        if step_id in self.rich_task_ids:
            task_id = self.rich_task_ids[step_id]
            self.progress.stop_task(task_id)
            self.progress.update(task_id, visible=False)

        # Clear active step if this was the active step
        if step_id == self.active_step:
            self.active_step = None

        # Update display to show failure
        self._update_display()

    def start(self):
        """Start the checklist display."""
        if self._started:
            return

        from rich.live import Live

        self._started = True

        # Initialize Live display with dynamic content
        self.live = Live(
            self._create_display_group(),
            console=self.console,
            refresh_per_second=40,
            auto_refresh=True,
        )
        self.live.start()

    def _update_display(self):
        """Update the live display with current progress."""
        if self._started and self.live:
            self.live.update(self._create_display_group())

    def finish(self):
        """Finish the checklist display and cleanup."""
        if not self._started:
            return

        self._started = False
        # Final display update to show final state
        if self.live:
            self.live.stop()
            self.live = None

    def _create_display_group(self):
        """Create the Rich renderable group for the hierarchical progress display."""
        from rich.console import Group
        from rich.table import Table
        from rich.text import Text

        # Create a table for step overview
        steps_table = Table(
            show_header=False, show_edge=False, pad_edge=False, box=None
        )
        steps_table.add_column("Status", style="bold", width=3, justify="center")
        steps_table.add_column("Step", ratio=1)

        # Add each step to the table
        for step_id in self.step_order:
            step_info = self.steps[step_id]
            symbol = self.SYMBOLS[step_info["state"]]
            title = step_info["title"]

            # Create step text with progress if available
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

            # Add substep progress if available
            if step_id in self.substeps and self.substeps[step_id]:
                substeps = self.substeps[step_id]
                completed_substeps = sum(
                    1 for s in substeps.values() if s["state"] == "completed"
                )
                total_substeps = len(substeps)
                if step_info["state"] == "active" and total_substeps > 0:
                    substep_percent = (completed_substeps / total_substeps) * 100
                    step_text += f" [{substep_percent:.0f}% substeps]"

            # Add error message for failed steps
            if step_info["state"] == "failed" and step_info["error_msg"]:
                step_text += f" - [red]{step_info['error_msg']}[/red]"

            # Style based on state
            if step_info["state"] == "completed":
                step_text = f"[green]{step_text}[/green]"
            elif step_info["state"] == "failed":
                step_text = f"[red]{step_text}[/red]"
            elif step_info["state"] == "active":
                step_text = f"[yellow]{step_text}[/yellow]"
            else:  # pending
                step_text = f"[dim white]{step_text}[/dim white]"

            steps_table.add_row(symbol, step_text)

            # Add substeps
            if step_id in self.substeps:
                for _substep_id, substep_info in self.substeps[step_id].items():
                    substep_description = substep_info["description"]

                    # Create substep text with progress
                    if substep_info["total"] is not None and substep_info["state"] in [
                        "active",
                        "completed",
                    ]:
                        substep_percentage = (
                            (substep_info["progress"] / substep_info["total"]) * 100
                            if substep_info["total"] > 0
                            else 0
                        )
                        substep_text = f"  └─ {substep_description} ({substep_info['progress']}/{substep_info['total']} - {substep_percentage:.0f}%)"
                    else:
                        substep_text = f"  └─ {substep_description}"

                    # Add error message for failed substeps
                    if substep_info["state"] == "failed" and substep_info["error_msg"]:
                        substep_text += f" - [red]{substep_info['error_msg']}[/red]"

                    # Style substeps
                    if substep_info["state"] == "completed":
                        substep_text = f"[green]{substep_text}[/green]"
                    elif substep_info["state"] == "failed":
                        substep_text = f"[red]{substep_text}[/red]"
                    elif substep_info["state"] == "active":
                        substep_text = f"[yellow]{substep_text}[/yellow]"
                    else:  # pending
                        substep_text = f"[dim white]{substep_text}[/dim white]"

                    steps_table.add_row("", substep_text)

        # Create the display group
        content_parts = []

        # Add title
        title_text = Text(self.title, style="bold blue")
        content_parts.append(title_text)
        content_parts.append("")  # Empty line
        content_parts.append(steps_table)

        # Add progress bar for active tasks
        has_active_progress = (
            self.active_step
            and self.active_step in self.rich_task_ids
            and self.steps[self.active_step]["state"] == "active"
        )

        # Check for active substep progress
        if not has_active_progress:
            for parent_step_id, active_substep_id in self.active_substeps.items():
                if (
                    active_substep_id
                    and parent_step_id in self.substeps
                    and active_substep_id in self.substeps[parent_step_id]
                    and self.substeps[parent_step_id][active_substep_id]["state"]
                    == "active"
                    and (parent_step_id, active_substep_id)
                    in self.rich_substep_task_ids
                ):
                    has_active_progress = True
                    break

        if has_active_progress:
            content_parts.append("")  # Empty line
            content_parts.append(self.progress)

        return Group(*content_parts)

    def __enter__(self):
        """Context manager entry - starts the checklist display."""
        self.start()
        return self

    def __exit__(self, exc_type, _exc_value, _traceback):
        """Context manager exit - finishes the checklist display."""
        # Handle KeyboardInterrupt specially to ensure clean terminal state
        if exc_type is KeyboardInterrupt:
            # Stop Rich display immediately and cleanly
            try:
                if self.live and self._started:
                    self.live.stop()
                    self.live = None
                # Clear the terminal to prevent repeated output
                self.console.clear()
                self._started = False
            except Exception:
                # If cleanup fails, at least try to restore terminal
                try:
                    self.console.clear()
                except Exception:
                    pass
        else:
            # Normal cleanup for other exceptions or successful completion
            self.finish()


# Create an alias for backward compatibility
ChecklistProgressManager = RichProgressManager
