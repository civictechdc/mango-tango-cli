from analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerOutput,
    AnalyzerParam,
    InputColumn,
    OutputColumn,
)
from analyzer_interface.params import TimeBinningParam

COL_AUTHOR_ID = "Unique UserID"
COL_TIME = "Timestamp"
COL_POST = "Post Content"

PARAM_TIME_WINDOW = "time_window"

OUTPUT_GINI = "hashtag_analysis"
OUTPUT_COL_USERS = "users"
OUTPUT_COL_TIMESPAN = "timewindow_start"
OUTPUT_COL_GINI = "gini"
OUTPUT_COL_COUNT = "count"
OUTPUT_COL_HASHTAGS = "hashtags"

interface = AnalyzerInterface(
    id="hashtags",
    version="0.1.0",
    name="Hashtag analysis",
    short_description="Computes the concentration of hashtag usage over time.",
    long_description="""
Analysis of hashtags measures the extent of online coordination among social media users
by looking at how the usage of hashtags in messages changes over time. Specificaly,
it measures whether certain hashtags are being used more frequently than others (i.e. trending).

The intuition behind the analysis is that the users on social media, if coordinated by
an event, will converge on using a few hasthags more frequently than others
(e.g. #worldcup at the time when a soccer world cup starts). The (in)equality in
the distritution of hasthags can be taken as evidence of coordination and is quantified
using the Gini coefficient (see: https://ourworldindata.org/what-is-the-gini-coefficient).

The results of this test can be used in confirmatory analyses to measure
the extent of coordination in large datasets collected from social media platforms around
specific events/timepoints that are hypothesized to have been coordinated.
  """,
    input=AnalyzerInput(
        columns=[
            InputColumn(
                name=COL_AUTHOR_ID,
                data_type="identifier",
                description="The unique identifier of the author of the message",
                name_hints=[
                    "author",
                    "user",
                    "poster",
                    "username",
                    "screen_name",
                    "screen name",
                    "user name",
                    "name",
                    "email",
                ],
            ),
            InputColumn(
                name=COL_POST,
                data_type="text",
                description="The column containing the tweet and hashtags associated with the message",
                name_hints=["text", "tweet", "post", "tweet_post", "message"],
            ),
            InputColumn(
                name=COL_TIME,
                data_type="datetime",
                description="The timestamp of the message",
                name_hints=[
                    "time",
                    "timestamp",
                    "date",
                    "datetime",
                    "created",
                    "created_at",
                ],
            ),
        ]
    ),
    params=[
        AnalyzerParam(
            id=PARAM_TIME_WINDOW,
            human_readable_name="Time window of analysis",
            description="""
The duration over which to compute the gini coefficient. After
selecting a time window (e.g. 12 hours), the dataset will be
chunked into equal-duration (e.g. 12-hour long) time windows. The gini 
coefficient is computed over hashtags found in each time window chunk. 

This value determines the time granularity of the analysis. The optimal
value depends on the time span of the dataset. Generally, you want to 
choose time window long enough that there is a meaningful number of hashtags
in that time period (if there are none, gini will be 0 for those time windows).

For example, if the full dataset spans multiple years, it makes sense
to choose a time window that spans multiple days if not months. Conversely,
if a dataset spans a few weeks, it makes sense to choose a time window of
a few hours or one day etc.
            """,
            type=TimeBinningParam(),
        )
    ],
    outputs=[
        AnalyzerOutput(
            id=OUTPUT_GINI,
            name="Gini coefficient over time",
            columns=[
                OutputColumn(name=OUTPUT_COL_TIMESPAN, data_type="datetime"),
                OutputColumn(name=OUTPUT_COL_GINI, data_type="float"),
                OutputColumn(name=OUTPUT_COL_USERS, data_type="text"),
                OutputColumn(name=OUTPUT_COL_COUNT, data_type="integer"),
                OutputColumn(name=OUTPUT_COL_HASHTAGS, data_type="text"),
            ],
        )
    ],
)
