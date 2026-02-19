from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.event import Event
from app.models.user import User
from app.schemas.checkin import CheckInRequest, CheckInResponse

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("", response_model=CheckInResponse)
def checkin(
    payload: CheckInRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_scanner_key: str | None = Header(default=None, alias="X-Scanner-Key"),
) -> CheckInResponse:
    attendee = db.scalar(select(Attendee).where(Attendee.qr_token == payload.qr_token))
    if not attendee:
        raise HTTPException(status_code=404, detail="Invalid QR token")

    event = db.get(Event, attendee.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # ✅ Auth logic:
    # - If JWT user is present, must be the event owner
    # - Otherwise require X-Scanner-Key to match the event's scanner_key
    if user is not None:
        if event.owner_user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    else:
        if not x_scanner_key or x_scanner_key != event.scanner_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid scanner key",
            )

    # Idempotent response if already checked in
    if attendee.checked_in_at is not None:
        return CheckInResponse(
            attendee_id=attendee.id,
            event_id=attendee.event_id,
            full_name=attendee.full_name,
            checked_in_at=attendee.checked_in_at,
            already_checked_in=True,
        )

    now = datetime.now(timezone.utc)

    # Atomic update to avoid double-checkins on race
    result = db.execute(
        update(Attendee)
        .where(Attendee.id == attendee.id, Attendee.checked_in_at.is_(None))
        .values(checked_in_at=now)
        .returning(Attendee.checked_in_at)
    ).first()

    db.commit()

    if not result:
        db.refresh(attendee)
        return CheckInResponse(
            attendee_id=attendee.id,
            event_id=attendee.event_id,
            full_name=attendee.full_name,
            checked_in_at=attendee.checked_in_at,  # should be set by winner
            already_checked_in=True,
        )

    checked_time = result[0]
    return CheckInResponse(
        attendee_id=attendee.id,
        event_id=attendee.event_id,
        full_name=attendee.full_name,
        checked_in_at=checked_time,
        already_checked_in=False,
    )


# from datetime import datetime, timezone

# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy import select, update
# from sqlalchemy.orm import Session

# from app.api.deps import get_current_user
# from app.db.session import get_db
# from app.models.attendee import Attendee
# from app.models.event import Event
# from app.models.user import User
# from app.schemas.checkin import CheckInRequest, CheckInResponse

# router = APIRouter(prefix="/checkin", tags=["checkin"])


# @router.post("", response_model=CheckInResponse)
# def checkin(
#     payload: CheckInRequest,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ) -> CheckInResponse:
#     """
#     Idempotent check-in:
#     - Invalid token => 404
#     - Already checked in => return already_checked_in=True
#     - First check-in => set checked_in_at (atomic update) and return already_checked_in=False
#     """
#     attendee = db.scalar(select(Attendee).where(Attendee.qr_token == payload.qr_token))
#     if not attendee:
#         raise HTTPException(status_code=404, detail="Invalid QR token")

#     # ensure the scanning user owns the event (owner-only MVP)
#     event = db.get(Event, attendee.event_id)
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found")
#     if event.owner_user_id != user.id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

#     # If already checked in, return idempotent success
#     if attendee.checked_in_at is not None:
#         return CheckInResponse(
#             attendee_id=attendee.id,
#             event_id=attendee.event_id,
#             full_name=attendee.full_name,
#             checked_in_at=attendee.checked_in_at,
#             already_checked_in=True,
#         )

#     now = datetime.now(timezone.utc)

#     # Atomic update: only set if checked_in_at is NULL
#     result = db.execute(
#         update(Attendee)
#         .where(Attendee.id == attendee.id, Attendee.checked_in_at.is_(None))
#         .values(checked_in_at=now)
#         .returning(Attendee.checked_in_at)
#     ).first()

#     db.commit()

#     # If another request won the race, result will be None
#     if not result:
#         db.refresh(attendee)
#         return CheckInResponse(
#             attendee_id=attendee.id,
#             event_id=attendee.event_id,
#             full_name=attendee.full_name,
#             checked_in_at=attendee.checked_in_at,  # type: ignore[arg-type]
#             already_checked_in=True,
#         )

#     checked_time = result[0]
#     return CheckInResponse(
#         attendee_id=attendee.id,
#         event_id=attendee.event_id,
#         full_name=attendee.full_name,
#         checked_in_at=checked_time,
#         already_checked_in=False,
#     )
