from nicegui import ui

MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
MANGO_ORANGE_LIGHT = "#f9bc30"
ACCENT = "white"


class ToggleButton(ui.button):

    def __init__(self, *args, group=None, **kwargs) -> None:
        self._state = False
        self._group = group
        super().__init__(*args, **kwargs)
        self.on("click", self._handle_click)

    def _handle_click(self) -> None:
        """Handle button click, coordinating with group if present."""
        if self._group:
            self._group.select(self)
        else:
            self.toggle()

    def toggle(self) -> None:
        """Toggle the button state."""
        self._state = not self._state
        self.update()

    def set_active(self, active: bool) -> None:
        """Set the button state externally."""
        self._state = active
        self.update()

    def update(self) -> None:
        if self._group:
            # Group mode: green when active, grey when inactive
            self.props(f'color={"primary" if self._state else "grey"}')
        else:
            # Standalone mode: orange/red toggle
            self.props(f'color={"primary" if self._state else "red"}')
        super().update()


class ToggleButtonGroup:
    """Manages a group of toggle buttons with mutual exclusivity."""

    def __init__(self):
        self.buttons = []
        self.selected = None

    def add_button(self, text: str, **kwargs) -> ToggleButton:
        """Add a button to the group."""
        btn = ToggleButton(text, group=self, **kwargs)
        self.buttons.append(btn)
        return btn

    def select(self, button: ToggleButton) -> None:
        """Select a button, deselecting all others."""
        for btn in self.buttons:
            btn.set_active(False)
        button.set_active(True)
        self.selected = button

    def get_selected(self) -> ToggleButton | None:
        """Get the currently selected button."""
        return self.selected

    def get_selected_text(self) -> str | None:
        """Get the text of the currently selected button."""
        return self.selected.text if self.selected else None
