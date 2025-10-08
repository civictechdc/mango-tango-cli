from inspect import signature
from typing import List, Optional

from pydantic import BaseModel
from shiny.session import Inputs, Outputs, Session
from shiny.ui import (
    _navs,
    card,
    card_footer,
    card_header,
    markdown,
    nav_panel,
    page_navbar,
    tags,
)

from analyzer_interface.context import ServerCallback

MANGO_ORANGE2 = "#f3921e"
LOGO_URL = "https://raw.githubusercontent.com/CIB-Mango-Tree/CIB-Mango-Tree-Website/main/assets/images/mango-text.PNG"
ABOUT_TEXT = markdown(
    f"""

<img src="{LOGO_URL}" alt="logo" style="width:200px;"/>

CIB Mango Tree, a collaborative and open-source project to develop software that tests for coordinated inauthentic behavior (CIB) in datasets of online activity.

[mangotree.org](https://mangotree.org)

A project of [Civic Tech DC](https://www.civictechdc.org/), our mission is to share methods to uncover how disruptive actors seek to hack our legitimate online discourse regarding health, politics, and society. The CIB Mango Tree presents the most simple tests for CIB first – the low-hanging fruit. These tests are easy to run and interpret. They will reveal signs of unsophisticated CIB. As you move up the Mango Tree, tests become harder and will scavenge for higher-hanging fruit.

"""
)
page_dependencies = tags.head(
    tags.style(".card-header { color:white; background:#f3921e !important; }"),
    tags.link(rel="stylesheet", href="https://fonts.googleapis.com/css?family=Roboto"),
    tags.style("body { font-family: 'Roboto', sans-serif; }"),
)


class ServerHandleManager(BaseModel):
    handlers: Optional[list[ServerCallback]] = []

    def add(self, handler: ServerCallback):
        self.handlers.append(handler)

    def extend(self, handlers: List[ServerCallback]):
        self.handlers.extend(handlers)

    def remove(self, handler: ServerCallback):
        self.handlers.remove(handler)

    def call_handlers(self, inputs: Inputs, outputs: Outputs, session: Session):
        for handler in self.handlers:
            handler_signature = signature(handler)

            if len(handler_signature.parameters) == 1:
                handler(inputs)
                continue

            handler(inputs, outputs, session)


class LayoutManager(BaseModel):
    title: Optional[str] = "CIB Mango Tree"
    elements: Optional[List[_navs.NavPanel]] = []

    class Config:
        arbitrary_types_allowed = True

    def add(self, element: _navs.NavPanel):
        self.elements.append(element)

    def extend(self, elements: List[_navs.NavPanel]):
        self.elements.extend(elements)

    def remove(self, element: _navs.NavPanel):
        self.elements.remove(element)

    def build_layout(self):
        return page_navbar(
            *self.elements,
            nav_panel(
                "About",
                card(
                    card_header("About the Mango Tree project"),
                    ABOUT_TEXT,
                    card_footer("PolyForm Noncommercial License 1.0.0"),
                ),
            ),
            title=self.title,
        )
