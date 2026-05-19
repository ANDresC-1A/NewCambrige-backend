# app/modules/parametrizacion/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AnioEscolarCreate(BaseModel):
    anio_inicio: int = Field(..., gt=2000, lt=2100, example=2025)
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool = Field(True, description="Estado del año escolar")

class AnioEscolarUpdate(BaseModel):
    # Todos los campos son opcionales para permitir actualizaciones parciales
    activo: Optional[bool] = Field(None, description="Nuevo estado de activación")
    fecha_inicio: Optional[datetime] = Field(None, description="Nueva fecha de inicio")
    fecha_fin: Optional[datetime] = Field(None, description="Nueva fecha de fin")

class AnioEscolarRead(BaseModel):
    id_periodo: int
    nombre: str
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool

    class Config:
        from_attributes = True