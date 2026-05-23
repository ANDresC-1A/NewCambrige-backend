from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.shared.models import PeriodoAcademico
from app.modules.paz_y_salvo import service
from app.modules.paz_y_salvo.schemas import FirmasResponse, FirmasUpdate, EstadoPazSalvoResponse, RectoriaFirmaRequest, RectoriaFirmaResponse, EstudiantePendienteResponse
from app.modules.auth.deps import require_roles
from app.modules.usuarios.models import Usuario, RolUsuario, Rol

router = APIRouter()

def _validar_acceso_periodo(periodo_id: Optional[int], current_user: Usuario, db: Session) -> int:
    roles = [r[0] for r in db.query(Rol.nombre).join(
        RolUsuario, Rol.id_rol == RolUsuario.id_rol
    ).filter(RolUsuario.id_usuario == current_user.id_usuario).all()]

    if periodo_id is None:
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.activo == True
        ).first()
        if not periodo:
            raise HTTPException(status_code=404, detail="No hay un periodo académico activo")
        return periodo.id_periodo
    
    periodo = db.query(PeriodoAcademico).filter(
        PeriodoAcademico.id_periodo == periodo_id
    ).first()
    if not periodo:
        raise HTTPException(status_code=404, detail=f"Periodo {periodo_id} no encontrado")
    
    if not periodo.activo and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Solo el administrador puede acceder a periodos inactivos")
    
    return periodo_id
    

@router.get("/estudiante/{estudiante_id}", response_model=EstadoPazSalvoResponse)
def obtener_estado_paz_salvo(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria", "rectoria"]))
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    resultado = service.get_estado_completo(db, estudiante_id, periodo_id_valido)
    if not resultado:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return resultado

@router.get("/sin-firmar/periodo/{periodo_id}")
def estudiantes_sin_firmas(
    periodo_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "rectoria"]))
):
    return service.get_sin_firmas(db, periodo_id)

@router.get("/firmas/{estudiante_id}", response_model=FirmasResponse)
def obtener_firmas(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria"]))
):
    periodo_id_validado = _validar_acceso_periodo(periodo_id, current_user, db)
    firmas = service.get_firmas(db, estudiante_id, periodo_id_validado)
    if not firmas:
        raise HTTPException(status_code=404, detail="No se encontraron firmas")
    return {
        "id_firma": firmas.id_firma,
        "id_estudiante": firmas.id_estudiante,
        "id_periodo": firmas.id_periodo,
        "banda": firmas.banda,
        "tesoreria": firmas.tesoreria,
        "uniforme": firmas.uniforme,
        "rectoria": firmas.rectoria,
        "salon": service._get_salon(firmas),
        "updated_at": firmas.updated_at,
    }

@router.put("/firmas/{estudiante_id}", response_model=FirmasResponse)
def actualizar_firmas(
    estudiante_id: int,
    data: FirmasUpdate,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria", "rectoria"]))
):
    
    data_dict = data.model_dump(exclude_unset=True)
    if data_dict.get("rectoria") is True:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La firma de Rectoría debe hacerse desde POST /api/paz-salvo/rectoria/{estudiante_id}")

    periodo_id_validado = _validar_acceso_periodo(periodo_id, current_user, db)
    firmas = service.update_firmas(db, estudiante_id, periodo_id_validado, data.model_dump(exclude_unset=True))
    if not firmas:
        raise HTTPException(status_code=404, detail="Estudiante o periodo no encontrado")
    return {
        "id_firma": firmas.id_firma,
        "id_estudiante": firmas.id_estudiante,
        "id_periodo": firmas.id_periodo,
        "banda": firmas.banda,
        "tesoreria": firmas.tesoreria,
        "uniforme": firmas.uniforme,
        "rectoria": firmas.rectoria,
        "salon": service._get_salon(firmas),
        "updated_at": firmas.updated_at,
    }

@router.post("/rectoria/{estudiante_id}", response_model=RectoriaFirmaResponse, summary="Firma final de Rectoría")
def firmar_rectoria(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    body: Optional[RectoriaFirmaRequest] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_validado = _validar_acceso_periodo(periodo_id, current_user, db)
    resultado = service.firmar_rectoria(
        db=db,
        estudiante_id=estudiante_id,
        usuario_nombre=current_user.nombre,
        periodo_id=periodo_id_validado,
    )

    if "error" in resultado:
        raise HTTPException(status_code=resultado.get("codigo", 400), detail=resultado["error"])

    return resultado

@router.get("/periodos", summary="Listar periodos académicos")
def listar_periodos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "secretaria", "rectoria"]))
):
    roles_usuario = db.query(Rol.nombre).join(
        RolUsuario, Rol.id_rol == RolUsuario.id_rol
    ).filter(RolUsuario.id_usuario == current_user.id_usuario).all()
    roles = [r[0] for r in roles_usuario]

    if "admin" in roles:
        periodos = db.query(PeriodoAcademico).order_by(
            PeriodoAcademico.id_periodo.desc()
        ).all()
    else:
        periodos = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.activo == True
        ).all()
    
    return [
        {
            "id_periodo": p.id_periodo,
            "nombre": p.nombre,
            "fecha_inicio": p.fecha_inicio,
            "fecha_fin": p.fecha_fin,
            "activo": p.activo,
        }
        for p in periodos
    ]

@router.get("/pendientes", response_model=List[EstudiantePendienteResponse], summary="Estudiantes con paz y salvo pendiente")
def listar_pendientes(
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "secretaria", "rectoria"])),
):
    return service.get_pendientes(db, periodo_id)