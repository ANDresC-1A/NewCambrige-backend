from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.importacion.schemas import (
    CargaMasivaRequest, 
    CargaIndividualRequest, 
    EjecucionBotResponse, 
    SincronizarRequest
)
from app.modules.importacion.service import ImportacionService
from app.modules.auth.deps import require_roles
from app.modules.usuarios.models import Usuario

router = APIRouter()

def get_importacion_service(db: Session = Depends(get_db)):
    return ImportacionService(db)

@router.post("/scraping", summary="Inicia el scraping desde WebColegios")
def iniciar_scraping(
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.iniciar_scraping(usuario_id=current_user.id_usuario)

@router.post("/scraping/estudiantes", summary="Inicia el scraping solo de estudiantes")
def iniciar_scraping_estudiantes(
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.iniciar_scraping_estudiantes(usuario_id=current_user.id_usuario)

@router.post("/scraping/docentes", summary="Inicia el scraping solo de docentes")
def iniciar_scraping_docentes(
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.iniciar_scraping_docentes(usuario_id=current_user.id_usuario)

@router.post("/carga-masiva", summary="Procesa un array de registros y los inserta en staging")
def carga_masiva(
    request: CargaMasivaRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.ejecutar_carga_masiva(request, usuario_id=current_user.id_usuario)

@router.post("/carga-individual", summary="Inserta un registro individual en staging")
def carga_individual(
    request: CargaIndividualRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.ejecutar_carga_individual(request, usuario_id=current_user.id_usuario)

@router.get("/ejecuciones", response_model=List[EjecucionBotResponse], summary="Obtiene el historial de ejecuciones")
def listar_ejecuciones(
    limit: int = 100, 
    skip: int = 0, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.obtener_ejecuciones(limit=limit, skip=skip)

@router.get("/ejecuciones/{id}", response_model=EjecucionBotResponse, summary="Obtiene una ejecucion especifica")
def obtener_ejecucion(
    id: int, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    ej = service.obtener_ejecucion(id)
    if not ej:
        raise HTTPException(status_code=404, detail="Ejecucion no encontrada")
    return ej


@router.post("/sincronizar-estudiantes", summary="Sincroniza estudiantes desde staging hacia la tabla oficial")
def sincronizar_estudiantes(
    request: SincronizarRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.sincronizar_estudiantes(ejecucion_id=request.ejecucion_id)

@router.post("/sincronizar-docentes", summary="Sincroniza docentes desde staging hacia la tabla oficial")
def sincronizar_docentes(
    request: SincronizarRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.sincronizar_docentes(ejecucion_id=request.ejecucion_id)
