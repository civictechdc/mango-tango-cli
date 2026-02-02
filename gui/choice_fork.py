from nicegui import ui
from typing import Callable


def two_button_choice_fork_content(
    prompt: str,
    left_button_label: str,
    left_button_on_click: Callable[[], None],
    left_button_icon: str,
    right_button_label: str,
    right_button_on_click: Callable[[], None],
    right_button_icon: str,
) -> None:
    # Main content area - centered vertically
    with (
        ui.column()
        .classes("items-center justify-center")
        .style("height: 80vh; width: 100%")
    ):
        # Prompt label
        ui.label(prompt).classes("q-mb-lg").style("font-size: 1.05rem")

        # Action buttons row
        with ui.row().classes("gap-4"):
            ui.button(
                left_button_label,
                on_click=left_button_on_click,
                icon=left_button_icon,
                color="primary",
            )

            ui.button(
                right_button_label,
                on_click=right_button_on_click,
                icon=right_button_icon,
                color="primary",
            )
