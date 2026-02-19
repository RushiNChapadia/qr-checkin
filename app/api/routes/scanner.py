import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.scanner import ScannerKeyOut
from app.services.scanner_key import generate_scanner_key

router = APIRouter(prefix="/events", tags=["scanner"])


def _get_owned_event(db: Session, user: User, event_id: uuid.UUID) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return event


@router.get("/{event_id}/scanner-key", response_model=ScannerKeyOut)
def get_scanner_key(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScannerKeyOut:
    event = _get_owned_event(db, user, event_id)
    return ScannerKeyOut(scanner_key=event.scanner_key)


@router.post("/{event_id}/scanner-key/rotate", response_model=ScannerKeyOut)
def rotate_scanner_key(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScannerKeyOut:
    event = _get_owned_event(db, user, event_id)
    event.scanner_key = generate_scanner_key()
    db.add(event)
    db.commit()
    db.refresh(event)
    return ScannerKeyOut(scanner_key=event.scanner_key)
