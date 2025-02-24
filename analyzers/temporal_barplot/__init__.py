from analyzer_interface import WebPresenterDeclaration

from .factory import factory, api_factory
from .interface import interface

temporal_barplot = WebPresenterDeclaration(
    interface=interface,
    factory=factory,
    api_factory=api_factory,
    name=__name__
)
