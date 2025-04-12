from ..utils import RouteContext
from .presenters import PresentersView

endpoints: list[RouteContext] = [
    RouteContext(name="presenters-many", path="/presenters", view=PresentersView)
]
