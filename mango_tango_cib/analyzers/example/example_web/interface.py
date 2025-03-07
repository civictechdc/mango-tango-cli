from mango_tango_cib.analyzer_interface import WebPresenterInterface

from ..example_base import interface as example_base
from ..example_report import interface as example_report

interface = WebPresenterInterface(
    # This ID must be unique among all web presenters.
    id="example_web",
    # We don't really use this yet, but specify something for now.
    version="0.1.0",
    # The name of the web presenter as shown on the UI.
    name="Message Length Histogram",
    # This is the description that will be shown to the user in the UI.
    short_description="Shows the distribution of message lengths",
    # Specify the primary analyzer here.
    base_analyzer=example_base,
    # You must specify all of the secondary analyzers that this web presenter
    # depends on, and they must obviously be secondaries to the same primary
    # analyzer.
    #
    # In this example, we don't depend on any secondary analyzer, so we leave
    # this blank. However, the commented out line below shows how you would
    # specify a dependency.
    depends_on=[
        # example_report
    ],
)
