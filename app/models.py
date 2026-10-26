from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


STAGES = ("cutting", "stitching", "finishing", "qc", "packed")


class Piece(Base):
    __tablename__ = "pieces"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)


class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = (
        UniqueConstraint("scan_id", name="uq_scans_scan_id"),
        Index("ix_scans_piece_ts", "piece_id", "ts"),
        Index("ix_scans_ts_stage", "ts", "stage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(String(100), nullable=False)
    piece_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("pieces.id", name="fk_scans_piece_id_pieces"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
