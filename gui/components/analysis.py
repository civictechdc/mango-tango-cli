from nicegui import ui

from analyzer_interface import AnalyzerParam, IntegerParam, ParamValue, TimeBinningValue


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
            with ui.row().classes("items-center gap-4"):
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
        default_value: int | None,
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
        self, param: AnalyzerParam, default_value: TimeBinningValue | None
    ):
        """Build time binning parameter control."""
        with ui.row().classes("gap-2"):
            # Unit selector
            unit_select = ui.select(
                {
                    "year": "Year",
                    "month": "Month",
                    "week": "Week",
                    "day": "Day",
                    "hour": "Hour",
                    "minute": "Minute",
                    "second": "Second",
                },
                label="Pick a time unit",
                value=default_value.unit if default_value else "day",
            ).classes("w-32")

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
            ).classes("w-32")

        self.param_widgets[param.id] = ("time_binning", unit_select, amount_input)

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
