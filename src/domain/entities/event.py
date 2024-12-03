from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from .task import TaskCreate


class Event(BaseModel):
    id: Optional[int] = None
    event_name: str
    event_description: Optional[str] = None
    event_start_date_time: datetime
    event_end_date_time: datetime
    event_location: Optional[str] = None
    tasks: Optional[List[TaskCreate]] = None
