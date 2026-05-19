# app/modules/parametrizacion/router.py
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db

from .schemas import AnioEscolarCreate, AnioEscolarRead, AnioEscolarUpdate
from .service import crear_anio_escolar, get_anios_all, update_anio_escolar

router = APIRouter(prefix="/parametrizacion", tags=["Parametrización"])

@router.post("/anio-escolar", response_model=AnioEscolarRead, status_code=status.HTTP_201_CREATED)
def registrar_anio(
    payload: AnioEscolarCreate, 
    forzar: bool = Query(False, description="Forzar la desactivación del año anterior"),
    db: Session = Depends(get_db)
):
    return crear_anio_escolar(db, payload, "USUARIO_PRUEBA", forzar)

@router.get("/anio-escolar", response_model=List[AnioEscolarRead])
def listar_anios(db: Session = Depends(get_db)):
    return get_anios_all(db)


@router.patch("/anio-escolar/{id_periodo}", response_model=AnioEscolarRead)
def actualizar_anio(
    id_periodo: int,
    payload: AnioEscolarUpdate,
    forzar: bool = Query(False, description="Forzar la desactivación del año actual para activar este"),
    db: Session = Depends(get_db)
):
   
    datos_filtrados = payload.dict(exclude_unset=True)
    
    actualizado = update_anio_escolar(db, id_periodo, datos_filtrados, "USUARIO_PRUEBA", forzar)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Año escolar no encontrado")
        
    return actualizado