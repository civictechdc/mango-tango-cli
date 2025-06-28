from analyzer_interface import WebPresenterDeclaration

from .factory import factory
from .interface import interface

hashtags_web = WebPresenterDeclaration(
    interface=interface, factory=factory, name=__name__, shiny=True
)
