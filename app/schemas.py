from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Stage = Literal["cutting", "stitching", "finishing", "qc", "packed"]


class ScanCreate(BaseModel):
    scan_id: str
    piece_id: str
    stage: Stage
    employee_id: str
    ts: datetime

    @field_validator("ts")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("ts must include a timezone")
        return value.astimezone(timezone.utc)


class ScanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    piece_id: str
    stage: str
    employee_id: str
    ts: datetime

    @field_validator("ts")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DailyThroughput(BaseModel):
    date: str
    counts: dict[str, int]
