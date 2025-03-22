from mango_tango_cib.analyzer_interface import WebPresenterDeclaration

from .factory import factory
from .interface import interface

example_web = WebPresenterDeclaration(
    interface=interface,
    factory=factory,
    # You must pass __name__ here. It's to make Dash happy.
    # See: http://dash.plotly.com/urls
    name=__name__,
)
