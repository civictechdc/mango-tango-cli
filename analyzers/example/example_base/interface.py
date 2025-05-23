from analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerOutput,
    AnalyzerParam,
    InputColumn,
    IntegerParam,
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
    params=[
        AnalyzerParam(
            # This corresponds to the key in the parameter dictionary when accessed
            # from the analyzer context.
            id="fudge_factor",
            # This is the human readable name that will be displayed in the user
            # interface. It's optional and will fall back to the ID.
            human_readable_name="Character Count Fudge Factor",
            # Also optional, shown in the UI if provided.
            description="""
Adds to the character count, because data manipulation is
good data science and ethically no-problemo.

/s: In seriousness, please *don't* manipulate data.
It's wrong. We are trying to fight misinformation :)
            """,
            # Follow the definition here to the module where all the supported
            # param types are defined.
            type=IntegerParam(
                # Depending on the parameter type, you may be required to
                # provide extra ranges/bounds for validation.
                min=-1000,
                max=1000,
            ),
            # Optional.
            # Sets the default/initial value. This is one of the two ways to set
            # a default parameter value, the other being using a default_params
            # function (see the `__init__.py` file), which can suggest defaults
            # in a data-dependent manner.
            default=0,
            # Optional.
            # If you have an existing analyzer that previously hardcoded a parameter
            # that you now want to customize, you can set this to the value it was
            # hardcoded, and older analysis saves will use this value when the
            # parameter is shown in the UI and accessed in the web presenter.
            # Note: This is NOT a default value!
            backfill_value=0,
        )
    ],
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
