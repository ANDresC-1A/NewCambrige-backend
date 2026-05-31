from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime

from app.modules.banda.models import (
    Categoria, Ubicacion, InventarioInstrumento, PrestamoInstrumento, AuditoriaBanda
)
from app.modules.estudiantes.models import Estudiante

# ============ AUDITORÍA (HELPER) ============
def registrar_auditoria(db: Session, current_user, modulo: str, accion: str, entidad: str, v_ant: str, v_nue: str, resultado: str, desc: str):
    id_usr = getattr(current_user, 'id_usuario', getattr(current_user, 'id', 0))
    nom_usr = getattr(current_user, 'nombre', getattr(current_user, 'username', 'Sistema'))
    
    auditoria = AuditoriaBanda(
        id_usuario=id_usr,
        nombre_usuario=nom_usr,
        modulo_origen=modulo,
        tipo_accion=accion,
        entidad_afectada=entidad,
        valor_anterior=v_ant,
        valor_nuevo=v_nue,
        resultado=resultado,
        descripcion=desc
    )
    db.add(auditoria)
    
    
# ============ CATEGORÍAS ============
def get_categorias_all(db: Session, skip: int = 0, limit: int = 100) -> List[Categoria]:
    return db.query(Categoria).offset(skip).limit(limit).all()

def get_categoria_by_id(db: Session, categoria_id: int) -> Optional[Categoria]:
    return db.query(Categoria).filter(Categoria.id_categoria == categoria_id).first()

def get_categoria_by_nombre(db: Session, nombre: str) -> Optional[Categoria]:
    return db.query(Categoria).filter(Categoria.nombre == nombre).first()

def create_categoria(db: Session, data: dict) -> Categoria:
    nueva = Categoria(**data)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def update_categoria(db: Session, categoria_id: int, data: dict) -> Optional[Categoria]:
    categoria = get_categoria_by_id(db, categoria_id)
    if not categoria:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(categoria, key, value)
    db.commit()
    db.refresh(categoria)
    return categoria

def delete_categoria(db: Session, categoria_id: int) -> bool:
    categoria = get_categoria_by_id(db, categoria_id)
    if not categoria:
        return False
    db.delete(categoria)
    db.commit()
    return True

# ============ UBICACIONES ============
def get_ubicaciones_all(db: Session, skip: int = 0, limit: int = 100) -> List[Ubicacion]:
    return db.query(Ubicacion).offset(skip).limit(limit).all()

def get_ubicacion_by_id(db: Session, ubicacion_id: int) -> Optional[Ubicacion]:
    return db.query(Ubicacion).filter(Ubicacion.id_ubicacion == ubicacion_id).first()

def create_ubicacion(db: Session, data: dict) -> Ubicacion:
    nueva = Ubicacion(**data)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def update_ubicacion(db: Session, ubicacion_id: int, data: dict) -> Optional[Ubicacion]:
    ubicacion = get_ubicacion_by_id(db, ubicacion_id)
    if not ubicacion:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(ubicacion, key, value)
    db.commit()
    db.refresh(ubicacion)
    return ubicacion

def delete_ubicacion(db: Session, ubicacion_id: int) -> bool:
    ubicacion = get_ubicacion_by_id(db, ubicacion_id)
    if not ubicacion:
        return False
    db.delete(ubicacion)
    db.commit()
    return True

# ============ INSTRUMENTOS ============
def get_instrumentos_all(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    solo_disponibles: bool = False,
    categoria_id: Optional[int] = None
) -> List[InventarioInstrumento]:
    query = db.query(InventarioInstrumento).options(
        joinedload(InventarioInstrumento.categoria),
        joinedload(InventarioInstrumento.ubicacion)
    )
    
    if solo_disponibles:
        query = query.filter(InventarioInstrumento.cantidad_disponible > 0, InventarioInstrumento.estado == "Activo")
    
    if categoria_id:
        query = query.filter(InventarioInstrumento.id_categoria == categoria_id)
    
    return query.offset(skip).limit(limit).all()

