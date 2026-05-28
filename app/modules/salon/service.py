from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date
from app.modules.salon.models import (
    Salon, Prueba, TipoPrueba, Pupitre, InventarioLibro, PrestamoLibro
)
from app.modules.estudiantes.models import Estudiante

# ======================
# 🏫 SALONES
# ======================
def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Salon]:
    return db.query(Salon).offset(skip).limit(limit).all()

def get_salon_all_by_periodo(db: Session, id_periodo: int, skip: int = 0, limit: int = 100) -> List[Salon]:
    return db.query(Salon).filter(Salon.id_periodo == id_periodo).offset(skip).limit(limit).all()


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
def get_all_pruebas(db: Session) -> list:
    pruebas = (
        db.query(Prueba)
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
            "id": p.id_prueba,
            "id_prueba": p.id_prueba,
            "codigo": e.documento if e else None,
            "nombre": e.nombre if e else None,
            "grado": str(salon.grado) if salon else None,
            "grupo": str(salon.grupo) if salon else None,
            "tipo_prueba": (
                p.tipo_prueba.nombre
                if p.tipo_prueba else None
            ),
            "estado": p.estado,

            # SOLO mostrar fecha si está pagado
            "fecha_pago": (
                p.fecha_pago.strftime("%d/%m/%Y")
                if p.estado == "visto" and p.fecha_pago
                else None
            ),
        })

    return resultado


def create_prueba(db: Session, data: dict) -> Prueba:
    nueva = Prueba(**data)

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return nueva


def update_estado_prueba(
    db: Session,
    prueba_id: int,
    estado: str
) -> Optional[Prueba]:

    prueba = db.query(Prueba).filter(
        Prueba.id_prueba == prueba_id
    ).first()

    if not prueba:
        return None

    prueba.estado = estado

    # FECHA AUTOMÁTICA
    if estado == "visto":
        prueba.fecha_pago = date.today()

    db.commit()
    db.refresh(prueba)

    return prueba

# ======================
# 🪑 PUPITRES
# ======================
def get_all_pupitres(db: Session) -> list:
    pupitres = (
        db.query(Pupitre)
        .options(
            joinedload(Pupitre.estudiante).joinedload(Estudiante.salon),
        )
        .all()
    )

    resultado = []

    for p in pupitres:
        e = p.estudiante
        salon = e.salon if e else None

        resultado.append({
            "id_mantenimiento": p.id_mantenimiento,
            "id_estudiante": p.id_estudiante,
            "codigo": e.documento if e else None,
            "nombre": e.nombre if e else None,
            "grado": str(salon.grado) if salon else None,
            "grupo": str(salon.grupo) if salon else None,
            "estado": p.estado,
            "fecha_pago": (
                p.fecha_pago.strftime("%d/%m/%Y")
                if p.estado == "visto" and p.fecha_pago  #  Cambio: "visto" en lugar de "PAGADO"
                else None
            ),
        })

    return resultado


def update_pupitre(db: Session, pupitre_id: int, estado: str, fecha_pago: Optional[date] = None) -> Optional[Pupitre]:
    pupitre = db.query(Pupitre).filter(
        Pupitre.id_mantenimiento == pupitre_id
    ).first()

    if not pupitre:
        return None

    pupitre.estado = estado
    
    if fecha_pago:  # Ahora recibe el parámetro
        pupitre.fecha_pago = fecha_pago

    db.commit()
    db.refresh(pupitre)
    return pupitre


# ======================
# 📚 BIBLIOTECA
# ======================
def get_all_libros(db: Session):
    libros = db.query(InventarioLibro).all()

    return [
        {
            "id_libro": l.id_libro,
            "nombre": l.nombre,
            "autor": l.autor,
            "id_salon": l.id_salon,
            "disponible": l.disponible,
            "edicion": l.edicion,
            "estado_fisico": l.estado_fisico,
        }
        for l in libros
    ]


def get_all_prestamos(db: Session) -> list:
    prestamos = (
        db.query(PrestamoLibro)
        .options(
            joinedload(PrestamoLibro.estudiante).joinedload(Estudiante.salon),
            joinedload(PrestamoLibro.libro)
        )
        .all()
    )

    resultado = []

    for p in prestamos:
        e = p.estudiante
        salon = e.salon if e else None

        resultado.append({
            "codigo": e.documento if e else None,
            "nombre": e.nombre if e else None,
            "grado": str(salon.grado) if salon else None,
            "grupo": str(salon.grupo) if salon else None,
            "libro": p.libro.nombre if p.libro else None,
            "fecha_prestamo": str(p.fecha_prestamo) if p.fecha_prestamo else None,
            "fecha_devolucion": str(p.fecha_devolucion) if p.fecha_devolucion else None,
            "estado": p.estado,
        })

    return resultado


