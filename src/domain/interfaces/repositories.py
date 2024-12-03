from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.event import Event
from ..entities.task import TaskCreate  # Add this import if needed


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

    @abstractmethod
    async def get_by_id(self, event_id: int) -> Optional[Event]:
        pass


class LLMRepository(ABC):
    @abstractmethod
    async def chat(self, messages: List[dict], functions: List[dict]) -> dict:
        pass

    @abstractmethod
    async def generate_ics(self, messages: List[dict]) -> str:
        pass
