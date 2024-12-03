# ...existing code...

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.event import (
    Event,
)  # Changed from domain.entities.event to ..entities.event


class EventRepository(ABC):
    @abstractmethod
    async def get_all(self) -> List[Event]:
        pass

    @abstractmethod
    async def get_by_id(self, event_id: int) -> Optional[Event]:
        pass

    @abstractmethod
    async def create(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def delete(self, event_id: int) -> bool:
        pass
