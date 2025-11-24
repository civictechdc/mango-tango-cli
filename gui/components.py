from typing import Optional

from nicegui import ui

from analyzer_interface import AnalyzerParam, IntegerParam, ParamValue, TimeBinningValue

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
        self.selected_text = None

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
        self.selected_text = button.text

    def get_selected(self) -> ToggleButton | None:
        """Get the currently selected button."""
        return self.selected

    def get_selected_text(self) -> str | None:
        """Get the text of the currently selected button."""
        return self.selected.text if self.selected else None


class AnalysisParamsCard:
    """
    Card component for configuring analyzer parameters.

    Displays interactive controls for modifying analysis parameters
    similar to ImportOptionsDialog but as a card component instead of a dialog.
    """

    def __init__(
        self,
        params: list[AnalyzerParam],
        default_values: dict[str, ParamValue],
    ):
        """
        Initialize the analysis parameters card.

        Args:
            params: List of analyzer parameter specifications
            default_values: Dictionary of default parameter values
        """
        self.params = params
        self.default_values = default_values
        self.param_widgets: dict[str, tuple] = {}

        # Build the card UI
        self._build_card()

    def _build_card(self):
        """Build the parameter configuration card."""
        with ui.card().classes("w-full"):

            if not self.params:
                ui.label("This analyzer has no configurable parameters.").classes(
                    "text-grey-7"
                )
                return

            # Build controls for each parameter
            for param in self.params:
                self._build_param_control(param)

    def _build_param_control(self, param: AnalyzerParam):
        """Build UI control for a single parameter."""
        with ui.column().classes("w-full mb-2"):
            # Parameter label with description
            with ui.row().classes("items-center gap-2"):
                ui.label(param.print_name).classes("text-base font-bold")
                if param.description:
                    with ui.icon("info").classes("text-grey-6 cursor-pointer"):
                        ui.tooltip(param.description)

                # Parameter input control based on type
                param_type = param.type
                default_value = self.default_values.get(param.id)

                if param_type.type == "integer":
                    self._build_integer_control(param, param_type, default_value)
                elif param_type.type == "time_binning":
                    self._build_time_binning_control(param, default_value)

    def _build_integer_control(
        self,
        param: AnalyzerParam,
        param_type: IntegerParam,
        default_value: Optional[int],
    ):
        """Build integer parameter control."""
        number_input = ui.number(
            label=f"Enter value between {param_type.min} and {param_type.max}",
            value=default_value if default_value is not None else param_type.min,
            min=param_type.min,
            max=param_type.max,
            step=1,
            precision=0,
            validation={
                f"Must be at least {param_type.min}": lambda v: v >= param_type.min,
                f"Must be at most {param_type.max}": lambda v: v <= param_type.max,
            },
        ).classes("w-40")

        self.param_widgets[param.id] = ("integer", number_input)

    def _build_time_binning_control(
        self, param: AnalyzerParam, default_value: Optional[TimeBinningValue]
    ):
        """Build time binning parameter control."""
        with ui.column().classes("gap-2"):
            # Unit selector
            unit_toggle = ui.toggle(
                {
                    "year": "Year",
                    "month": "Month",
                    "week": "Week",
                    "day": "Day",
                    "hour": "Hour",
                    "minute": "Minute",
                    "second": "Second",
                },
                value=default_value.unit if default_value else "day",
            )

            # Amount input
            amount_input = ui.number(
                label="How many?",
                value=default_value.amount if default_value else 1,
                min=1,
                max=1000,
                step=1,
                precision=0,
                validation={
                    "Must be at least 1": lambda v: v >= 1,
                    "Cannot exceed 1000": lambda v: v <= 1000,
                },
            ).classes("w-48")

            self.param_widgets[param.id] = ("time_binning", unit_toggle, amount_input)

    def get_param_values(self) -> dict[str, ParamValue]:
        """
        Retrieve current parameter values from the UI controls.

        Returns:
            Dictionary mapping parameter IDs to their values
        """
        param_values = {}

        for param_id, widgets in self.param_widgets.items():
            param_type = widgets[0]

            if param_type == "integer":
                number_input = widgets[1]
                param_values[param_id] = int(number_input.value)

            elif param_type == "time_binning":
                unit_toggle = widgets[1]
                amount_input = widgets[2]
                param_values[param_id] = TimeBinningValue(
                    unit=unit_toggle.value, amount=int(amount_input.value)
                )

        return param_values
