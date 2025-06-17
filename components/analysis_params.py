from tempfile import TemporaryDirectory

from pydantic import BaseModel

from analyzer_interface import (
    AnalyzerInterface,
    AnalyzerParam,
    IntegerParam,
    ParamValue,
    TimeBinningValue,
)
from app import ProjectContext
from context import InputColumnProvider, PrimaryAnalyzerDefaultParametersContext
from terminal_tools import print_ascii_table, prompts

from .context import ViewContext


def customize_analysis(
    context: ViewContext,
    project: ProjectContext,
    analyzer: AnalyzerInterface,
    column_mapping: dict[str, str],
) -> dict[str, ParamValue] | None:
    app = context.app
    if not analyzer.params:
        return dict()

    with TemporaryDirectory() as temp_dir:
        default_parameters_context = PrimaryAnalyzerDefaultParametersContext(
            analyzer=analyzer,
            store=app.context.storage,
            temp_dir=temp_dir,
            input_columns={
                analyzer_column_name: InputColumnProvider(
                    user_column_name=user_column_name,
                    semantic=project.column_dict[user_column_name].semantic,
                )
                for analyzer_column_name, user_column_name in column_mapping.items()
            },
        )
        analyzer_decl = app.context.suite.get_primary_analyzer(analyzer.id)
        assert analyzer_decl, f"Analyzer `{analyzer.id}` not found"

        param_values = {
            **{
                param_spec.id: static_param_default_value
                for param_spec in analyzer_decl.params
                if (static_param_default_value := param_spec.default) is not None
            },
            # Deliberately allow `None` to override here
            **analyzer_decl.default_params(default_parameters_context),
        }
        param_values = {
            param_id: param_value
            for param_id, param_value in param_values.items()
            if param_value is not None
        }

    while True:
        with context.terminal.nest("Customization"):
            param_states = [
                ParamState(
                    param_spec=param_spec,
                    value=param_values.get(param_spec.id),
                )
                for param_spec in analyzer.params
            ]

            print_ascii_table(
                [
                    [
                        param_state.param_spec.print_name,
                        print_param_value(param_state.value),
                    ]
                    for param_state in param_states
                ],
                header=["parameter name", "parameter value"],
            )

            has_all_params = all(
                (param_state.value is not None for param_state in param_states)
            )

            prompt_title = (
                "Does this look right?"
                if has_all_params
                else "The analyzer needs more information before it can run."
            )

            prompt_choices = [
                *([("Yes. Proceed.", (True, None))] if has_all_params else []),
                *[
                    (
                        (
                            f"Change {param_state.param_spec.print_name}"
                            if param_state.value
                            else f"Set {param_state.param_spec.print_name}"
                        ),
                        (False, param_state),
                    )
                    for param_state in param_states
                ],
            ]

            prompt_answer: tuple[bool, ParamState | None] | None = prompts.list_input(
                prompt_title, choices=prompt_choices
            )
            if not prompt_answer:
                return None

            proceed, param_to_edit = prompt_answer
            if proceed:
                return param_values

            with context.terminal.nest(
                f"Set {param_to_edit.param_spec.print_name}"
            ) as scope:

                def refresh():
                    scope.refresh()
                    description = param_to_edit.param_spec.description
                    if description:
                        print(f"\nHelp:\n\n{description}\n")

                refresh()
                param_value = edit_param(param_to_edit)
                if param_value is not None:
                    param_values[param_to_edit.param_spec.id] = param_value


class ParamState(BaseModel):
    param_spec: AnalyzerParam
    value: ParamValue | None


def print_param_value(value: ParamValue | None):
    if isinstance(value, TimeBinningValue):
        return value.to_human_readable_text()
    if isinstance(value, int):
        return str(value)
    if value is None:
        return "(not set)"
    raise ValueError("Unsupported parameter type")


def edit_param(state: ParamState) -> ParamValue | None:
    param_type = state.param_spec.type
    current_value = state.value
    if param_type.type == "integer":
        return edit_int_param(param_type, current_value)
    if param_type.type == "time_binning":
        return edit_time_binning_param(current_value)
    raise ValueError("Unsupported parameter type")


def edit_int_param(param_type: IntegerParam, current_value: int | None):
    return prompts.int_input(
        "Enter an integer value",
        min=param_type.min,
        max=param_type.max,
        default=current_value,
    )


def edit_time_binning_param(
    current_value: TimeBinningValue | None,
) -> TimeBinningValue | None:
    unit = prompts.list_input(
        "Choose binning unit",
        choices=[
            ("Year", "year"),
            ("Month", "month"),
            ("Day", "day"),
            ("Hour", "hour"),
            ("Minute", "minute"),
            ("Second", "second"),
        ],
        default=current_value.unit if current_value else None,
    )
    if not unit:
        return None

    amount = prompts.int_input(
        "How many?",
        min=1,
        max=1000,
        default=(
            current_value.amount
            if current_value and current_value.unit == unit
            else None
        ),
    )
    if not amount:
        return None

    return TimeBinningValue(unit=unit, amount=amount)
