from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SemaforoEstado:
    VERDE = "VERDE"        
    AMARILLO = "AMARILLO" 
    ROJO = "ROJO"          

class FirmasBase(BaseModel):
    banda: bool = False
    tesoreria: bool = False
    uniforme: bool = False
    salon: bool = False
    secretaria: bool = False
    rectoria: bool = False
    

class FirmasUpdate(BaseModel):
    banda: Optional[bool] = None
    tesoreria: Optional[bool] = None
    uniforme: Optional[bool] = None
    salon: Optional[bool] = None
    secretaria: Optional[bool] = None
    rectoria: Optional[bool] = None

class FirmasResponse(FirmasBase):
    id_firma: int
    id_estudiante: int
    id_periodo: int
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DetalleFirma(BaseModel):
    nombre: str
    firmado: bool
    rol_responsable: str
    no_aplica: bool = False

class EstadoPazSalvoResponse(BaseModel):
    id_estudiante: int
    nombre: str
    id_periodo: int
    periodo_nombre: Optional[str] = None
    firmas: FirmasBase
    todas_firmadas: bool
    puede_retirarse: bool
    semaforo: Optional [str] = None
    detalle_firmas: Optional[list[DetalleFirma]] = None
    firmas_completadas: Optional [int] = 0
    total_firmas: Optional [int] = 0

class RectoriaFirmaResponse(BaseModel):
    mensaje: str
    id_estudiante: int
    nombre_estudiante: str
    paz_y_salvo_completo: bool
    fecha_firma: datetime

class EstudiantePendienteResponse(BaseModel):
    id_estudiante: int
    nombre: str
    semaforo: str
    firmas_faltantes: list[str]
    firmas_completadas: int
    total_firmas: int

class RectoriaFirmaRequest(BaseModel):
    observacion: Optional[str] = None

class SelloHashResponse(BaseModel):
    hash_actual: str
    hash_registrado: Optional[str] = None
    integro: bool
    ultima_actualizacion: Optional[datetime] = None

class SelloRegistroResponse(BaseModel):
    mensaje: str
    hash_sha256: str