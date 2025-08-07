"""
Logo generated with: https://github.com/shinshin86/oh-my-logo
(used as: `npx oh-my-logo "CIB Mango Tree" gold --filled --no-color`)
Ascii tree was generated with: https://www.asciiart.eu/image-to-ascii
"""
from rich import print
from rich.panel import Panel

from meta import get_version
from terminal_tools import clear_terminal, wait_for_key


def splash():
    clear_terminal()
    print(_ASCII_LOGO)
    print(_ASCII_TREE)
    print("")
    wait_for_key(True)


_VERSION = f"[dim]{get_version() or 'development version'}[/dim]"

_ASCII_LOGO = Panel.fit(
    """[orange1]
  ██████╗ ██╗ ██████╗      ███╗   ███╗  █████╗  ███╗   ██╗  ██████╗   ██████╗      ████████╗ ██████╗  ███████╗ ███████╗
 ██╔════╝ ██║ ██╔══██╗     ████╗ ████║ ██╔══██╗ ████╗  ██║ ██╔════╝  ██╔═══██╗     ╚══██╔══╝ ██╔══██╗ ██╔════╝ ██╔════╝
 ██║      ██║ ██████╔╝     ██╔████╔██║ ███████║ ██╔██╗ ██║ ██║  ███╗ ██║   ██║        ██║    ██████╔╝ █████╗   █████╗
 ██║      ██║ ██╔══██╗     ██║╚██╔╝██║ ██╔══██║ ██║╚██╗██║ ██║   ██║ ██║   ██║        ██║    ██╔══██╗ ██╔══╝   ██╔══╝
 ╚██████╗ ██║ ██████╔╝     ██║ ╚═╝ ██║ ██║  ██║ ██║ ╚████║ ╚██████╔╝ ╚██████╔╝        ██║    ██║  ██║ ███████╗ ███████╗
  ╚═════╝ ╚═╝ ╚═════╝      ╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚═╝  ╚═══╝  ╚═════╝   ╚═════╝         ╚═╝    ╚═╝  ╚═╝ ╚══════╝ ╚══════╝[/orange1]""",
    title="A Civic Tech DC Project",
    subtitle=_VERSION,
)

_ASCII_TREE: str = """
        -..*+:..-.
       -.=-+%@%##+-=.-
    = =:*%:...=:..=@*:+ =
  :: -:=#==#*=:::-=-...-:::
 =.*++:%#*##=##+++:.*%*++..=
 @@@::--#@%#%%###%#@#-:::@@@
 ..:-##%@#@#%%%%++@#@%#+-=...
@@@@#-%@@#+#+++##+*+@@%%#@@@%
  : %#     @# %*++    :#% :
            @##%
            @@#
            @@#=
            @@%
            @@@
"""

_FOOTER: str = Panel.fit(
    """
  A Civic Tech DC Project
[red]
       ╱ * * *  ╱ ╲
       ╲ ===== ╱  ╱[/red]
"""
)
