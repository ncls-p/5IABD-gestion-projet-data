from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel


class EventCreate(BaseModel):
    event_name: str
    event_description: Optional[str] = None
    event_start_date_time: datetime
    event_end_date_time: datetime
    event_location: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[dict]
    selected_date: str
    functions: Optional[List[Dict]] = None


class EventResponse(BaseModel):
    id: int
    event_name: str
    event_description: Optional[str]
    event_start_date_time: datetime
    event_end_date_time: datetime
    event_location: Optional[str]
