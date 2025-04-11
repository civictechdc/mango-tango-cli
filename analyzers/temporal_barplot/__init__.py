from analyzer_interface import WebPresenterDeclaration

from .factory import api_factory, factory
from .interface import interface

temporal_barplot = WebPresenterDeclaration(
    interface=interface, factory=factory, api_factory=api_factory, name=__name__
)
