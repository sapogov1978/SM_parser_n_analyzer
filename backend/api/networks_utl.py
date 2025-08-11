from sqlalchemy.orm import Session
from db.models import Network

def get_or_create_other(db: Session):
    other = db.query(Network).filter(Network.name == "other").first()
    if not other:
        other = Network(name="other", domain="other.local")
        db.add(other)
        db.commit()
        db.refresh(other)
    return other