def get_instrumento_by_id(db: Session, instrumento_id: int) -> Optional[InventarioInstrumento]:
    return db.query(InventarioInstrumento).options(
        joinedload(InventarioInstrumento.categoria),
        joinedload(InventarioInstrumento.ubicacion)
    ).filter(InventarioInstrumento.id_instrumento == instrumento_id).first()

def create_instrumento(db: Session, data: dict) -> InventarioInstrumento:
    nuevo = InventarioInstrumento(**data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def update_instrumento(db: Session, instrumento_id: int, data: dict, current_user) -> Optional[InventarioInstrumento]:
    instrumento = get_instrumento_by_id(db, instrumento_id)
    if not instrumento:
        return None
    
    valor_anterior = f"Total: {instrumento.cantidad_total}, Estado: {instrumento.estado}"
    
    if "cantidad_total" in data:
        diferencia = data["cantidad_total"] - instrumento.cantidad_total
        instrumento.cantidad_disponible += diferencia
        if instrumento.cantidad_disponible < 0:
            raise ValueError("La cantidad total no puede ser menor a los instrumentos actualmente prestados.")
            
    for key, value in data.items():
        if value is not None and key != "codigo":
            setattr(instrumento, key, value)
            
    valor_nuevo = f"Total: {instrumento.cantidad_total}, Estado: {instrumento.estado}"
    registrar_auditoria(db, current_user, "Inventario", "Instrumento editado", f"{instrumento.codigo} - {instrumento.nombre}", valor_anterior, valor_nuevo, "EXITOSO", "Se editó el instrumento.")
    
    db.commit()
    db.refresh(instrumento)
    return instrumento

def delete_instrumento(db: Session, instrumento_id: int, current_user) -> bool:
    instrumento = get_instrumento_by_id(db, instrumento_id)
    if not instrumento:
        return False
    
    if instrumento.cantidad_disponible < instrumento.cantidad_total:
        raise ValueError("No es posible eliminar este instrumento. Tiene asignaciones activas.")
    
    registrar_auditoria(db, current_user, "Inventario", "Instrumento eliminado", f"{instrumento.codigo} - {instrumento.nombre}", "Activo", "Eliminado", "EXITOSO", "Se eliminó el instrumento del sistema.")
    
    db.delete(instrumento)
    db.commit()
    return True

# ============ PRÉSTAMOS DE INSTRUMENTOS ============
def get_prestamos_all(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    solo_activos: bool = False,
    estudiante_id: Optional[int] = None
) -> List[PrestamoInstrumento]:
    query = db.query(PrestamoInstrumento).options(
        joinedload(PrestamoInstrumento.instrumento),
        joinedload(PrestamoInstrumento.estudiante)
    )
    
    if solo_activos:
        query = query.filter(PrestamoInstrumento.estado_entrega == "prestado")
    
    if estudiante_id:
        query = query.filter(PrestamoInstrumento.id_estudiante == estudiante_id)
    
    return query.order_by(PrestamoInstrumento.fecha_prestamo.desc()).offset(skip).limit(limit).all()

def get_prestamo_by_id(db: Session, prestamo_id: int) -> Optional[PrestamoInstrumento]:
    return db.query(PrestamoInstrumento).options(
        joinedload(PrestamoInstrumento.instrumento),
        joinedload(PrestamoInstrumento.estudiante)
    ).filter(PrestamoInstrumento.id_prestamo == prestamo_id).first()

def get_prestamos_activos_por_estudiante(db: Session, estudiante_id: int) -> List[PrestamoInstrumento]:
    return db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_estudiante == estudiante_id,
        PrestamoInstrumento.estado_entrega == "prestado"
    ).all()

