from mango_tango_cib.analyzer_interface import AnalyzerDeclaration

from .interface import interface
from .main import main

hashtags = AnalyzerDeclaration(interface=interface, main=main)
