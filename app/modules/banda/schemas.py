from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# ============ CATEGORÍAS ============
class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None

class CategoriaResponse(CategoriaBase):
    id_categoria: int
    
    class Config:
        from_attributes = True

# ============ UBICACIONES ============
class UbicacionBase(BaseModel):
    nombre: str

class UbicacionCreate(UbicacionBase):
    pass

class UbicacionUpdate(BaseModel):
    nombre: Optional[str] = None

class UbicacionResponse(UbicacionBase):
    id_ubicacion: int
    
    class Config:
        from_attributes = True

# ============ INSTRUMENTOS ============
class InstrumentoBase(BaseModel):
    codigo:int
    nombre: str
    id_categoria: Optional[int] = None
    id_ubicacion: Optional[int] = None
    cantidad_total:int = Field(ge=1)
    estado:str = "activo"
    
class InstrumentoCreate(InstrumentoBase):
    pass

class InstrumentoUpdate(BaseModel):
    nombre: Optional[str] = None
    id_categoria: Optional[int] = None
    id_ubicacion: Optional[int] = None
    cantidad_total: Optional[int] = Field(None, ge=1)
    estado: Optional[str] = None

class InstrumentoResponse(InstrumentoBase):
    id_instrumento: int
    cantidad_disponible: int
    categoria_nombre: Optional[str] = None
    ubicacion_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True

# ============ DEVOLUCIONES DE INSTRUMENTOS ============
class DevolucionCreate(BaseModel):
    estado_al_devolver: str # "Bueno" o "Malo"
    observaciones: Optional[str] = None

# ============ PRÉSTAMOS DE INSTRUMENTOS ============
class PrestamoInstrumentoBase(BaseModel):
    id_instrumento: int
    id_estudiante: int
    observacion: Optional[str] = None

class PrestamoInstrumentoCreate(PrestamoInstrumentoBase):
    pass

class PrestamoInstrumentoUpdate(BaseModel):
    fecha_devolucion: Optional[date] = None
    estado_entrega: Optional[str] = None
    observacion: Optional[str] = None

class PrestamoInstrumentoResponse(PrestamoInstrumentoBase):
    id_prestamo: int
    id_instrumento: int
    id_estudiante: int
    fecha_prestamo: date
    fecha_devolucion: Optional[date] = None
    estado_entrega: str
    estado_al_devolver: Optional[str] = None
    observacion: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    instrumento_nombre: Optional[str] = None
    estudiante_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True

# ============ REPORTES ============
class InstrumentoDisponibleResponse(BaseModel):
    id_instrumento: int
    codigo: int
    nombre: str
    cantidad_disponible: int
    categoria: Optional[str] = None
    ubicacion: Optional[str] = None

class PrestamoActivoResponse(BaseModel):
    id_prestamo: int
    instrumento: str
    estudiante: str
    fecha_prestamo: datetime
    dias_prestado: int