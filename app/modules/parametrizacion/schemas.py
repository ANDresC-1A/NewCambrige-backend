from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator
import re

class AnioEscolarCreate(BaseModel):
    # El usuario solo envía el número inicial (ej: 2025)
    anio_inicio: int = Field(..., gt=2000, lt=2100, example=2025)
    activo: bool = Field(False)

class AnioEscolarUpdate(BaseModel):
    activo: bool = Field(..., description="Nuevo estado de activación del año")

class AnioEscolarRead(BaseModel):
    id_periodo: int
    nombre: str # Seguiremos mostrando "2025-2026" al usuario
    anio: int
    activo: bool

    class Config:
        from_attributes = True
