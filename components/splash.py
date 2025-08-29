from rich import print
from rich.console import Console
from rich.panel import Panel

from meta import get_version
from terminal_tools import clear_terminal, wait_for_key


def splash():
    console = Console()

    # Calculate exact width thresholds for each logo size
    # Measured from actual ASCII art content + Rich Panel borders/padding
    BIG_LOGO_WIDTH = 102  # Big logo longest line
    SMALL_LOGO_WIDTH = 78  # Small logo longest line
    PANEL_PADDING = 4  # Rich Panel border + padding (2 chars each side)

    BIG_THRESHOLD = BIG_LOGO_WIDTH + PANEL_PADDING  # 106 chars
    SMALL_THRESHOLD = SMALL_LOGO_WIDTH + PANEL_PADDING  # 82 chars

    clear_terminal()

    # Three-tier adaptive logo display
    if console.size.width < SMALL_THRESHOLD:
        print(_LOGO_MINI)  # Very narrow terminals
    elif console.size.width < BIG_THRESHOLD:
        print(_ASCII_LOGO_SMALL)  # Medium terminals
    else:
        print(_ASCII_LOGO_BIG)  # Wide terminals

    print(_ASCII_TREE)
    print("")
    wait_for_key(True)


_VERSION = f"[dim]{get_version() or 'development version'}[/dim]"
_TITLE = "A Civic Tech DC Project"

_LOGO_MINI = Panel.fit(
    """[orange1 bold]
    CIB MANGO TREE
    [/orange1 bold]""",
    title=_TITLE,
    title_align="center",
    subtitle=_VERSION,
)

_ASCII_LOGO_SMALL = Panel.fit(
    """[orange1]
   ____ ___ ____    __  __                           _____              
  / ___|_ _| __ )  |  \/  | __ _ _ __   __ _  ___   |_   _| __ ___  ___ 
 | |    | ||  _ \  | |\/| |/ _` | '_ \ / _` |/ _ \    | || '__/ _ \/ _ \\
 | |___ | || |_) | | |  | | (_| | | | | (_| | (_) |   | || | |  __/  __/
  \____|___|____/  |_|  |_|\__,_|_| |_|\__, |\___/    |_||_|  \___|\___|
                                       |___/[/orange1]""",
    title=_TITLE,
    subtitle=_VERSION,
)

_ASCII_LOGO_BIG = Panel.fit(
    """[orange1]
  ██████╗ ██╗ ██████╗      ███╗   ███╗  █████╗  ███╗   ██╗  ██████╗   ██████╗      ████████╗ ██████╗  ███████╗ ███████╗
 ██╔════╝ ██║ ██╔══██╗     ████╗ ████║ ██╔══██╗ ████╗  ██║ ██╔════╝  ██╔═══██╗     ╚══██╔══╝ ██╔══██╗ ██╔════╝ ██╔════╝
 ██║      ██║ ██████╔╝     ██╔████╔██║ ███████║ ██╔██╗ ██║ ██║  ███╗ ██║   ██║        ██║    ██████╔╝ █████╗   █████╗
 ██║      ██║ ██╔══██╗     ██║╚██╔╝██║ ██╔══██║ ██║╚██╗██║ ██║   ██║ ██║   ██║        ██║    ██╔══██╗ ██╔══╝   ██╔══╝
 ╚██████╗ ██║ ██████╔╝     ██║ ╚═╝ ██║ ██║  ██║ ██║ ╚████║ ╚██████╔╝ ╚██████╔╝        ██║    ██║  ██║ ███████╗ ███████╗
  ╚═════╝ ╚═╝ ╚═════╝      ╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚═╝  ╚═══╝  ╚═════╝   ╚═════╝         ╚═╝    ╚═╝  ╚═╝ ╚══════╝ ╚══════╝[/orange1]""",
    title=_TITLE,
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

"""
Notes:
Logo generated with: https://github.com/shinshin86/oh-my-logo
(used as: `npx oh-my-logo "CIB Mango Tree" gold --filled --no-color`)
Ascii tree was generated with: https://www.asciiart.eu/image-to-ascii
"""
