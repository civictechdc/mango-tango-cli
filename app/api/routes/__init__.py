from ..utils import RouteContext
from .presenters import PresentersView, PresenterView

endpoints: list[RouteContext] = [
    RouteContext(name="presenters-many", path="/presenters", view=PresentersView),
    RouteContext(
        name="presenters-one", path="/presenters/<string:id>", view=PresenterView
    ),
]
