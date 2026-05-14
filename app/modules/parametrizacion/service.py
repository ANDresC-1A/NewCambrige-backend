from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models import PeriodoAcademico

def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[PeriodoAcademico]:
    return db.query(PeriodoAcademico).offset(skip).limit(limit).all()