import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.event import EventCreate, EventListOut, EventOut

from app.services.scanner_key import generate_scanner_key

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut, status_code=201)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Event:
    event = Event(
        owner_user_id=user.id,
        name=payload.name,
        venue=payload.venue,
        start_time=payload.start_time,
        scanner_key=generate_scanner_key(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=EventListOut)
def list_events(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> EventListOut:
    total = db.scalar(select(func.count()).select_from(Event).where(Event.owner_user_id == user.id)) or 0

    rows = db.scalars(
        select(Event)
        .where(Event.owner_user_id == user.id)
        .order_by(Event.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return EventListOut(items=rows, limit=limit, offset=offset, total=total)


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return event
