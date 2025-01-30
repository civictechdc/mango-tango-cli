from analyzer_interface import AnalyzerOutput, OutputColumn, SecondaryAnalyzerInterface

from ..example_base.interface import interface as example_base

interface = SecondaryAnalyzerInterface(
    # This ID should unique among the analyzers in the application.
    id="example_report",
    # We don't really use this yet, but specify something for now.
    version="0.1.0",
    # The name of the analyzer as shown on the UI.
    name="Example Report",
    short_description="",
    # Specify the primary analyzer here. You MUST do this otherwise the
    # secondary analyzer will not be detected as deriving from the primary.
    base_analyzer=example_base,
    outputs=[
        AnalyzerOutput(
            id="example_report",
            name="Example Report",
            columns=[
                OutputColumn(name="message_id", data_type="integer"),
                OutputColumn(name="character_count", data_type="integer"),
                # This is our pretend "presented column" that isn't part of the
                # actual analysis, but is just for the report. We avoid storing
                # things like this in the primary analyzer output (unless it's
                # laborious to compute), since it's only specific to this export.
                OutputColumn(name="is_long", data_type="boolean"),
            ],
        )
    ],
)
