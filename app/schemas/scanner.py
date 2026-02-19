from pydantic import BaseModel


class ScannerKeyOut(BaseModel):
    scanner_key: str
