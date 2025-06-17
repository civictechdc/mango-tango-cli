from analyzer_interface import AnalyzerDeclaration

from .default_params import default_params
from .interface import interface
from .main import main

# This is an example primary analyzer. It simply counts the number of characters
# in a text column and writes the result to a parquet file.
example_base = AnalyzerDeclaration(
    interface=interface,
    main=main,
    # Optional.
    # If your analyzer is parameterized, you can define a function to suggest
    # default analysis parameters based on the input data. For an easier way
    # to provide default parameter values independently of input data, simply
    # specify it in the analysis parameter specification in the interface itself
    # (see `interface.py`)
    default_params=default_params,
    # This marks the analyzer as distributed or not. A distributed
    # analyzer is visible only when the application is packaged. A non-distributed
    # analyzer is also visible when the application is run in development mode.
    is_distributed=False,
)
