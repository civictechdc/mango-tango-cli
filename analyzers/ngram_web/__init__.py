from analyzer_interface import WebPresenterDeclaration, WebPresenterInterface

from .factory import factory, api_factory
from .interface import interface

ngrams_web = WebPresenterDeclaration(
    interface=interface,
    factory=factory,
    api_factory=api_factory,
    name=__name__
)
