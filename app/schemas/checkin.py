import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    qr_token: str = Field(min_length=10, max_length=256)
    device_id: str | None = Field(default=None, max_length=100)


class CheckInResponse(BaseModel):
    attendee_id: uuid.UUID
    event_id: uuid.UUID
    full_name: str
    checked_in_at: datetime
    already_checked_in: bool
