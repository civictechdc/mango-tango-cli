from analyzer_interface import WebPresenterDeclaration, WebPresenterInterface

from .factory import factory
from .interface import interface

hashtags_web = WebPresenterDeclaration(
    interface=interface, factory=factory, name=__name__
)
