"""Create pieces and scans.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pieces",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.String(length=100), nullable=False),
        sa.Column("piece_id", sa.String(length=100), nullable=False),
        sa.Column("stage", sa.String(length=20), nullable=False),
        sa.Column("employee_id", sa.String(length=100), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id", name="uq_scans_scan_id"),
    )
    op.create_index("ix_scans_piece_id", "scans", ["piece_id"], unique=False)
    op.create_index("ix_scans_piece_ts", "scans", ["piece_id", "ts"], unique=False)
    op.create_index("ix_scans_ts_stage", "scans", ["ts", "stage"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scans_ts_stage", table_name="scans")
    op.drop_index("ix_scans_piece_ts", table_name="scans")
    op.drop_index("ix_scans_piece_id", table_name="scans")
    op.drop_table("scans")
    op.drop_table("pieces")
