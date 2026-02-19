import secrets
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendee import Attendee


def generate_unique_qr_token(db: Session, length_bytes: int = 32, max_tries: int = 5) -> str:
    """
    Generates a URL-safe random token and ensures uniqueness in DB.
    length_bytes=32 => long token (good security).
    """
    for _ in range(max_tries):
        token = secrets.token_urlsafe(length_bytes)
        exists = db.scalar(select(Attendee.id).where(Attendee.qr_token == token))
        if not exists:
            return token
    # extremely unlikely unless DB is under attack or misconfigured
    raise RuntimeError("Failed to generate unique QR token")
