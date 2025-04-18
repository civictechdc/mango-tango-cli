from flask.views import MethodView
from pydantic import BaseModel


class RouteContext(BaseModel):
    name: str
    path: str
    view: type[MethodView]
