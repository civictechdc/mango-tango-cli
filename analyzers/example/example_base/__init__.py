from analyzer_interface import AnalyzerDeclaration

from .interface import interface
from .main import main

# This is an example primary analyzer. It simply counts the number of characters
# in a text column and writes the result to a parquet file.
example_base = AnalyzerDeclaration(
    interface=interface,
    main=main,
    # This marks the analyzer as distributed or not. A distributed
    # analyzer is visible only when the application is packaged. A non-distributed
    # analyzer is also visible when the application is run in development mode.
    is_distributed=False,
)
