from pydantic import BaseModel, Field, field_validator
import re

class AnioEscolarCreate(BaseModel):
    nombre: str = Field(..., example="2025-2026")
    activo: bool = Field(False, description="¿Debe ser el año activo?")

    @field_validator('nombre')
    @classmethod
    def validar_formato(cls, v):
        # Valida que sea 4 dígitos, un guion y otros 4 dígitos
        if not re.match(r"^\d{4}-\d{4}$", v):
            raise ValueError("El formato debe ser YYYY-YYYY (ej. 2025-2026)")
        return v

class AnioEscolarRead(AnioEscolarCreate):
    id_periodo: int
    anio: int

    class Config:
        from_attributes = True