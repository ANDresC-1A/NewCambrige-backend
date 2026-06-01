from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EstudianteImportBase(BaseModel):
    documento: Optional[str] = None
    nombre: Optional[str] = None
    grado: Optional[str] = None
    curso: Optional[str] = None
    jornada: Optional[str] = None

class DocenteImportBase(BaseModel):
    documento: Optional[str] = None
    nombre: Optional[str] = None
    grado_titular: Optional[str] = None
    curso_titular: Optional[str] = None

class CargaMasivaRequest(BaseModel):
    tipo: str # "estudiante" o "docente"
    datos: List[dict] # Se puede hacer un list de BaseModel para validacion mas estricta luego

class CargaIndividualRequest(BaseModel):
    tipo: str
    datos: dict

class EjecucionBotResponse(BaseModel):
    id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado: str
    registros_estudiantes: int
    registros_docentes: int
    errores: int
    tipo_ejecucion: str

    class Config:
        from_attributes = True

class ErrorImportacionResponse(BaseModel):
    id: int
    ejecucion_id: int
    tipo_origen: str
    registro_referencia: Optional[str] = None
    mensaje_error: str
    fecha_error: datetime

    class Config:
        from_attributes = True

class SincronizarRequest(BaseModel):
    ejecucion_id: int
