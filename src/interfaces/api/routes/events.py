from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ....application.services.calendar_service import CalendarService
from ....domain.entities.event import Event
from ..schemas.models import EventCreate, EventResponse, EventSplitRequest
from ..dependencies import get_calendar_service

# Add a prefix to the router
router = APIRouter(prefix="/events")

@router.post("/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> Event:
    return await calendar_service.create_event(Event(**event.dict()))

@router.get("/", response_model=List[EventResponse])
async def get_events(
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> List[Event]:
    return await calendar_service.get_all_events()

@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> dict:
    success = await calendar_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "success", "message": "Event deleted successfully"}

@router.post("/split")
async def split_event(
    request: EventSplitRequest,
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> dict:
    success = await calendar_service.split_event(request.event_id, request.tasks)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "success", "message": "Event split successfully"}
