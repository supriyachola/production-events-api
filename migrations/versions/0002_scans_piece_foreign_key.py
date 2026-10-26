"""Add the scans-to-pieces foreign key.

Revision ID: 0002_scans_piece_foreign_key
Revises: 0001_initial
"""
from alembic import op

revision = "0002_scans_piece_foreign_key"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

CONSTRAINT_NAME = "fk_scans_piece_id_pieces"


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("scans", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                CONSTRAINT_NAME,
                "pieces",
                ["piece_id"],
                ["id"],
            )
    else:
        op.create_foreign_key(
            CONSTRAINT_NAME,
            "scans",
            "pieces",
            ["piece_id"],
            ["id"],
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("scans", recreate="always") as batch_op:
            batch_op.drop_constraint(CONSTRAINT_NAME, type_="foreignkey")
    else:
        op.drop_constraint(CONSTRAINT_NAME, "scans", type_="foreignkey")
