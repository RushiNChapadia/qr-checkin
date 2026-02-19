from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class Event(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "events"

    owner_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    venue: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scanner_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    owner = relationship("User", back_populates="events")
    attendees = relationship("Attendee", back_populates="event", cascade = "all, delete-orphan")