from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from .schemas import AnioEscolarCreate, AnioEscolarRead, AnioEscolarUpdate, TipoPruebaUpdate, TipoPruebaRead
from .service import crear_anio_escolar, get_anios_all, update_anio_escolar, get_tipos_prueba, update_tipo_prueba

router = APIRouter(prefix="/parametrizacion", tags=["Parametrización"])

#PERIDO ACADEMICO
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

#TIPOS DE PRUEBA

@router.get("/tipos-prueba", response_model=List[TipoPruebaRead])
def listar_tipos_prueba(db: Session = Depends(get_db)):
    """Muestra los tipos de prueba fijos del sistema."""
    return get_tipos_prueba(db)

@router.patch("/tipos-prueba/{id_tipo_prueba}", response_model=TipoPruebaRead)
def editar_rangos_prueba(
    id_tipo_prueba: int, 
    payload: TipoPruebaUpdate, 
    db: Session = Depends(get_db)
):
    """Permite editar únicamente los rangos de grados (min y max)."""
    try:
        actualizado = update_tipo_prueba(db, id_tipo_prueba, payload.dict())
        if not actualizado:
            raise HTTPException(status_code=404, detail="Tipo de prueba no encontrado")
        return actualizado
        
    # Aquí capturamos los mensajes de error de BR249 y de validación 1-12
    except ValueError as e:
        # Pydantic devuelve los errores en formato lista, extraemos el mensaje limpio
        errores = e.errors() if hasattr(e, 'errors') else [{"msg": str(e)}]
        mensaje_limpio = errores[0]['msg'] if errores else str(e)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=mensaje_limpio
        )