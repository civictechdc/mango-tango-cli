"""
Memory-aware progress manager that integrates real-time memory monitoring
with hierarchical progress reporting.
"""

import time
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from app.utils import MemoryManager, MemoryPressureLevel
from terminal_tools.progress import RichProgressManager


class MemoryAwareProgressManager(RichProgressManager):
    """
    Extended progress manager that includes real-time memory usage statistics.

    Features:
    - Memory usage displayed in progress bars
    - Memory pressure warnings in UI
    - Automatic fallback suggestions when memory limits approached
    - Memory trend analysis and predictions
    """

    def __init__(self, description: str, memory_manager: MemoryManager):
        super().__init__(description)
        self.memory_manager = memory_manager
        self.console = Console()
        self.last_memory_warning = None

    def update_step_with_memory(
        self, step_id: str, current: int, memory_context: str = ""
    ) -> None:
        """Update progress step with current memory usage information."""
        # Get current memory stats
        memory_stats = self.memory_manager.get_current_memory_usage()

        # Update the progress step
        self.update_step(step_id, current)

        # Check for memory pressure and warn if necessary
        pressure_level = MemoryPressureLevel(memory_stats["pressure_level"])

        if pressure_level in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
            self._display_memory_warning(pressure_level, memory_stats, memory_context)

        # Trigger GC if needed
        if self.memory_manager.should_trigger_gc():
            cleanup_stats = self.memory_manager.enhanced_gc_cleanup()
            if cleanup_stats["memory_freed_mb"] > 50:  # Significant cleanup
                self.console.print(
                    f"[green]Freed {cleanup_stats['memory_freed_mb']:.1f}MB memory[/green]"
                )

    def _display_memory_warning(
        self, pressure_level: MemoryPressureLevel, memory_stats: Dict, context: str
    ) -> None:
        """Display memory pressure warning to user."""
        # Avoid spam - only show warning every 30 seconds
        current_time = time.time()
        if self.last_memory_warning and current_time - self.last_memory_warning < 30:
            return

        self.last_memory_warning = current_time

        memory_mb = memory_stats["rss_mb"]
        pressure_color = {
            MemoryPressureLevel.HIGH: "yellow",
            MemoryPressureLevel.CRITICAL: "red",
        }[pressure_level]

        warning_text = Text()
        warning_text.append(f"Memory Usage: {memory_mb:.1f}MB ", style=pressure_color)
        warning_text.append(
            f"({memory_stats['process_memory_percent']:.1f}% of limit)",
            style=pressure_color,
        )

        if context:
            warning_text.append(f" during {context}", style="dim")

        # Suggest actions based on pressure level
        if pressure_level == MemoryPressureLevel.CRITICAL:
            warning_text.append(
                "\n⚠️  Critical memory pressure - switching to disk-based processing",
                style="red bold",
            )
        elif pressure_level == MemoryPressureLevel.HIGH:
            warning_text.append(
                "\n⚠️  High memory pressure - reducing chunk sizes", style="yellow"
            )

        panel = Panel(warning_text, title="Memory Monitor", border_style=pressure_color)
        self.console.print(panel)

    def display_memory_summary(self) -> None:
        """Display final memory usage summary."""
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
