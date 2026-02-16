from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class Attendee(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "attendees"

    event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    #qr taken should be long + random 
    qr_token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
 
    event = relationship("Event", back_populates="attendees")