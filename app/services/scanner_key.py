import secrets


def generate_scanner_key(length_bytes: int = 24) -> str:
    # URL-safe, long enough, easy to paste into headers
    return secrets.token_urlsafe(length_bytes)
