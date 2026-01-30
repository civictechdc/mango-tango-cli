from analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerOutput,
    AnalyzerParam,
    InputColumn,
    OutputColumn,
)
from analyzer_interface.params import IntegerParam

COL_AUTHOR_ID = "user_id"
COL_MESSAGE_ID = "message_id"
COL_MESSAGE_SURROGATE_ID = "message_surrogate_id"
COL_MESSAGE_TEXT = "message_text"
COL_NGRAM_ID = "ngram_id"
COL_NGRAM_WORDS = "words"
COL_NGRAM_LENGTH = "n"
COL_MESSAGE_TIMESTAMP = "timestamp"

OUTPUT_MESSAGE_NGRAMS = "message_ngrams"
OUTPUT_NGRAM_DEFS = "ngrams"
OUTPUT_MESSAGE = "message_authors"

# Parameter definitions
PARAM_MIN_N = "min_n"
PARAM_MAX_N = "max_n"

interface = AnalyzerInterface(
    id="ngrams",
    version="0.2.0",
    name="N-gram Analysis",
    short_description="Extracts n-grams from text data with multilingual support",
    long_description="""
The n-gram analysis extracts n-grams (sequences of n words) from the text data
in the input and counts the occurrences of unique n-grams across posts, linking
the message author to the n-gram frequency.

This analyzer uses Unicode-aware tokenization with support for multilingual content,
including proper handling of different scripts (Latin, CJK, Arabic) and social media
entities (hashtags, mentions, URLs).

The result can be used to see if certain word sequences are more common in
the collection of social media posts, and whether certain authors use these sequences more often.
  """,
    input=AnalyzerInput(
        columns=[
            InputColumn(
                name=COL_AUTHOR_ID,
                human_readable_name="Unique User ID",
                data_type="identifier",
                description="The unique identifier of the author of the message",
                name_hints=[
                    "author",
                    "user",
                    "poster",
                    "username",
                    "screen name",
                    "user name",
                    "name",
                    "email",
                ],
            ),
            InputColumn(
                name=COL_MESSAGE_ID,
                human_readable_name="Unique Post Number",
                data_type="identifier",
                description="The unique identifier of the message",
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
                name=COL_MESSAGE_TEXT,
                human_readable_name="Post Content",
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
            InputColumn(
                name=COL_MESSAGE_TIMESTAMP,
                human_readable_name="Timestamp",
                data_type="datetime",
                description="The time at which the message was posted",
                name_hints=["time", "timestamp", "date", "ts"],
            ),
        ]
    ),
    outputs=[
        AnalyzerOutput(
            id=OUTPUT_MESSAGE_NGRAMS,
            name="Unique n-grams present in message",
            internal=True,
            description="Maps messages to the unique n-grams they contain (deduplicated within message)",
            columns=[
                OutputColumn(name=COL_MESSAGE_SURROGATE_ID, data_type="identifier"),
                OutputColumn(name=COL_NGRAM_ID, data_type="identifier"),
            ],
        ),
        AnalyzerOutput(
            id=OUTPUT_NGRAM_DEFS,
            name="N-gram definitions",
            internal=True,
            description="The word compositions of each unique n-gram",
            columns=[
                OutputColumn(name=COL_NGRAM_ID, data_type="identifier"),
                OutputColumn(name=COL_NGRAM_WORDS, data_type="text"),
                OutputColumn(name=COL_NGRAM_LENGTH, data_type="integer"),
            ],
        ),
        AnalyzerOutput(
            id=OUTPUT_MESSAGE,
            name="Message data",
            internal=True,
            description="The original message data",
            columns=[
                OutputColumn(name=COL_MESSAGE_SURROGATE_ID, data_type="identifier"),
                OutputColumn(name=COL_AUTHOR_ID, data_type="identifier"),
                OutputColumn(name=COL_MESSAGE_ID, data_type="identifier"),
                OutputColumn(name=COL_MESSAGE_TEXT, data_type="text"),
                OutputColumn(name=COL_MESSAGE_TIMESTAMP, data_type="datetime"),
            ],
        ),
    ],
    params=[
        AnalyzerParam(
            id=PARAM_MIN_N,
            human_readable_name="Minimum N-gram Length",
            description="Minimum length of n-grams to extract (e.g., 3 for trigrams and longer)",
            type=IntegerParam(min=1, max=10),
            default=3,
        ),
        AnalyzerParam(
            id=PARAM_MAX_N,
            human_readable_name="Maximum N-gram Length",
            description="Maximum length of n-grams to extract (e.g., 5 for up to 5-grams)",
            type=IntegerParam(min=1, max=10),
            default=5,
        ),
    ],
)
