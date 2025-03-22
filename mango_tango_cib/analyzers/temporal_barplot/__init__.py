from mango_tango_cib.analyzer_interface import WebPresenterDeclaration

from .factory import factory
from .interface import interface

temporal_barplot = WebPresenterDeclaration(
    interface=interface, factory=factory, name=__name__
)
