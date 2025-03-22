# Example Analyzer Implementation

This is an example of how to implement an analyzer for the `analyzer` module. This analyzer is a simple example that counts the number of words in a given text, an export format that includes a "long"
flag that indicates whether a message is long or not.

A web presenter module is included that plots a histogram of
message lengths.

- [Primary Analyzer](./example_base/__init__.py)
- [Secondary Analyzer](./example_report/__init__.py)
- [Web Presenter](./example_web/__init__.py)
- [Test for Primary Analyzer](./example_base/test_example_base.py)
- [Test for Secondary Analyzer](./example_report/test_example_report.py)