def create_prestamo(db: Session, data: dict, current_user) -> Optional[PrestamoInstrumento]:
    instrumento = get_instrumento_by_id(db, data["id_instrumento"])
    if not instrumento:
        return None
    
    if instrumento.cantidad_disponible <= 0 or instrumento.estado != "Activo":
        raise ValueError("No hay instrumentos disponibles para asignar.")
    
    prestamo_activo = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_estudiante == data["id_estudiante"],
        PrestamoInstrumento.estado_entrega == "prestado"
    ).first()
    
    if prestamo_activo:
        raise ValueError("El estudiante ya tiene un instrumento asignado. Debe registrar la devolución antes de asignar uno nuevo.")
    
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == data["id_estudiante"]).first()
    if not estudiante:
        return None
    
    prestamo = PrestamoInstrumento(
        id_instrumento=data["id_instrumento"],
        id_estudiante=data["id_estudiante"],
        fecha_prestamo=datetime.today(),
        observacion=data.get("observacion"),
        estado_entrega="prestado"
    )
    
    instrumento.cantidad_disponible -= 1
    
    db.add(prestamo)
    registrar_auditoria(db, current_user, "Asignaciones", "Asignación creada", f"Inst: {instrumento.codigo}, Est: {estudiante.nombre}", "—", "Prestado", "EXITOSO", "Se asignó un instrumento al estudiante.")
    
    db.commit()
    db.refresh(prestamo)
    return prestamo

def devolver_instrumento(db: Session, prestamo_id: int, data: dict, current_user) -> Optional[PrestamoInstrumento]:
    prestamo = get_prestamo_by_id(db, prestamo_id)
    if not prestamo:
        return None
    
    if prestamo.estado_entrega != "prestado":
        raise ValueError("El instrumento ya fue devuelto")
        
    estado_devolucion = data.get("estado_al_devolver")
    observaciones = data.get("observaciones")
    
    if estado_devolucion == "Malo" and not observaciones:
        raise ValueError("Debe describir el daño del instrumento en las observaciones.")
    
    prestamo.estado_entrega = "devuelto"
    prestamo.estado_al_devolver = estado_devolucion
    prestamo.observacion = observaciones if observaciones else prestamo.observacion
    prestamo.fecha_devolucion = datetime.today()
    instrumento = get_instrumento_by_id(db, prestamo.id_instrumento)
    if instrumento:
        if estado_devolucion == "Bueno":
            instrumento.cantidad_disponible += 1
        else:
            instrumento.estado = "En mantenimiento"
            
    registrar_auditoria(db, current_user, "Devoluciones", "Devolución registrada", f"Inst: {instrumento.codigo}, Est: {prestamo.estudiante.nombre}", "Prestado", f"Devuelto ({estado_devolucion})", "EXITOSO", "Se registró la devolución del instrumento.")
    
    db.commit()
    db.refresh(prestamo)
    return prestamo

def update_prestamo(db: Session, prestamo_id: int, data: dict) -> Optional[PrestamoInstrumento]:
    prestamo = get_prestamo_by_id(db, prestamo_id)
    if not prestamo:
        return None
    
    for key, value in data.items():
        if value is not None:
            setattr(prestamo, key, value)
    
    db.commit()
    db.refresh(prestamo)
    return prestamo

def get_historial_instrumento(db: Session, instrumento_id: int) -> List[PrestamoInstrumento]:
    return db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_instrumento == instrumento_id
    ).order_by(PrestamoInstrumento.fecha_prestamo.desc()).all()

def get_estadisticas(db: Session) -> dict:
    total_instrumentos = db.query(func.sum(InventarioInstrumento.cantidad_total)).scalar() or 0
    disponibles = db.query(func.sum(InventarioInstrumento.cantidad_disponible)).scalar() or 0
    prestamos_activos = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.estado_entrega == "prestado"
    ).count()
    
    return {
        "total_instrumentos": total_instrumentos,
        "instrumentos_disponibles": disponibles,
        "instrumentos_prestados": total_instrumentos - disponibles,
        "prestamos_activos": prestamos_activos
    }