from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ....application.services.calendar_service import CalendarService
from ....domain.entities.event import Event
from ..schemas.models import EventCreate, EventResponse
from ..dependencies import get_calendar_service

router = APIRouter()


@router.post("/events", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> Event:
    return await calendar_service.create_event(Event(**event.dict()))


@router.get("/events", response_model=List[EventResponse])
async def get_events(
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> List[Event]:
    return await calendar_service.get_all_events()


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int, calendar_service: CalendarService = Depends(get_calendar_service)
) -> dict:
    success = await calendar_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "success", "message": "Event deleted successfully"}
