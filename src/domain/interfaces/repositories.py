from abc import ABC, abstractmethod
from typing import List
from ..entities.event import Event


class EventRepository(ABC):
    @abstractmethod
    async def create(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def get_all(self) -> List[Event]:
        pass

    @abstractmethod
    async def delete(self, event_id: int) -> bool:
        pass


class LLMRepository(ABC):
    @abstractmethod
    async def chat(self, messages: List[dict], functions: List[dict]) -> dict:
        pass

    @abstractmethod
    async def generate_ics(self, messages: List[dict]) -> str:
        pass
