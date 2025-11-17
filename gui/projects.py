from nicegui import ui

from gui.base import GuiSession


class ManageProjectsDialog(ui.dialog):
    """
    Dialog for managing projects (view and delete).

    Displays a list of projects in a grid and allows users to select
    and delete projects.
    """

    def __init__(self, session: GuiSession) -> None:
        """
        Initialize the Manage Projects dialog.

        Args:
            session: GUI session containing app context and state
        """
        super().__init__()

        self.session = session
        self.project_contexts = self.session.app.list_projects()

        # Build dialog UI
        with self, ui.card().classes("w-full"):
            # Dialog title
            ui.label("Manage Projects").classes("text-h6 q-mb-md")

            # Check if there are projects to display
            if not self.project_contexts:
                ui.label("No projects found").classes("text-grey q-mb-md")
            else:
                # Projects grid
                self.grid = ui.aggrid(
                    {
                        "columnDefs": [
                            {"headerName": "Project Name", "field": "project_name"},
                            {"headerName": "Project ID", "field": "project_id"},
                        ],
                        "rowData": [
                            {
                                "project_name": proj.display_name,
                                "project_id": proj.id,
                            }
                            for proj in self.project_contexts
                        ],
                        "rowSelection": {"mode": "singleRow"},
                    },
                    theme="quartz",
                ).classes("w-full h-96")

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button(
                    "Cancel",
                    on_click=self._handle_cancel,
                    color="secondary",
                ).props("outline")

                ui.button("Delete", on_click=self._handle_delete, color="primary")

    async def _handle_delete(self):
        """Handle delete button click - show confirmation then delete selected project."""
        # Get selected row
        selected_rows = await self.grid.get_selected_rows()

        if not selected_rows:
            ui.notify("Please select a project to delete", type="warning")
            return

        selected_row = selected_rows[0]
        project_id = selected_row["project_id"]
        project_name = selected_row["project_name"]

        # Show confirmation dialog
        confirmed = await self._show_delete_confirmation(project_name, project_id)

        if not confirmed:
            return

        try:
            # Find the project context or fetch None if not found
            project_context = next(
                (p for p in self.project_contexts if p.id == project_id), None
            )

            if not project_context:
                ui.notify("Project not found", type="negative")
                return

            # Delete the project via ProjectContext API
            project_context.delete()

            # Close dialog and return information for notification pop up
            self.submit(
                (project_context.is_deleted, project_name, project_id)
            )  # Return True to indicate changes were made

        except Exception as e:
            ui.notify(f"Error deleting project: {str(e)}", type="negative")

    async def _show_delete_confirmation(self, project_name: str, project_id) -> bool:
        """
        Show confirmation dialog before deleting a project.

        Args:
            project_name: Name of the project to delete

        Returns:
            True if user confirmed deletion, False otherwise
        """

        with ui.dialog() as dialog, ui.card():
            ui.label(
                f"Are you sure you want to delete project '{project_name}' (ID: {project_id})?"
            ).classes("q-mb-md")
            ui.label("This action cannot be undone.").classes("text-warning q-mb-lg")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancel",
                    on_click=lambda: dialog.submit(False),
                    color="secondary",
                ).props("outline")

                ui.button(
                    "Delete", on_click=lambda: dialog.submit(True), color="negative"
                )

        return await dialog

    async def _handle_cancel(self):
        """Handle cancel button click - close dialog without changes."""
        self.submit(False)  # Return False to indicate no changes
