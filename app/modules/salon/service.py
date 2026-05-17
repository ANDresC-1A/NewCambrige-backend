from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.modules.salon.models import Salon

def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Salon]:
    return db.query(Salon).offset(skip).limit(limit).all()

def get_by_id(db: Session, salon_id: int) -> Optional[Salon]:
    return db.query(Salon).filter(Salon.id_salon == salon_id).first()

def get_by_grado_grupo(db: Session, grado: int, grupo: int) -> List[Salon]:
    return db.query(Salon).filter(Salon.grado == grado, Salon.grupo == grupo).all()

def create(db: Session, data: dict) -> Salon:
    nuevo = Salon(**data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def update(db: Session, salon_id: int, data: dict) -> Optional[Salon]:
    salon = get_by_id(db, salon_id)
    if not salon:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(salon, key, value)
    db.commit()
    db.refresh(salon)
    return salon

def delete(db: Session, salon_id: int) -> bool:
    salon = get_by_id(db, salon_id)
    if not salon:
        return False
    db.delete(salon)
    db.commit()
    return True

# ======================
# 🧪 PRUEBAS
# ======================
from app.modules.salon.models import Prueba, TipoPrueba
from app.modules.estudiantes.models import Estudiante  # ajusta si la ruta es diferente

def get_all_pruebas(db: Session) -> list:
    pruebas = (
        db.query(Prueba)
        .join(Prueba.estudiante)
        .join(Prueba.tipo_prueba)
        .options(
            joinedload(Prueba.estudiante).joinedload(Estudiante.salon),
            joinedload(Prueba.tipo_prueba)
        )
        .all()
    )

    resultado = []
    for p in pruebas:
        e = p.estudiante
        salon = e.salon if e else None
        resultado.append({
            "id_prueba":   p.id_prueba,
            "codigo":      e.documento if e else None,
            "nombre":      e.nombre if e else None,
            "grado":       str(salon.grado) if salon else None,
            "grupo":       str(salon.grupo) if salon else None,
            "tipo_prueba": p.tipo_prueba.nombre if p.tipo_prueba else None,
            "estado":      p.estado,
        })
    return resultado

def create_prueba(db: Session, data: dict) -> Prueba:
    nueva = Prueba(**data)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def update_estado_prueba(db: Session, prueba_id: int, estado: str):
    prueba = db.query(Prueba).filter(Prueba.id_prueba == prueba_id).first()
    if not prueba:
        return None
    prueba.estado = estado
    db.commit()
    db.refresh(prueba)
    return prueba