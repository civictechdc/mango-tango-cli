from analyzer_interface import WebPresenterInterface

from ..hashtags import interface as hashtags_interface

interface = WebPresenterInterface(
    id="hashtags_dashboard",
    version="0.1.0",
    name="Hashtag Analysis Dashboard",
    short_description="",
    base_analyzer=hashtags_interface,
)
