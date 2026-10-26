from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import authenticate, manager_only, scanner_only
from app.database import get_db
from app.models import STAGES, Piece, Scan
from app.schemas import DailyThroughput, ScanCreate, ScanRead, TokenRequest, TokenResponse

app = FastAPI(title="Production Events API", version="1.0.0")
DbSession = Annotated[Session, Depends(get_db)]


def _matches_scan(existing: Scan, request: ScanCreate) -> bool:
    existing_ts = existing.ts
    if existing_ts.tzinfo is None:
        existing_ts = existing_ts.replace(tzinfo=timezone.utc)
    return (
        existing.piece_id == request.piece_id
        and existing.stage == request.stage
        and existing.employee_id == request.employee_id
        and existing_ts == request.ts
    )


@app.post("/auth/token", response_model=TokenResponse)
def issue_token(credentials: TokenRequest) -> TokenResponse:
    token = authenticate(credentials)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return TokenResponse(access_token=token)


@app.post("/scans", response_model=ScanRead, status_code=status.HTTP_201_CREATED)
def create_scan(
    request: ScanCreate,
    db: DbSession,
    response: Response,
    _: Annotated[dict[str, str], Depends(scanner_only)],
) -> ScanRead:
    existing = db.scalar(select(Scan).where(Scan.scan_id == request.scan_id))
    if existing is not None:
        if not _matches_scan(existing, request):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="scan_id has already been used with a different payload",
            )
        response.status_code = status.HTTP_200_OK
        return ScanRead.model_validate(existing)

    if db.get(Piece, request.piece_id) is None:
        raise HTTPException(status_code=404, detail=f"Piece '{request.piece_id}' not found")

    latest_stage = db.scalar(
        select(Scan.stage)
        .where(Scan.piece_id == request.piece_id)
        .order_by(Scan.id.desc())
        .limit(1)
    )
    expected_stage = STAGES[0] if latest_stage is None else (
        STAGES[STAGES.index(latest_stage) + 1]
        if latest_stage in STAGES and latest_stage != STAGES[-1]
        else None
    )
    if request.stage != expected_stage:
        expected = expected_stage or "no further stage (piece is already packed)"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Out-of-order stage for piece '{request.piece_id}': expected {expected}, got {request.stage}",
        )

    scan = Scan(
        scan_id=request.scan_id,
        piece_id=request.piece_id,
        stage=request.stage,
        employee_id=request.employee_id,
        ts=request.ts,
    )
    db.add(scan)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(Scan).where(Scan.scan_id == request.scan_id))
        if existing is None:
            raise
        if not _matches_scan(existing, request):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="scan_id has already been used with a different payload",
            )
        response.status_code = status.HTTP_200_OK
        return ScanRead.model_validate(existing)
    db.refresh(scan)
    return ScanRead.model_validate(scan)


@app.get("/pieces/{piece_id}/timeline", response_model=list[ScanRead])
def piece_timeline(
    piece_id: str,
    db: DbSession,
    _: Annotated[dict[str, str], Depends(manager_only)],
) -> list[ScanRead]:
    if db.get(Piece, piece_id) is None:
        raise HTTPException(status_code=404, detail=f"Piece '{piece_id}' not found")
    scans = db.scalars(
        select(Scan)
        .where(Scan.piece_id == piece_id)
        .order_by(Scan.ts.asc(), Scan.id.asc())
    ).all()
    return [ScanRead.model_validate(scan) for scan in scans]


@app.get("/reports/daily-throughput", response_model=DailyThroughput)
def daily_throughput(
    report_date: date = Query(alias="date"),
    db: Session = Depends(get_db),
    _: dict[str, str] = Depends(manager_only),
) -> DailyThroughput:
    start = datetime.combine(report_date, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    rows = db.execute(
        select(Scan.stage, func.count(Scan.id))
        .where(Scan.ts >= start, Scan.ts < end)
        .group_by(Scan.stage)
    ).all()
    counts = {stage: 0 for stage in STAGES}
    counts.update({stage: count for stage, count in rows})
    return DailyThroughput(date=report_date.isoformat(), counts=counts)
