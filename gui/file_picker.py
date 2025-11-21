"""
Local file picker for NiceGUI native mode.

Allows browsing the local filesystem without tempfile overhead,
matching the terminal file selector behavior.
"""

import os
import platform
from pathlib import Path
from typing import Optional

from nicegui import events, ui

from storage.file_selector import FileSelectorStateManager


class LocalFilePicker(ui.dialog):
    """
    File picker dialog for selecting files from the local filesystem.

    Returns actual file paths (not file content), avoiding tempfile overhead
    when running in native mode.
    """

    def __init__(
        self,
        directory: str = "~",
        *,
        state: Optional[FileSelectorStateManager] = None,
        upper_limit: Optional[str] = None,
        show_hidden_files: bool = False,
        file_extensions: Optional[list[str]] = None,
    ) -> None:
        """
        Initialize the local file picker dialog.

        Args:
            directory: Starting directory path (default: home directory)
            state: FileSelectorStateManager for path persistence
            upper_limit: Optional path to restrict upward navigation
            show_hidden_files: Whether to show hidden files/folders
            file_extensions: Optional list of allowed extensions (e.g., ['.csv', '.xlsx'])
        """
        super().__init__()

        # Restore last path from state if available
        initial_dir = state and state.get_current_path()
        if initial_dir and os.path.isdir(initial_dir):
            self.path = Path(initial_dir).expanduser().resolve()
        else:
            self.path = Path(directory).expanduser().resolve()

        self.state = state
        self.show_hidden_files = show_hidden_files
        self.file_extensions = file_extensions

        # Set upper navigation limit
        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = (
                Path(directory if upper_limit == ... else upper_limit)
                .expanduser()
                .resolve()
            )

        # Build dialog UI
        with self, ui.card().classes("w-full"):
            # Current path display
            self.path_label = ui.label().classes("text-sm text-gray-600 mb-2")

            # Windows drive selector
            self.drives_toggle = None
            self._add_drives_toggle()

            # File/folder grid
            self.grid = (
                ui.aggrid(
                    {
                        "columnDefs": [
                            {"field": "name", "headerName": "Name"},
                            {
                                "field": "size",
                                "headerName": "Size",
                                "sortable": True,
                            },
                        ],
                        "rowData": [],
                        "rowSelection": {"mode": "singleRow"},
                    },
                    theme="quartz",
                    html_columns=[0],
                )
                .classes("w-full h-96")
                .on("cellDoubleClicked", self._handle_double_click)
            )

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=self._handle_cancel).props("outline")
                ui.button("Select", on_click=self._handle_select).props("color=primary")

        # Initial grid population
        self._update_grid()

    def _add_drives_toggle(self):
        """Add drive selection toggle for Windows systems."""
        if platform.system() != "Windows":
            return

        try:
            # Try using win32api if available
            import win32api

            drives = win32api.GetLogicalDriveStrings().split("\000")[:-1]
        except ImportError:
            # Fallback: detect drives manually
            from string import ascii_uppercase

            drives = [
                f"{letter}:\\"
                for letter in ascii_uppercase
                if os.path.exists(f"{letter}:\\")
            ]

        if drives:
            current_drive = os.path.splitdrive(str(self.path))[0] + "\\"
            self.drives_toggle = ui.toggle(
                drives, value=current_drive, on_change=self._handle_drive_change
            ).classes("mb-2")

    def _handle_drive_change(self):
        """Handle drive selection change on Windows."""
        if self.drives_toggle:
            self.path = Path(self.drives_toggle.value).resolve()
            self._update_grid()

    def _update_grid(self):
        """Update the grid with current directory contents."""
        self.path_label.text = f"Current path: {self.path}"

        try:
            # Get directory contents
            entries = []

            # Add parent directory entry if not at upper limit
            if self.upper_limit is None or self.path != self.upper_limit:
                entries.append(
                    {
                        "name": "⬆️ Go up to parent folder",
                        "size": "",
                        "path": str(self.path.parent),
                        "is_dir": True,
                    }
                )

            # List all items in current directory
            for item in sorted(
                self.path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
            ):
                # Skip hidden files if configured
                if not self.show_hidden_files and item.name.startswith("."):
                    continue

                is_dir = item.is_dir()

                # Filter files by extension if specified
                if not is_dir and self.file_extensions:
                    if not any(item.name.endswith(ext) for ext in self.file_extensions):
                        continue

                # Format entry
                name = f"📁 {item.name}" if is_dir else item.name
                size = ""
                if not is_dir:
                    try:
                        size_bytes = item.stat().st_size
                        size = self._format_size(size_bytes)
                    except (OSError, PermissionError):
                        size = "N/A"

                entries.append(
                    {"name": name, "size": size, "path": str(item), "is_dir": is_dir}
                )

            # Update grid
            self.grid.options["rowData"] = entries
            self.grid.update()

        except PermissionError:
            ui.notify("Permission denied for this directory", type="negative")
            # Navigate back to parent on permission error
            if self.path.parent != self.path:
                self.path = self.path.parent
                self._update_grid()

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    async def _handle_double_click(self, e: events.GenericEventArguments):
        """Handle double-click on grid row to navigate into directories."""
        row_data = e.args["data"]

        if row_data["is_dir"]:
            self.path = Path(row_data["path"]).resolve()
            self._update_grid()

    async def _handle_select(self):
        """Handle Select button click - return selected file path."""
        selected_rows = await self.grid.get_selected_rows()

        if not selected_rows:
            ui.notify("Please select a file", type="warning")
            return

        row_data = selected_rows[0]

        if row_data["is_dir"]:
            ui.notify("Please select a file, not a directory", type="warning")
            return

        # Save current directory to state
        if self.state:
            self.state.set_current_path(str(self.path))

        # Return selected file path
        selected_path = row_data["path"]
        self.submit(selected_path)

    async def _handle_cancel(self):
        """Handle Cancel button click - close dialog without selection."""
        self.submit(None)
