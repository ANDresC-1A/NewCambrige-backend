from pydantic import BaseModel

class PeriodoAcademicoBase(BaseModel):
    nombre: str
    anio: int

class PeriodoAcademicoResponse(PeriodoAcademicoBase):
    id_periodo: int
    activo: bool
    
    class Config:
        from_attributes = True