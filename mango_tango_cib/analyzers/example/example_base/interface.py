from mango_tango_cib.analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerOutput,
    InputColumn,
    OutputColumn,
)

interface = AnalyzerInterface(
    # Should be globally unique.
    id="__example__",
    # We don't really use this yet, but specify something for now.
    version="0.1.0",
    # The name of the analyzer as shown on the UI.
    name="Example Analyzer",
    # These descriptions are shown to the user in the UI at some point during the
    # analysis selection process.
    short_description="Example Analyzer (Character Count)",
    long_description="""
This is an example analyzer that counts the number of characters in each message.
  """,
    input=AnalyzerInput(
        columns=[
            InputColumn(
                # This is the column name that you will use in your data analysis
                # code.
                name="message_id",
                # This is the human readable name that will be displayed in the
                # user interface.
                human_readable_name="Unique Message ID",
                # Refer to the complete set of data types by following the
                # type definition.
                data_type="identifier",
                # This is a description of the column that will be displayed in
                # the user interface during column matching.
                description="The unique identifier of the message",
                # This name hints give the application a kind of soft heuristics
                # to match the column to the right data. The user will be able to
                # override the suggestion if it is incorrect.
                #
                # You don't need to provide all possible hints, but the more you
                # provide, the better the suggestions will be.
                name_hints=[
                    "post",
                    "message",
                    "comment",
                    "text",
                    "retweet id",
                    "tweet",
                ],
            ),
            InputColumn(
                name="message_text",
                human_readable_name="Message Text",
                data_type="text",
                description="The text content of the message",
                name_hints=[
                    "message",
                    "text",
                    "comment",
                    "post",
                    "body",
                    "content",
                    "tweet",
                ],
            ),
        ]
    ),
    outputs=[
        AnalyzerOutput(
            # This should be locally unique to the analyzer.
            # Remember this -- you will need it to refer to this output in your
            # implementation. It will also form part of the exported output's
            # file name, so choose something that's intuitive.
            id="character_count",
            # This is the human readable name that will be displayed in the
            # user interface. Only used if this is exportable. You can leave
            # it out and it will fallback to the id.
            name="Character Count Per Message",
            # Mark this as internal, so that it is not shown in the list of
            # exported outputs.
            internal=True,
            columns=[
                OutputColumn(
                    # This is the column name that you will use in your data analysis
                    # code when saving the output.
                    name="message_id",
                    # This is the human readable name that will be used in the
                    # exported output.
                    human_readable_name="Unique Message ID",
                    data_type="integer",
                ),
                OutputColumn(name="character_count", data_type="integer"),
            ],
        )
    ],
)
