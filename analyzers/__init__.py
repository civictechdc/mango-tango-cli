from analyzer_interface import AnalyzerSuite

from .example.example_base import example_base
from .example.example_report import example_report
from .example.example_web import example_web
from .hashtags import hashtags
from .ngram_stats import ngram_stats
from .ngram_web import ngrams_web
from .ngrams import ngrams
from .temporal import temporal
from .temporal_barplot import temporal_barplot
from .time_coordination import time_coordination

suite = AnalyzerSuite(
    all_analyzers=[
        example_base,
        example_report,
        example_web,
        ngrams,
        ngram_stats,
        ngrams_web,
        time_coordination,
        temporal,
        temporal_barplot,
        hashtags,
    ]
)
