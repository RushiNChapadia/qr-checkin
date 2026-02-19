import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AttendeeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None


class AttendeeBulkCreate(BaseModel):
    attendees: list[AttendeeCreate] = Field(min_length=1, max_length=500)


class AttendeeOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    full_name: str
    email: str | None
    qr_token: str
    checked_in_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AttendeeListOut(BaseModel):
    items: list[AttendeeOut]
    limit: int
    offset: int
    total: int


class QRPayloadOut(BaseModel):
    """
    This is what you embed into the QR code.
    For MVP: we return token only.
    Later: we can return full URL to a hosted check-in page.
    """
    qr_token: str
    payload: str
