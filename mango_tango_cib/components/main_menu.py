from sys import exit

from terminal_tools import draw_box, prompts

from .analysis_main import analysis_main
from .context import ViewContext
from .new_analysis import new_analysis
from .new_project import new_project
from .project_main import project_main
from .select_project import select_project


def main_menu(context: ViewContext):
    terminal = context.terminal
    while True:
        exit_instruction = "⟪ Hit Ctrl+C at any time to exit a menu ⟫"
        welcome_message = "Import your datasets to run analysis for likelihood of coordinated inauthentic behavior."
        with terminal.nest(
            draw_box("CIB Mango Tree")
            + "\n"
            + exit_instruction
            + "\n\n"
            + welcome_message
            + "\n"
        ):
            action = prompts.list_input(
                "What would you like to do?",
                choices=[
                    ("Import dataset for new project", "new_project"),
                    ("Review existing project", "load_project"),
                    ("Exit", "exit"),
                ],
            )

        if action == "exit" or action is None:
            print("Bye!")
            exit(0)

        if action == "new_project":
            with terminal.nest(
                draw_box("CIB Mango Tree: New Dataset") + "\n" + exit_instruction + "\n"
            ):
                project = new_project(context)

            if project is not None:
                analysis = new_analysis(context, project)
                if analysis is not None:
                    analysis_main(context, analysis)
                project_main(context, project)
            continue

        if action == "load_project":
            with terminal.nest(
                draw_box("CIB Mango Tree: Load Dataset")
                + "\n"
                + exit_instruction
                + "\n"
            ):
                project = select_project(context)
            if project is not None:
                project_main(context, project)
            continue
