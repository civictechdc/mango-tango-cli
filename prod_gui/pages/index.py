from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/")
async def home() -> PlainTextResponse:
    return PlainTextResponse("Hello world!")
