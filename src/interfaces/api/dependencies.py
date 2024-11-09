from ...application.services.calendar_service import CalendarService
from ...application.services.chat_service import ChatService
from ...infrastructure.database.postgres import PostgresEventRepository
from ...infrastructure.llm.openai import OpenAIRepository


def get_calendar_service() -> CalendarService:
    return CalendarService(PostgresEventRepository())


def get_chat_service() -> ChatService:
    return ChatService(OpenAIRepository())
