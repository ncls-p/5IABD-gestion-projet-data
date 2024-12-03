from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    task_name: str
    task_start_date_time: datetime
    task_end_date_time: datetime
