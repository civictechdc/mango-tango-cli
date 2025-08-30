from tempfile import TemporaryDirectory
from traceback import format_exc
from typing import Optional

import polars as pl

from analyzer_interface import (
    AnalyzerInterface,
    InputColumn,
    ParamValue,
    UserInputColumn,
    column_automap,
    get_data_type_compatibility_score,
)
from app import ProjectContext
from terminal_tools import draw_box, prompts, smart_print_data_frame, wait_for_key

from .analysis_params import customize_analysis
from .context import ViewContext


def new_analysis(
    context: ViewContext,
    project: ProjectContext,
):
    terminal = context.terminal
    app = context.app
    analyzers = app.context.suite.primary_anlyzers
    with terminal.nest(draw_box("Choose a test", padding_lines=0)):
        analyzer: Optional[AnalyzerInterface] = prompts.list_input(
            "Which test?",
            choices=[
                ("(Back)", None),
                *(
                    (f"{analyzer.name} ({analyzer.short_description})", analyzer)
                    for analyzer in analyzers
                ),
            ],
        )

    if analyzer is None:
        return

    with terminal.nest(draw_box(analyzer.name, padding_lines=0)):
        with terminal.nest("◆◆ About this test ◆◆"):
            print("")
            print(analyzer.long_description or analyzer.short_description)
            print("")
            print("◆◆ Required Input ◆◆")
            print("The test requires these columns in the input data:")
            print("")

            required_cols_dict = {"Column ID": [], "Description": []}
            for input_column in analyzer.input.columns:
                required_cols_dict["Column ID"].append(
                    input_column.human_readable_name_or_fallback()
                )
                required_cols_dict["Description"].append(input_column.description)

            smart_print_data_frame(
                data_frame=pl.DataFrame(required_cols_dict),
                title=None,
                apply_color="row-wise",
            )

            # for index, input_column in enumerate(analyzer.input.columns):
            #    print(
            #        f"[{index + 1}] {input_column.human_readable_name_or_fallback()}"
            #        f" ({input_column.data_type})"
            #    )
            #    print(input_column.description or "")
            #    print("")

            user_columns = project.columns
            user_columns_by_name = {
                user_column.name: user_column for user_column in user_columns
            }
            draft_column_mapping = column_automap(user_columns, analyzer.input.columns)
            unmapped_columns = list(
                input_column
                for input_column in analyzer.input.columns
                if draft_column_mapping.get(input_column.name) is None
            )

            if len(unmapped_columns) > 0:
                print("Your dataset does NOT have all the types of columns required.")
                print("These columns cannot be satisfied:")
                for input_column in unmapped_columns:
                    print(
                        f"- {input_column.human_readable_name_or_fallback()}"
                        + f" ({input_column.data_type})"
                    )

                print("")
                print("The analysis will now exit.")
                print("")
                wait_for_key(True)
                return
            else:
                print(
                    "You will now choose which columns in your dataset to use for the test."
                )
                wait_for_key(True)

        final_column_mapping = draft_column_mapping
        while True:
            with terminal.nest("◆◆ Column selection ◆◆") as column_mapping_scope:
                mapping_df = pl.DataFrame(
                    {
                        "Column Name for Analyzer Input": [
                            input_column.human_readable_name_or_fallback()
                            for input_column in analyzer.input.columns
                        ],
                        "← Column Name In Your Dataset": [
                            draft_column_mapping.get(input_column.name)
                            for input_column in analyzer.input.columns
                        ],
                    }
                )

                smart_print_data_frame(
                    data_frame=mapping_df,
                    title=None,
                    apply_color="row-wise",
                    smart_print=False,
                )

                sample_input_df = pl.DataFrame(
                    {
                        input_col.human_readable_name_or_fallback(): project.column_dict.get(
                            final_column_mapping.get(input_col.name)
                        )
                        .head(5)
                        .apply_semantic_transform()
                        for input_col in analyzer.input.columns
                    }
                )
                print("Your test data would look like this:")
                smart_print_data_frame(
                    data_frame=sample_input_df,
                    title="Sample input data",
                    apply_color="column-wise",
                    smart_print=False,
                )

                mapping_ok = prompts.confirm(
                    "Are you happy with this mapping?",
                    default=False,
                    cancel_fallback=None,
                )

                if mapping_ok is None:
                    print("Canceled")
                    wait_for_key(True)
                    return

                if mapping_ok:
                    break

                column_mapping_scope.refresh()
                selected_analyzer_column: Optional[InputColumn] = prompts.list_input(
                    "Choose the input column to re-assign",
                    choices=[
                        (
                            input_column.human_readable_name_or_fallback()
                            + (
                                ": " + input_column.description
                                if input_column.description
                                else ""
                            ),
                            input_column,
                        )
                        for input_column in analyzer.input.columns
                    ],
                )

                if selected_analyzer_column is None:
                    continue

                column_mapping_scope.refresh()
                print("You are re-assigning data for this test input column:")
                print(
                    "["
                    + selected_analyzer_column.human_readable_name_or_fallback()
                    + "]"
                )
                if selected_analyzer_column.description:
                    print("")
                    print("Explanation: " + selected_analyzer_column.description)
                print("")
                print(
                    "The test requires data type"
                    + f"[{selected_analyzer_column.data_type}] for this column."
                )
                print("")

                selected_user_column: Optional[UserInputColumn] = prompts.list_input(
                    "Choose your dataset's column to use",
                    choices=[
                        (
                            '"'
                            + user_column.name
                            + '" ['
                            + user_column.data_type
                            + "]",
                            user_column,
                        )
                        for user_column in user_columns
                        if get_data_type_compatibility_score(
                            selected_analyzer_column.data_type, user_column.data_type
                        )
                        is not None
                    ],
                )

                if selected_user_column is not None:
                    draft_column_mapping[selected_analyzer_column.name] = (
                        selected_user_column.name
                    )
        param_values = customize_analysis(
            context, project, analyzer, final_column_mapping
        )

        if param_values is None:
            print("Canceled")
            wait_for_key(True)
            return

        analysis = project.create_analysis(
            analyzer.id, final_column_mapping, param_values
        )

        with terminal.nest("Analysis") as run_scope:
            is_export_started = False
            try:
                for event in analysis.run():
                    if event.event == "start":
                        run_scope.refresh()
                        if event.analyzer.kind == "primary":
                            print("Starting base analysis for the test...")
                        else:
                            print("Running post-analysis: ", event.analyzer.name)

                run_scope.refresh()
                print("<<Hit Ctrl+C at any time to exit a menu>>")
                print("The Analysis is complete.")
                wait_for_key(prompt=True)

                return analysis

            except KeyboardInterrupt:
                if is_export_started:
                    print(
                        "The export was interrupted -- the outputs may be incomplete."
                    )
                    print("You can re-attempt the export from the menu.")
                else:
                    print("The test run was canceled")

                wait_for_key(True)
                return None

            except Exception as e:
                traceback = format_exc()
                run_scope.refresh()
                print("An error occurred during the analysis:")
                print(e)
                print("")

                if prompts.confirm(
                    "Would you like to see the full error traceback?", default=False
                ):
                    print(traceback)

                print("")
                print(
                    "Help us improve this tool by reporting this error on our GitHub repository:"
                )
                print("https://github.com/CIB-Mango-Tree/mango-tango-cli")
                print("")
                wait_for_key(True)

                return None

            finally:
                if analysis.is_draft:
                    analysis.delete()
