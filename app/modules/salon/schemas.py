from pydantic import BaseModel
from typing import Optional

class SalonBase(BaseModel):
    grado: int
    grupo: int
    id_usuario: Optional[int] = None
    id_periodo: Optional[int] = None

class SalonCreate(SalonBase):
    pass

class SalonUpdate(BaseModel):
    grado: Optional[int] = None
    grupo: Optional[int] = None
    id_usuario: Optional[int] = None
    id_periodo: Optional[int] = None

class SalonResponse(SalonBase):
    id_salon: int
    
    class Config:
        from_attributes = True
        
# ======================
# 🧪 PRUEBAS
# ======================
class PruebaResponse(BaseModel):
    id_prueba: int
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    grado: Optional[int] = None
    grupo: Optional[str] = None
    tipo_prueba: Optional[str] = None
    estado: Optional[str] = None

    class Config:
        from_attributes = True

class PruebaCreate(BaseModel):
    id_estudiante: int
    id_tipo_prueba: int
    estado: Optional[str] = "Pendiente"