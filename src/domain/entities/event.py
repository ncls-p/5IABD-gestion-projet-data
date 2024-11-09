from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Event(BaseModel):
    id: Optional[int] = None
    event_name: str
    event_description: Optional[str] = None
    event_start_date_time: datetime
    event_end_date_time: datetime
    event_location: Optional[str] = None
