from typing import List
from ...domain.entities.event import Event
from ...domain.entities.task import TaskCreate
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

    async def split_event(self, event_id: int, tasks: List[TaskCreate]) -> bool:
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            return False
        await self.event_repository.delete(event_id)
        for task in tasks:
            new_event = Event(
                event_name=task.task_name,
                event_description=event.event_description,
                event_start_date_time=task.task_start_date_time,
                event_end_date_time=task.task_end_date_time,
                event_location=event.event_location,
            )
            await self.event_repository.create(new_event)
        return True
