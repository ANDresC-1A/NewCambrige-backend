from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.modules.parametrizacion import service
from app.modules.parametrizacion.schemas import PeriodoAcademicoResponse
from app.modules.auth.deps import require_roles

router = APIRouter()
@router.get("/periodos/", response_model=List[PeriodoAcademicoResponse])
def listar_periodos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user =  Depends(require_roles(["admin", "titular", "secretaria",  "tesoreria"]))
):
    return service.get_all(db, skip, limit)
