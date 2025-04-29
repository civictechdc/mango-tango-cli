from analyzer_interface import ParamValue
from analyzer_interface.context import PrimaryAnalyzerContext


def default_params(context: PrimaryAnalyzerContext) -> dict[str, ParamValue]:
    # Like the `main.py` analyzer entry point, the default parameter function
    # can use the context object to access the input data. It can then use it to
    # suggest parameters in a data-dependent manner.
    #
    # Data-dependent defaults override static defaults. Importantly, if you pass
    # `None` here, it will *unset* a static default.
    return {}
