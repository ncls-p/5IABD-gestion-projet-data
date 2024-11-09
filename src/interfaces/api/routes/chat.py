from fastapi import APIRouter, Depends
from ..schemas.models import ChatRequest
from ....application.services.chat_service import ChatService
from ..dependencies import get_chat_service
from ....core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/chat")
async def chat(
    request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)
) -> dict:
    functions = request.functions if request.functions is not None else []
    return await chat_service.process_chat(request.messages, functions)


@router.post("/export-ics")
async def export_to_ics(
    messages: list, chat_service: ChatService = Depends(get_chat_service)
) -> str:
    return await chat_service.generate_calendar_ics(messages)