def create_libro(db: Session, data: dict) -> InventarioLibro:
    libro = InventarioLibro(**data)
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return libro


def update_libro(db: Session, libro_id: int, data: dict) -> Optional[InventarioLibro]:
    libro = db.query(InventarioLibro).filter(
        InventarioLibro.id_libro == libro_id
    ).first()

    if not libro:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(libro, key, value)

    db.commit()
    db.refresh(libro)
    return libro


def delete_libro(db: Session, libro_id: int) -> bool:
    # 1. Buscar el libro en el inventario por su ID
    libro = db.query(InventarioLibro).filter(
        InventarioLibro.id_libro == libro_id
    ).first()

    if not libro:
        return False

    # 2. Guardar el nombre exacto del libro
    nombre_libro_original = libro.nombre

    try:
        # 3. Filtrado directo en la DB usando igualdad estándar (sin .ilike ni .all() masivo)
        # Esto evita procesar registros corruptos de otros libros
        prestamos_asociados = db.query(PrestamoLibro).filter(
            PrestamoLibro.libro == nombre_libro_original
        ).all()

        # 4. Actualizar el log de auditoría para este libro
        for prestamo in prestamos_asociados:
            prestamo.observacion = "Libro eliminado del inventario"
            prestamo.estado = True  # Cerrar préstamo en el historial

    except Exception as current_error:
        # Si la tabla de préstamos tiene un problema estructural, imprimimos el error real en la consola de Python
        print(f"--- ERROR CRÍTICO EN AUDITORÍA DE PRÉSTAMOS: {str(current_error)} ---")
        # No detenemos el flujo para que al menos el borrado lógico del libro se ejecute
        pass

    # 5. Aplicar Borrado Lógico en el libro
    libro.disponible = False
    
    if "Eliminado del Inventario" not in libro.nombre:
        libro.nombre = f"{libro.nombre} (Eliminado del Inventario)"

    # 6. Confirmar cambios de forma limpia
    db.commit()
    return True

def create_prestamo(db: Session, data: dict) -> PrestamoLibro:
    # 1. Crear el registro del préstamo
    prestamo = PrestamoLibro(**data)
    db.add(prestamo)
    
    # 2. LÓGICA AUTOMÁTICA: Buscar el libro por su nombre (o ID si lo cambias luego) y pasarlo a NO disponible
    libro = db.query(InventarioLibro).filter(
        # Usamos ilike para evitar problemas de mayúsculas/minúsculas con el string enviado por el front
        InventarioLibro.nombre.ilike(data.get("libro")) 
    ).first()
    
    if libro:
        libro.disponible = False
        # Si del front mandas un estado físico al asignar, lo actualizamos aquí
        if "estado_fisico" in data: 
            libro.estado_fisico = data.get("estado_fisico")

    db.commit()
    db.refresh(prestamo)
    return prestamo


def registrar_devolucion(db: Session, prestamo_id: int, data: dict) -> Optional[PrestamoLibro]:
    """
    Función que te faltaba para procesar la devolución en el backend.
    """
    # 1. Buscar el préstamo activo
    prestamo = db.query(PrestamoLibro).filter(PrestamoLibro.id_prestamo == prestamo_id).first()
    if not prestamo:
        return None
        
    # 2. Actualizar el estado del préstamo a Devuelto (True) y meter observaciones
    prestamo.estado = True 
    if "observacion" in data:
        prestamo.observacion = data.get("observacion")
    if "fecha_devolucion" in data:
        prestamo.fecha_devolucion = data.get("fecha_devolucion")

    # 3. LÓGICA AUTOMÁTICA: Volver a poner el libro como Disponible
    libro = db.query(InventarioLibro).filter(InventarioLibro.nombre.ilike(prestamo.libro)).first()
    if libro:
        libro.disponible = True
        if "estado_de_devolucion" in data:
            libro.estado_fisico = data.get("estado_de_devolucion")

    db.commit()
    db.refresh(prestamo)
    return prestamo