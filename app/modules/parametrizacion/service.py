from sqlalchemy.orm import Session
from app.shared.models import PeriodoAcademico, Auditoria
from fastapi import HTTPException, status
from .schemas import AnioEscolarCreate

class AnioEscolarService:
    @staticmethod
    def crear_anio_escolar(db: Session, anio_in: AnioEscolarCreate, forzar: bool = False):
        # 1. Lógica de activación (Solo uno puede estar activo)
        if anio_in.activo:
            anio_activo_actual = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
            
            # Si hay conflicto y NO se ha forzado la acción
            if anio_activo_actual and not forzar:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un año activo ({anio_activo_actual.nombre}). ¿Desea desactivarlo y activar el nuevo?"
                )
            
            # Si se forzó la acción, desactivamos el anterior
            if anio_activo_actual and forzar:
                anio_activo_actual.activo = False

        # 2. Extraer el año inicial del nombre (ej: "2025-2026" -> 2025)
        anio_inicial = int(anio_in.nombre.split('-')[0])

        # 3. Crear el nuevo registro
        nuevo_anio = PeriodoAcademico(
            nombre=anio_in.nombre,
            anio=anio_inicial,
            activo=anio_in.activo
        )
        db.add(nuevo_anio)
        db.flush() 

        # 4. Registrar Auditoría 
        nueva_auditoria = Auditoria(
            tabla="periodo_academico",
            id_registro=nuevo_anio.id_periodo,
            accion="CREAR_ANIO",
            usuario="ADMIN_SISTEMA" 
        )
        db.add(nueva_auditoria)
        
        db.commit()
        db.refresh(nuevo_anio)
        return nuevo_anio