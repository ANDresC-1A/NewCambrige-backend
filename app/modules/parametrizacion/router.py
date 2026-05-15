from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from .schemas import AnioEscolarCreate, AnioEscolarRead, AnioEscolarUpdate
from .service import crear_anio_escolar, get_anios_all, update_estado_anio

router = APIRouter(prefix="/parametrizacion", tags=["Parametrización"])

# --- REGISTRAR AÑO ESCOLAR ---

@router.post("/anio-escolar", response_model=AnioEscolarRead, status_code=status.HTTP_201_CREATED)
def registrar_anio(
    payload: AnioEscolarCreate, 
    forzar: bool = Query(False),
    db: Session = Depends(get_db)
):
    return crear_anio_escolar(
        db, 
        payload.anio_inicio, 
        payload.activo, 
        "USUARIO_PRUEBA", 
        forzar
    )

# --- LISTAR AÑOS ESCOLARES ---
@router.get("/anio-escolar", response_model=List[AnioEscolarRead])
def listar_anios(db: Session = Depends(get_db)):
  
    return get_anios_all(db)

# --- ACTUALIZAR AÑO ESCOLAR ---
@router.patch("/anio-escolar/{id_periodo}", response_model=AnioEscolarRead)
def actualizar_estado_anio(
    id_periodo: int,
    payload: AnioEscolarUpdate,
    forzar: bool = Query(False, description="Desactivar el año actual para activar este"),
    db: Session = Depends(get_db)
):
    actualizado = update_estado_anio(
        db, 
        id_periodo, 
        payload.activo, # Solo pasamos el booleano
        "USUARIO_PRUEBA", 
        forzar
    )
    
    if not actualizado:
        raise HTTPException(status_code=404, detail="Año escolar no encontrado")
        
    return actualizado