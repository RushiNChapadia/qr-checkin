import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    venue: str | None = Field(default=None, max_length=200)
    start_time: datetime | None = None


class EventOut(BaseModel):
    id: uuid.UUID
    name: str
    venue: str | None
    start_time: datetime | None

    class Config:
        from_attributes = True


class EventListOut(BaseModel):
    items: list[EventOut]
    limit: int
    offset: int
    total: int
