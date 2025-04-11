from analyzer_interface import WebPresenterDeclaration

from .factory import api_factory, factory
from .interface import interface

example_web = WebPresenterDeclaration(
    interface=interface,
    factory=factory,
    api_factory=api_factory,
    # You must pass __name__ here. It's to make Dash happy.
    # See: http://dash.plotly.com/urls
    name=__name__,
)
