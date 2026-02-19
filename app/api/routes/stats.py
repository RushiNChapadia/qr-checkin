import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.event import Event
from app.models.user import User

router = APIRouter(prefix="/events", tags=["stats"])


@router.get("/{event_id}/stats")
def event_stats(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    total = db.scalar(select(func.count()).select_from(Attendee).where(Attendee.event_id == event_id)) or 0
    checked_in = (
        db.scalar(
            select(func.count())
            .select_from(Attendee)
            .where(Attendee.event_id == event_id, Attendee.checked_in_at.is_not(None))
        )
        or 0
    )

    return {"total": int(total), "checked_in": int(checked_in), "not_checked_in": int(total - checked_in)}
