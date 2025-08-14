from analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerOutput,
    AnalyzerParam,
    InputColumn,
    IntegerParam,
    OutputColumn,
)

COL_AUTHOR_ID = "user_id"
COL_MESSAGE_ID = "message_id"
COL_MESSAGE_SURROGATE_ID = "message_surrogate_id"
COL_MESSAGE_TEXT = "message_text"
COL_MESSAGE_NGRAM_COUNT = "count"
COL_NGRAM_ID = "ngram_id"
COL_NGRAM_WORDS = "words"
COL_NGRAM_LENGTH = "n"
COL_MESSAGE_TIMESTAMP = "timestamp"


PARAM_MIN_N = "min_n"
PARAM_MAX_N = "max_n"

OUTPUT_MESSAGE_NGRAMS = "message_ngrams"
OUTPUT_NGRAM_DEFS = "ngrams"
OUTPUT_MESSAGE = "message_authors"

interface = AnalyzerInterface(
    id="ngrams",
    version="0.3.0",
    name="N-gram Analysis",
    short_description="Extracts configurable n-grams from text data",
    long_description="""
The n-gram analysis extracts n-grams (sequences of n words) from the text data
in the input and counts the occurrences of each n-gram in each message, linking
the message author to the ngram frequency.

The analyzer automatically detects the language type and applies appropriate
tokenization: space-separated for Western languages (English, Spanish, French, etc.)
and character-level for non-spaced languages (Chinese, Japanese, Thai, etc.).

You can configure the minimum and maximum n-gram lengths to focus on specific
word sequence patterns. The result can be used to see if certain word sequences
are more common in the corpus of text, and whether certain authors use these
sequences more often.
  """,
    input=AnalyzerInput(
        columns=[
            InputColumn(
                name=COL_AUTHOR_ID,
                human_readable_name="Message Author ID",
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
                human_readable_name="Unique Message ID",
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
            InputColumn(
                name=COL_MESSAGE_TIMESTAMP,
                human_readable_name="Message Timestamp",
                data_type="datetime",
                description="The time at which the message was posted",
                name_hints=["time", "timestamp", "date", "ts"],
            ),
        ]
    ),
    params=[
        AnalyzerParam(
            id=PARAM_MIN_N,
            human_readable_name="Minimum N-gram Length",
            description="""
The minimum length for n-grams to extract. For example, setting this to 2 will
include bigrams (2-word sequences) and longer sequences.

Common settings:
- 1: Include single words (unigrams)
- 2: Start with word pairs (bigrams)
- 3: Start with three-word phrases (trigrams)

Lower values capture more general patterns but produce larger result sets.
            """,
            type=IntegerParam(min=1, max=10),
            default=3,
        ),
        AnalyzerParam(
            id=PARAM_MAX_N,
            human_readable_name="Maximum N-gram Length",
            description="""
The maximum length for n-grams to extract. For example, setting this to 5 will
include sequences up to 5 words long.

Common settings:
- 3: Focus on short phrases (up to trigrams)
- 5: Include medium-length phrases
- 8: Include longer phrases and sentences

Higher values capture more specific patterns but may be less frequent.
            """,
            type=IntegerParam(min=1, max=15),
            default=5,
        ),
    ],
    outputs=[
        AnalyzerOutput(
            id=OUTPUT_MESSAGE_NGRAMS,
            name="N-gram count per message",
            internal=True,
            columns=[
                OutputColumn(name=COL_MESSAGE_SURROGATE_ID, data_type="identifier"),
                OutputColumn(name=COL_NGRAM_ID, data_type="identifier"),
                OutputColumn(name=COL_MESSAGE_NGRAM_COUNT, data_type="integer"),
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
)
