from datetime import datetime

from pydantic import BaseModel

class PeriodoAcademicoBase(BaseModel):
    nombre: str
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool = True

class PeriodoAcademicoResponse(PeriodoAcademicoBase):
    id_periodo: int
    nombre: str
    activo: bool
    
    class Config:
        from_attributes = True


    