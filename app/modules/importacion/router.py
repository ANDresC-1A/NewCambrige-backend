from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.importacion.schemas import (
    CargaMasivaRequest, 
    CargaIndividualRequest, 
    EjecucionBotResponse, 
    ErrorImportacionResponse,
    SincronizarRequest
)
from app.modules.importacion.service import ImportacionService
# Si tienes dependencias de auth: from app.modules.auth.dependencies import get_current_user

router = APIRouter()

def get_importacion_service(db: Session = Depends(get_db)):
    return ImportacionService(db)

@router.post("/scraping", summary="Inicia el scraping desde WebColegios")
def iniciar_scraping(service: ImportacionService = Depends(get_importacion_service)):
    # usuario = Depends(get_current_user) # Placeholder para futura integracion de auth
    return service.iniciar_scraping(usuario_id=None)

@router.post("/scraping/estudiantes", summary="Inicia el scraping solo de estudiantes")
def iniciar_scraping_estudiantes(service: ImportacionService = Depends(get_importacion_service)):
    return service.iniciar_scraping_estudiantes(usuario_id=None)

@router.post("/scraping/docentes", summary="Inicia el scraping solo de docentes")
def iniciar_scraping_docentes(service: ImportacionService = Depends(get_importacion_service)):
    return service.iniciar_scraping_docentes(usuario_id=None)

@router.post("/carga-masiva", summary="Procesa un array de registros y los inserta en staging")
def carga_masiva(request: CargaMasivaRequest, service: ImportacionService = Depends(get_importacion_service)):
    return service.ejecutar_carga_masiva(request, usuario_id=None)

@router.post("/carga-individual", summary="Inserta un registro individual en staging")
def carga_individual(request: CargaIndividualRequest, service: ImportacionService = Depends(get_importacion_service)):
    return service.ejecutar_carga_individual(request, usuario_id=None)

@router.get("/ejecuciones", response_model=List[EjecucionBotResponse], summary="Obtiene el historial de ejecuciones")
def listar_ejecuciones(limit: int = 100, skip: int = 0, service: ImportacionService = Depends(get_importacion_service)):
    return service.obtener_ejecuciones(limit=limit, skip=skip)

@router.get("/ejecuciones/{id}", response_model=EjecucionBotResponse, summary="Obtiene una ejecucion especifica")
def obtener_ejecucion(id: int, service: ImportacionService = Depends(get_importacion_service)):
    ej = service.obtener_ejecucion(id)
    if not ej:
        raise HTTPException(status_code=404, detail="Ejecucion no encontrada")
    return ej

@router.get("/errores", response_model=List[ErrorImportacionResponse], summary="Obtiene el log de errores de importacion")
def listar_errores(limit: int = 100, skip: int = 0, service: ImportacionService = Depends(get_importacion_service)):
    return service.obtener_errores(limit=limit, skip=skip)

@router.post("/sincronizar-estudiantes", summary="Sincroniza estudiantes desde staging hacia la tabla oficial")
def sincronizar_estudiantes(request: SincronizarRequest, service: ImportacionService = Depends(get_importacion_service)):
    return service.sincronizar_estudiantes(ejecucion_id=request.ejecucion_id)
