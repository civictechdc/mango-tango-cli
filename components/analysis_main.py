from colorama import Fore

from app import AnalysisContext
from terminal_tools import (
    draw_box,
    open_directory_explorer,
    print_ascii_table,
    prompts,
    wait_for_key,
)

from .analysis_params import print_param_value
from .context import ViewContext
from .export_outputs import export_outputs


def analysis_main(
    context: ViewContext, analysis: AnalysisContext, *, no_web_server=False
):
    terminal = context.terminal
    while True:
        has_web_server = len(analysis.web_presenters) > 0
        is_draft = analysis.is_draft
        has_exports = analysis.export_directory_exists()

        with terminal.nest(
            draw_box(f"Analysis: {analysis.display_name}", padding_lines=0)
        ):
            analyzer = analysis.analyzer_spec
            param_rows = [
                [
                    param_spec.print_name,
                    print_param_value(param_value),
                ]
                for param_spec in analyzer.params
                if (param_value := analysis.backfilled_param_values.get(param_spec.id))
                is not None
            ]
            if param_rows:
                print_ascii_table(
                    param_rows,
                    header=["parameter name", "parameter value"],
                )

            if is_draft:
                print("⚠️  This analysis didn't complete successfully.  ⚠️")

            action = prompts.list_input(
                "What would you like to do?",
                choices=[
                    *(
                        [
                            ("Open output directory", "open_output_dir"),
                        ]
                        if has_exports
                        else []
                    ),
                    *(
                        [
                            ("Export raw output files", "export_output"),
                        ]
                        if not is_draft
                        else []
                    ),
                    *(
                        [("Initiate browser-based dashboard", "web_server")]
                        if (not is_draft) and has_web_server and not no_web_server
                        else []
                    ),
                    ("Rename", "rename"),
                    ("Delete", "delete"),
                    ("(Back)", None),
                ],
            )

        if action is None:
            return

        if action == "open_output_dir":
            print("Starting file explorer")
            open_directory_explorer(analysis.export_root_path)
            wait_for_key(True)
            continue

        if action == "export_output":
            export_outputs(context, analysis)
            continue

        if action == "web_server":
            server = analysis.web_server()
            print("Web server will run at http://localhost:8050/")
            print("Stop it with Ctrl+C")
            try:
                server.start()
            except KeyboardInterrupt:
                pass
            print("Web server stopped")
            wait_for_key(True)
            continue

        if action == "rename":
            new_name = prompts.text("Enter new name", default=analysis.display_name)
            if new_name is None:
                print("Rename canceled")
                wait_for_key(True)
                continue

            analysis.rename(new_name)
            print("Analysis renamed")
            wait_for_key(True)
            continue

        if action == "delete":
            print(
                f"⚠️  Warning  ⚠️\n\n"
                f"This will permanently delete the analysis and all its outputs, "
                f"including the default export directory. "
                f"**Be sure to copy out any exports you want to keep before proceeding.**\n\n"
                f"The web dashboad will also no longer be accessible.\n\n"
            )
            confirm = prompts.confirm("Are you sure you want to delete this analysis?")
            if not confirm:
                print("Deletion canceled.")
                wait_for_key(True)
                continue

            safephrase = f"DELETE {analysis.display_name}"
            print(f"Type {Fore.RED}{safephrase}{Fore.RESET} to confirm deletion.")
            if prompts.text(f"(type the above to confirm)") != safephrase:
                print("Deletion canceled.")
                wait_for_key(True)
                continue

            analysis.delete()
            print("🔥 Analysis deleted.")
            wait_for_key(True)
            return
