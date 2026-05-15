from sqlalchemy.orm import Session
from typing import List, Optional
from app.shared.models import PeriodoAcademico, Auditoria
from fastapi import HTTPException, status

# ============ LECTURA ============
def get_anios_all(db: Session) -> List[PeriodoAcademico]:
    return db.query(PeriodoAcademico).order_by(PeriodoAcademico.anio.desc()).all()

def get_anio_by_id(db: Session, id_periodo: int) -> Optional[PeriodoAcademico]:
    return db.query(PeriodoAcademico).filter(PeriodoAcademico.id_periodo == id_periodo).first()

# ============ CREACIÓN ============

def crear_anio_escolar(db: Session, anio_inicio: int, activo: bool, usuario_nombre: str, forzar: bool = False):
    nombre_formateado = f"{anio_inicio}-{anio_inicio + 1}"

    anio_existente = db.query(PeriodoAcademico).filter(PeriodoAcademico.anio == anio_inicio).first()
    
    if anio_existente:
        raise HTTPException(
            status_code=400, 
            detail=f"El año escolar {anio_inicio}-{anio_inicio + 1} ya está registrado en el sistema."
        )
    # ---------------------------------------

    nombre_formateado = f"{anio_inicio}-{anio_inicio + 1}"
   
    if activo:
        anio_actual = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
        if anio_actual and not forzar:
            raise HTTPException(
                status_code=409, 
                detail=f"Ya existe un año activo: {anio_actual.nombre}"
            )
        if anio_actual and forzar:
            anio_actual.activo = False

 
    nuevo = PeriodoAcademico(
        nombre=nombre_formateado, 
        anio=anio_inicio,         
        activo=activo
    )
    db.add(nuevo)
    db.flush()

    # Auditoría
    db.add(Auditoria(
        tabla="periodo_academico", 
        id_registro=nuevo.id_periodo, 
        accion="CREAR", 
        usuario=usuario_nombre
    ))
    
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ============ ACTUALIZACIÓN ============
def update_estado_anio(db: Session, id_periodo: int, nuevo_estado: bool, usuario_nombre: str, forzar: bool = False):
    anio_obj = get_anio_by_id(db, id_periodo)
    if not anio_obj:
        return None

    if nuevo_estado is True and anio_obj.activo is False:
        anio_activo_otro = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.activo == True, 
            PeriodoAcademico.id_periodo != id_periodo
        ).first()
        
        if anio_activo_otro:
            if not forzar:
                raise HTTPException(
                    status_code=409, 
                    detail=f"No puedes activar este año porque {anio_activo_otro.nombre} ya está activo."
                )
            else:
                anio_activo_otro.activo = False

    anio_obj.activo = nuevo_estado

    db.add(Auditoria(
        tabla="periodo_academico", 
        id_registro=id_periodo, 
        accion="CAMBIO_ESTADO_ACTIVACION", 
        usuario=usuario_nombre
    ))
    
    db.commit()
    db.refresh(anio_obj)
    return anio_obj