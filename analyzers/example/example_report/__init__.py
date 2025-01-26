from analyzer_interface import SecondaryAnalyzerDeclaration

from .interface import interface
from .main import main

# This is an example secondary analyzer. It adds a column to the output of the
# primary analyzer that indicates whether the message is "long" or not.
example_report = SecondaryAnalyzerDeclaration(interface=interface, main=main)
