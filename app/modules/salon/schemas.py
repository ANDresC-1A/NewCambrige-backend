from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

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
    grado: Optional[str] = None
    grupo: Optional[str] = None
    tipo_prueba: Optional[str] = None
    estado: Optional[str] = None
    fecha_pago: Optional[date] = None   # NUEVO
    
    class Config:
        from_attributes = True

class PruebaCreate(BaseModel):
    id_estudiante: int
    id_tipo_prueba: int
    estado: Optional[str] = "Pendiente"

# ======================
# 🪑 PUPITRES
# ======================
class PupitreResponse(BaseModel):
    id_mantenimiento: int
    id_estudiante: int
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    estado: Optional[str] = None
    class Config:
        from_attributes = True

class PupitreUpdate(BaseModel):
    pago: str

# ======================
# 📚 BIBLIOTECA
# ======================
class LibroResponse(BaseModel):
    id_libro: int
    nombre: str
    autor: str
    id_salon: Optional[int] = None
    disponible: bool
    edicion: Optional[str] = None
    estado_fisico: Optional[str] = None

    class Config:
        from_attributes = True

class LibroCreate(BaseModel):
    nombre: str
    autor: str
    id_salon: Optional[int] = None
    disponible: Optional[bool] = True

class LibroUpdate(BaseModel):
    nombre: Optional[str] = None
    autor: Optional[str] = None
    id_salon: Optional[int] = None
    disponible: Optional[bool] = None

class PrestamoResponse(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    grado: Optional[str] = None
    grupo: Optional[str] = None
    libro: Optional[str] = None
    fecha_prestamo: Optional[str] = None
    fecha_devolucion: Optional[str] = None
    estado: Optional[bool] = None

    class Config:
        from_attributes = True

class PrestamoCreate(BaseModel):
    id_libro: int
    id_estudiante: int
    fecha_prestamo: Optional[date] = None
    fecha_devolucion: Optional[date] = None
    estado: Optional[bool] = True