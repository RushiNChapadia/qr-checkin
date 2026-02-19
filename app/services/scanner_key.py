import secrets

def generate_scanner_key(length_bytes: int = 48) -> str:
    return secrets.token_urlsafe(length_bytes)
