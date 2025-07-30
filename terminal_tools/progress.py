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


class AdvancedProgressReporter:
    """Advanced progress reporter using tqdm for rich progress displays.

    Provides detailed progress tracking with ETA calculation, processing speed,
    and visual progress bars. Can be used as a context manager.
    """

    def __init__(self, title: str, total: int):
        """Initialize the progress reporter.

        Args:
            title: The title/description for the progress bar
            total: The total number of items to process
        """
        self.title = title
        self.total = total
        self._pbar = None

    def start(self) -> None:
        """Start the progress bar display."""
        import tqdm

        self._pbar = tqdm.tqdm(
            total=self.total,
            desc=self.title,
            unit="items",
            unit_scale=True,
            dynamic_ncols=True,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )

    def update(self, n: int = 1) -> None:
        """Update progress by n items.

        Args:
            n: Number of items processed (default: 1)
        """
        if self._pbar is not None:
            self._pbar.update(n)

    def set_progress(self, processed: int) -> None:
        """Set the absolute progress to a specific number of processed items.

        Args:
            processed: Total number of items processed so far
        """
        if self._pbar is not None:
            # Calculate the difference from current position
            current = getattr(self._pbar, "n", 0)
            diff = processed - current
            if diff > 0:
                self._pbar.update(diff)
            elif diff < 0:
                # If we need to go backwards, reset and update to new position
                self._pbar.reset()
                self._pbar.update(processed)

    def finish(self, done_text: str = "Done!") -> None:
        """Finish the progress bar and display completion message.

        Args:
            done_text: Text to display when finished (default: "Done!")
        """
        if self._pbar is not None:
            # Ensure progress bar is at 100%
            if self._pbar.n < self._pbar.total:
                self._pbar.update(self._pbar.total - self._pbar.n)

            self._pbar.set_description(done_text)
            self._pbar.close()
            self._pbar = None

    def __enter__(self):
        """Context manager entry - starts the progress bar."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit - finishes the progress bar."""
        self.finish()


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
        import threading

        from rich.console import Console
        from rich.live import Live
        from rich.panel import Panel
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            SpinnerColumn,
            TaskID,
            TaskProgressColumn,
            TextColumn,
            TimeRemainingColumn,
        )
        from rich.table import Table
        from rich.text import Text

        self.title = title
        self.steps = {}  # step_id -> step_info dict
        self.substeps = {}  # step_id -> {substep_id -> substep_info} dict
        self.step_order = []  # ordered list of step_ids
        self.active_step = None
        self.active_substeps = {}  # step_id -> active_substep_id mapping
        self._started = False
        self._display_lock = threading.Lock()  # Synchronize terminal display operations

        # Rich components
        self.console = Console()
        self.live = None

        # Create custom progress with appropriate columns
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

        # Rich task management - use Rich's native task IDs instead of custom mapping
        self.rich_task_ids = {}  # step_id -> Rich TaskID mapping
        # Also track Rich task IDs for substeps
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

        # Create Rich progress task if total is specified, but keep it hidden initially
        if total is not None:
            task_id = self.progress.add_task(
                description=title,
                total=total,
                visible=False,  # Start hidden - will show when step becomes active
                start=False,  # Don't start timer until step is active
            )
            self.rich_task_ids[step_id] = task_id

        # Update display immediately if we're already started
        if self._started and self.live:
            self._update_display()

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

        # Create Rich progress task if total is specified, but keep it hidden initially
        if total is not None:
            task_id = self.progress.add_task(
                description=f"  └─ {description}",  # Indent substeps visually
                total=total,
                visible=False,  # Start hidden - will show when substep becomes active
                start=False,  # Don't start timer until substep is active
            )
            self.rich_substep_task_ids[(parent_step_id, substep_id)] = task_id

        # Update display immediately if we're already started
        if self._started and self.live:
            self._update_display()

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

        # Update display immediately
        if self._started and self.live:
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

        # Update display if started (with error handling)
        if self._started and self.live:
            try:
                self._update_display()
            except Exception as e:
                self.console.print(
                    f"[yellow]Warning: Failed to update progress display: {e}[/yellow]",
                    file=sys.stderr,
                )

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

        # Update display immediately
        if self._started and self.live:
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

        # Update display immediately
        if self._started and self.live:
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

        # Update display immediately
        if self._started and self.live:
            self._update_display()

    def update_step(self, step_id: str, progress: int):
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

        # Convert to int if it was a float
        progress = int(progress)

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

        # Update display if started (with error handling)
        if self._started and self.live:
            try:
                self._update_display()
            except Exception as e:
                self.console.print(
                    f"[yellow]Warning: Failed to update progress display: {e}[/yellow]",
                    file=sys.stderr,
                )
                # Continue execution - display issues shouldn't crash progress tracking

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

        # Update display immediately
        if self._started and self.live:
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

        # Update display immediately
        if self._started and self.live:
            self._update_display()

    def start(self):
        """Start the checklist display."""
        if self._started:
            return

        from rich.console import Group
        from rich.live import Live

        self._started = True

        # Create the display content group
        self.display_group = Group()

        # Initialize Rich Live display with the group
        self.live = Live(
            self.display_group,
            console=self.console,
            refresh_per_second=4,
            auto_refresh=True,
        )
        self.live.start()

        # Initial display update
        self._update_display()

    def finish(self):
        """Finish the checklist display and cleanup."""
        if not self._started:
            return

        # Final display update to show final state
        if self.live:
            self._update_display()
            self.live.stop()
            self.live = None

        # Add a final newline for separation
        self.console.print()
        self._started = False

    def _update_display(self):
        """Update the Rich display with current step states, substeps, and active progress."""
        with self._display_lock:
            if not self._started or not self.live:
                return

            from rich.console import Group
            from rich.panel import Panel
            from rich.table import Table
            from rich.text import Text

            # Create the main table for all steps and substeps
            steps_table = Table(
                show_header=False, show_edge=False, pad_edge=False, box=None
            )
            steps_table.add_column("Status", style="bold", width=3, justify="center")
            steps_table.add_column("Step", ratio=1)

            # Add each step and its substeps to the table
            for step_id in self.step_order:
                step_info = self.steps[step_id]
                symbol = self.SYMBOLS[step_info["state"]]
                title = step_info["title"]

                # Create the step text with potential progress info
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

                # Add substep progress information if available
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

                # Style based on state - colors help distinguish states
                if step_info["state"] == "completed":
                    step_text = f"[green]{step_text}[/green]"
                elif step_info["state"] == "failed":
                    step_text = f"[red]{step_text}[/red]"
                elif step_info["state"] == "active":
                    step_text = f"[yellow]{step_text}[/yellow]"
                else:  # pending
                    step_text = f"[dim white]{step_text}[/dim white]"

                steps_table.add_row(symbol, step_text)

                # Add substeps if they exist
                if step_id in self.substeps:
                    substeps = self.substeps[step_id]
                    for substep_id, substep_info in substeps.items():
                        substep_symbol = self.SYMBOLS[substep_info["state"]]
                        substep_description = substep_info["description"]

                        # Create substep text with progress if available
                        if substep_info["total"] is not None and substep_info[
                            "state"
                        ] in [
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
                        if (
                            substep_info["state"] == "failed"
                            and substep_info["error_msg"]
                        ):
                            substep_text += f" - [red]{substep_info['error_msg']}[/red]"

                        # Style substeps based on state
                        if substep_info["state"] == "completed":
                            substep_text = f"[green]{substep_text}[/green]"
                        elif substep_info["state"] == "failed":
                            substep_text = f"[red]{substep_text}[/red]"
                        elif substep_info["state"] == "active":
                            substep_text = f"[yellow]{substep_text}[/yellow]"
                        else:  # pending
                            substep_text = f"[dim white]{substep_text}[/dim white]"

                        steps_table.add_row(
                            "", substep_text
                        )  # Empty symbol for substeps

            # Build the content parts
            content_parts = []

            # Add title
            title_text = Text(self.title, style="bold blue")
            content_parts.append(title_text)
            content_parts.append("")  # Empty line
            content_parts.append(steps_table)

            # Add active progress bar - check both step and substep progress bars
            progress_bar_added = False

            # Check for active step with total (original logic)
            if (
                self.active_step
                and self.active_step in self.rich_task_ids
                and self.steps[self.active_step]["state"] == "active"
            ):
                step_info = self.steps[self.active_step]
                if step_info["total"] is not None:
                    content_parts.append("")  # Empty line
                    content_parts.append(self.progress)
                    progress_bar_added = True

            # Check for active substep with total (new logic)
            if not progress_bar_added:
                for parent_step_id, active_substep_id in self.active_substeps.items():
                    if (
                        active_substep_id
                        and parent_step_id in self.substeps
                        and active_substep_id in self.substeps[parent_step_id]
                    ):

                        substep_info = self.substeps[parent_step_id][active_substep_id]
                        if (
                            substep_info["state"] == "active"
                            and substep_info["total"] is not None
                            and (parent_step_id, active_substep_id)
                            in self.rich_substep_task_ids
                        ):

                            content_parts.append("")  # Empty line
                            content_parts.append(self.progress)
                            progress_bar_added = True
                            break

            # Update the display group and live display
            from rich.console import Group

            self.display_group = Group(*content_parts)
            self.live.update(self.display_group)

    def __enter__(self):
        """Context manager entry - starts the checklist display."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit - finishes the checklist display."""
        self.finish()


# Create an alias for backward compatibility
ChecklistProgressManager = RichProgressManager
