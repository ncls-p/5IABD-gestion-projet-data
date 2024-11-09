from typing import List
from ...domain.entities.event import Event
from ...domain.interfaces.repositories import EventRepository


class CalendarService:
    def __init__(self, event_repository: EventRepository):
        self.event_repository = event_repository

    async def create_event(self, event: Event) -> Event:
        return await self.event_repository.create(event)

    async def get_all_events(self) -> List[Event]:
        return await self.event_repository.get_all()

    async def delete_event(self, event_id: int) -> bool:
        return await self.event_repository.delete(event_id)
