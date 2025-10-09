from cibmangotree.analyzer_interface import WebPresenterInterface

from ..stats import interface as ngram_stats_interface
from ..base import interface as ngrams_interface

interface = WebPresenterInterface(
    id="ngram_repetition_by_poster",
    version="0.1.0",
    name="Repetition By Poster",
    short_description="",
    base_analyzer=ngrams_interface,
    depends_on=[ngram_stats_interface],
)
