from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from .schemas import AnioEscolarCreate, AnioEscolarRead
from .service import AnioEscolarService

router = APIRouter(prefix="/parametrizacion", tags=["Parametrización"])

@router.post("/anio-escolar", response_model=AnioEscolarRead, status_code=status.HTTP_201_CREATED)
def registrar_anio(
    payload: AnioEscolarCreate, 
    forzar: bool = Query(False, description="Forzar la desactivación del año anterior"),
    db: Session = Depends(get_db)
):
  
    return AnioEscolarService.crear_anio_escolar(db, payload, forzar)