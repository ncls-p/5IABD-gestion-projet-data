from typing import List, Dict
from ...domain.interfaces.repositories import LLMRepository
from ...core.logger import setup_logger

logger = setup_logger(__name__)


class ChatService:
    def __init__(self, llm_repository: LLMRepository):
        self.llm_repository = llm_repository

    async def process_chat(self, messages: List[Dict], functions: List[Dict]) -> Dict:
        return await self.llm_repository.chat(messages, functions)

    async def generate_calendar_ics(self, messages: List[Dict]) -> str:
        return await self.llm_repository.generate_ics(messages)
