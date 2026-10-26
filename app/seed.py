from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Piece

SEED_PIECE_IDS = ("piece-001", "piece-002", "piece-003")


def seed(db: Session) -> None:
    for piece_id in SEED_PIECE_IDS:
        if db.get(Piece, piece_id) is None:
            db.add(Piece(id=piece_id))
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
