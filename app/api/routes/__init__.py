from ..utils import RouteContext
from .presenters import PresenterDownloadView, PresentersView, PresenterView

endpoints: list[RouteContext] = [
    RouteContext(name="presenters-many", path="/presenters", view=PresentersView),
    RouteContext(
        name="presenters-one", path="/presenters/<string:id>", view=PresenterView
    ),
    RouteContext(
        name="presenters-one-download",
        path="/presenters/<string:id>/download/<string:file_type>",
        view=PresenterDownloadView,
    ),
]
