import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.event import Event
from app.models.user import User
from app.schemas.attendee import (
    AttendeeBulkCreate,
    AttendeeCreate,
    AttendeeListOut,
    AttendeeOut,
    QRPayloadOut,
)
from app.services.qr import generate_unique_qr_token

router = APIRouter(prefix="/events/{event_id}/attendees", tags=["attendees"])


def _get_owned_event(db: Session, user: User, event_id: uuid.UUID) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return event


@router.post("", response_model=AttendeeOut, status_code=201)
def create_attendee(
    event_id: uuid.UUID,
    payload: AttendeeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Attendee:
    _get_owned_event(db, user, event_id)

    token = generate_unique_qr_token(db)
    attendee = Attendee(
        event_id=event_id,
        full_name=payload.full_name,
        email=str(payload.email) if payload.email else None,
        qr_token=token,
    )
    db.add(attendee)
    db.commit()
    db.refresh(attendee)
    return attendee


@router.post("/bulk", response_model=list[AttendeeOut], status_code=201)
def bulk_create_attendees(
    event_id: uuid.UUID,
    payload: AttendeeBulkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Attendee]:
    _get_owned_event(db, user, event_id)

    created: list[Attendee] = []
    for a in payload.attendees:
        token = generate_unique_qr_token(db)
        attendee = Attendee(
            event_id=event_id,
            full_name=a.full_name,
            email=str(a.email) if a.email else None,
            qr_token=token,
        )
        db.add(attendee)
        created.append(attendee)

    db.commit()
    for attendee in created:
        db.refresh(attendee)

    return created


@router.get("", response_model=AttendeeListOut)
def list_attendees(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, description="Search by name or email"),
) -> AttendeeListOut:
    _get_owned_event(db, user, event_id)

    base_filter = [Attendee.event_id == event_id]
    if q:
        like = f"%{q.strip()}%"
        base_filter.append(or_(Attendee.full_name.ilike(like), Attendee.email.ilike(like)))

    total = db.scalar(select(func.count()).select_from(Attendee).where(*base_filter)) or 0

    rows = db.scalars(
        select(Attendee)
        .where(*base_filter)
        .order_by(Attendee.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return AttendeeListOut(items=rows, limit=limit, offset=offset, total=total)


@router.get("/{attendee_id}", response_model=AttendeeOut)
def get_attendee(
    event_id: uuid.UUID,
    attendee_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Attendee:
    _get_owned_event(db, user, event_id)

    attendee = db.get(Attendee, attendee_id)
    if not attendee or attendee.event_id != event_id:
        raise HTTPException(status_code=404, detail="Attendee not found")

    return attendee


@router.get("/{attendee_id}/qr", response_model=QRPayloadOut)
def get_attendee_qr_payload(
    event_id: uuid.UUID,
    attendee_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QRPayloadOut:
    _get_owned_event(db, user, event_id)

    attendee = db.get(Attendee, attendee_id)
    if not attendee or attendee.event_id != event_id:
        raise HTTPException(status_code=404, detail="Attendee not found")

    # MVP payload: token only (you embed this in QR)
    # Later: payload could be a full URL to a check-in web page.
    payload = attendee.qr_token
    return QRPayloadOut(qr_token=attendee.qr_token, payload=payload)
