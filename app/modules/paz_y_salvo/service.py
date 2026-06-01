from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from app.shared.models import PeriodoAcademico, Auditoria
from app.modules.estudiantes.models import Estudiante, EstudianteBanda
from app.modules.paz_y_salvo.models import FirmasPazYSalvo, TipoFirma, DetalleFirmaPazYSalvo
from app.modules.uniformes.models import PrestamoObjeto
from app.modules.paz_y_salvo.schemas import SemaforoEstado, DetalleFirma, EstudiantePendienteResponse
from app.modules.salon.models import Salon, Prueba, Pupitre, PrestamoLibro
from app.modules.banda.models import PrestamoInstrumento
from app.modules.tesoreria.models import Matricula, DetalleMatricula
from datetime import datetime
import hashlib, os

SELLO_PATH = "app/modules/paz_y_salvo/sellos/sello.svg"
SELLO_HASH_PATH = "app/modules/paz_y_salvo/sellos/sello.svg.hash"

CAMPOS_FIRMAS = ["banda", "tesoreria", "uniforme", "salon", "secretaria", "rectoria"]

CAMPO_TIPO_MAP = {
    "banda": "Banda",
    "tesoreria": "Tesorería",
    "uniforme": "Uniforme",
    "salon": "Salón",
    "secretaria": "Secretaría",
    "rectoria": "Rectoría",
    
}

DETALLE_FIRMAS_CONFIG = [
    {"campo": "banda",      "nombre": "Banda",      "rol": "banda"},
    {"campo": "tesoreria",  "nombre": "Tesorería",  "rol": "tesoreria"},
    {"campo": "uniforme",   "nombre": "Uniforme",   "rol": "uniformes"},
    {"campo": "salon",      "nombre": "Salón",      "rol": "titular"},
    {"campo": "secretaria", "nombre": "Secretaría", "rol": "secretaria"},
    {"campo": "rectoria",   "nombre": "Rectoría",   "rol": "rectoria"},
]
 

def _get_periodo_activo(db: Session) -> Optional[PeriodoAcademico]:
    return db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()

def _get_detalle(firma, tipo_nombre):
    for d in firma.detalles:
        if d.tipo_firma.nombre == tipo_nombre:
            return d
    return None

def _get_valor_campo(firma, campo):
    tipo_nombre = CAMPO_TIPO_MAP.get(campo)
    if not tipo_nombre:
        return False
    d = _get_detalle(firma, tipo_nombre)
    return d.estado if d else False

def _hash_sello() -> str:
    if os.path.exists(SELLO_PATH):
        with open(SELLO_PATH, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    return ""

def _hash_guardado() -> str:
    if os.path.exists(SELLO_HASH_PATH):
        with open(SELLO_HASH_PATH, "r", encoding="utf-8-sig") as f:
            contenido = f.read().strip()
            return "".join(c for c in contenido if c in "0123456789abcdef")
    return ""

def verificar_sello() -> dict:
    actual = _hash_sello()
    guardado = _hash_guardado()
    return {
        "hash_actual": actual,
        "hash_guardado": guardado if guardado else None,
        "integro": actual == guardado if guardado else False,
        "archivo": "sello.svg",
    }

def _get_no_aplica(db: Session, estudiante_id: int) -> set:
    no_aplica = set()

    en_banda = db.query(EstudianteBanda).filter(
        EstudianteBanda.id_estudiante == estudiante_id,
        EstudianteBanda.activo == True
    ).first()
    if not en_banda:
        no_aplica.add("banda")
    
    return no_aplica

def _calcular_semaforo(firmas_dict: dict, no_aplica: set) -> str:
    campos_que_aplican = [c for c in CAMPOS_FIRMAS if c not in no_aplica]
    if not campos_que_aplican:
        return SemaforoEstado.VERDE
    valores = [firmas_dict[c] for c in campos_que_aplican]
    total_true = sum(v for v in valores if v)
    if total_true == len(campos_que_aplican):
        return SemaforoEstado.VERDE
    elif total_true > 0:
        return SemaforoEstado.AMARILLO
    else:
        return SemaforoEstado.ROJO

def _construir_detalle_firmas(firmas_dict: dict, no_aplica: set) -> list:
    return [
        DetalleFirma(
            nombre=config["nombre"],
            firmado= config["campo"] in no_aplica or firmas_dict.get(config["campo"], False),
            rol_responsable=config["rol"],
            no_aplica=config["campo"] in no_aplica,
        )
        for config in DETALLE_FIRMAS_CONFIG
    ]

def _registrar_auditoria(db: Session, usuario: str, accion: str, tabla: str, id_registro: int) -> None:
    entrada = Auditoria(
        tabla=tabla,
        id_registro=id_registro,
        accion=accion,
        usuario=usuario,
        fecha=datetime.utcnow(),
    )
    db.add(entrada)



def get_firmas(db: Session, estudiante_id: int, periodo_id: Optional[int] = None) -> Optional[FirmasPazYSalvo]:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return None
        periodo_id = periodo.id_periodo
    
    firmas = db.query(FirmasPazYSalvo).options(
        joinedload(FirmasPazYSalvo.detalles).joinedload(DetalleFirmaPazYSalvo.tipo_firma)
    ).filter(
        FirmasPazYSalvo.id_estudiante == estudiante_id,
        FirmasPazYSalvo.id_periodo == periodo_id
    ).first()
    
    if firmas and not firmas.detalles:
        tipos = db.query(TipoFirma).all()
        for t in tipos:
            db.add(DetalleFirmaPazYSalvo(id_firma=firmas.id_firma, id_tipo_firma=t.id_tipo_firma, estado=False))
        db.commit()
        firmas = db.query(FirmasPazYSalvo).options(
            joinedload(FirmasPazYSalvo.detalles).joinedload(DetalleFirmaPazYSalvo.tipo_firma)
        ).filter(FirmasPazYSalvo.id_firma == firmas.id_firma).first()

    if not firmas:
        firmas = FirmasPazYSalvo(
            id_estudiante=estudiante_id,
            id_periodo=periodo_id
        )
        db.add(firmas)
        db.flush()
        tipos = db.query(TipoFirma).all()
        for t in tipos:
            db.add(DetalleFirmaPazYSalvo(id_firma=firmas.id_firma, id_tipo_firma=t.id_tipo_firma, estado=False))
        db.commit()
        db.refresh(firmas)
    
    return firmas

def get_estado_completo(db: Session, estudiante_id: int, periodo_id: Optional[int] = None) -> Optional[dict]:
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()
    if not estudiante:
        return None
    
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return None
        periodo_id = periodo.id_periodo
        periodo_nombre = periodo.nombre
    else:
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.id_periodo == periodo_id).first()
        periodo_nombre = periodo.nombre if periodo else None
    
    firmas = get_firmas(db, estudiante_id, periodo_id)
    no_aplica = _get_no_aplica(db, estudiante_id)
    
    firmas_dict = {
        c: _get_valor_auto(firmas, c, db, estudiante_id, periodo_id) for c in CAMPOS_FIRMAS
    }
    
    campos_que_aplican = [c for c in CAMPOS_FIRMAS if c not in no_aplica]
    completadas = sum(1 for c in campos_que_aplican if firmas_dict[c])
    todas_firmadas = completadas == len(campos_que_aplican)

    
    return {
        "id_estudiante": estudiante_id,
        "nombre": estudiante.nombre,
        "id_periodo": periodo_id,
        "periodo_nombre": periodo_nombre,
        "firmas": firmas_dict,
        "todas_firmadas": todas_firmadas,
        "puede_retirarse": todas_firmadas,
        "semaforo":          _calcular_semaforo(firmas_dict, no_aplica),
        "detalle_firmas":    _construir_detalle_firmas(firmas_dict, no_aplica),
        "firmas_completadas": completadas,
        "total_firmas":      len([c for c in CAMPOS_FIRMAS if c not in no_aplica]),
    }

def update_firmas(db: Session, estudiante_id: int, periodo_id: Optional[int], data: dict, usuario_id: int = None) -> Optional[FirmasPazYSalvo]:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return None
        periodo_id = periodo.id_periodo
    
    firmas = get_firmas(db, estudiante_id, periodo_id)
    no_aplica = _get_no_aplica(db, estudiante_id)

    for key, value in data.items():
        if key in no_aplica:
            if value == True:
                raise ValueError(f"No se puede firmar '{key}' porque no aplica para este estudiante")
            continue
        if value is not None:
            d = _get_detalle(firmas, CAMPO_TIPO_MAP.get(key))
            if d:
                d.estado = value
                if usuario_id:
                    d.id_usuario_firmante = usuario_id
    
    db.commit()
    db.refresh(firmas)
    return firmas



def firmar_rectoria(db: Session, estudiante_id: int, usuario_nombre: str, periodo_id: Optional[int] = None, usuario_id: int = None) -> dict:
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()
    if not estudiante:
        return {"error": "Estudiante no encontrado", "codigo": 404}

    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return {"error": "No hay periodo académico activo", "codigo": 400}
        periodo_id = periodo.id_periodo

    firmas = get_firmas(db, estudiante_id, periodo_id)
    no_aplica = _get_no_aplica(db, estudiante_id)

    firmas_previas = ["banda", "tesoreria", "uniforme", "salon", "secretaria"]
    nombres_display = {
        "banda": "Banda",
        "tesoreria":  "Tesorería",
        "uniforme":   "Uniforme",
        "salon":      "Salón",
        "secretaria": "Secretaría",
    }
    faltantes = [c for c in firmas_previas if not _get_valor_auto(firmas, c, db, estudiante_id, periodo_id) and c not in no_aplica]

    if faltantes:
        return {
            "error": f"No se puede firmar. Hay módulos pendientes: {', '.join(nombres_display[f] for f in faltantes)}",
            "codigo": 400,
        }

    d_rect = _get_detalle(firmas, "Rectoría")
    if not d_rect:
        return {"error": "Error interno", "codigo": 500}
    if d_rect.estado:
        return {"error": "Este estudiante ya tiene la firma de Rectoría.", "codigo": 400}
    d_rect.estado = True
    if usuario_id:
        d_rect.id_usuario_firmante = usuario_id

    _registrar_auditoria(
        db=db,
        usuario=usuario_nombre,
        accion="FIRMA_RECTORIA",
        tabla="firmas_paz_y_salvo",
        id_registro=firmas.id_firma,
    )

    db.commit()
    db.refresh(firmas)

    return {
        "mensaje": f"Paz y salvo de {estudiante.nombre} firmado correctamente por Rectoría.",
        "id_estudiante": estudiante_id,
        "nombre_estudiante": estudiante.nombre,
        "paz_y_salvo_completo": True,
        "fecha_firma": datetime.utcnow(),
    }

def get_pendientes(db: Session, periodo_id: Optional[int] = None) -> List[dict]:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return []
        periodo_id = periodo.id_periodo

    estudiantes = db.query(Estudiante).all()
    resultado = []

    for estudiante in estudiantes:
        firmas = get_firmas(db, estudiante.id_estudiante, periodo_id)
        no_aplica = _get_no_aplica(db, estudiante.id_estudiante)
        firmas_dict = {c: _get_valor_auto(firmas, c, db, estudiante.id_estudiante, periodo_id) for c in CAMPOS_FIRMAS}
        faltantes = [c for c in CAMPOS_FIRMAS if not _get_valor_auto(firmas, c, db, estudiante.id_estudiante, periodo_id) and c not in no_aplica]

        if faltantes:
            campos_aplican = [c for c in CAMPOS_FIRMAS if c not in no_aplica]
            completadas = len(campos_aplican) - len(faltantes)
            resultado.append(EstudiantePendienteResponse(
                id_estudiante=estudiante.id_estudiante,
                nombre=estudiante.nombre,
                semaforo=_calcular_semaforo(firmas_dict, no_aplica),
                firmas_faltantes=faltantes,
                firmas_completadas=completadas,
                total_firmas=len(campos_aplican),
            ))

    return resultado

def obtener_sello() -> dict:
    if not os.path.exists(SELLO_PATH):
        return {"error": "Sello no encontrado"}
    return {"ruta": SELLO_PATH, "hash": _hash_sello()}

def get_titular_pendientes(db: Session, usuario_id: int, periodo_id: Optional[int] = None) -> dict:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return {"error": "No hay periodo activo", "codigo": 400}
        periodo_id = periodo.id_periodo
    
    salon = db.query(Salon).filter(
        Salon.id_usuario == usuario_id,
        Salon.id_periodo == periodo_id
    ).first()
    if not salon:
        return {"error": "No tienes un salón asignado", "codigo": 404}
    
    estudiantes_data = []
    for estudiante in salon.estudiantes:
        firmas = get_firmas(db, estudiante.id_estudiante, periodo_id)
        no_aplica = _get_no_aplica(db, estudiante.id_estudiante)
        firmas_dict = {c: _get_valor_auto(firmas, c, db, estudiante.id_estudiante, periodo_id) for c in CAMPOS_FIRMAS}
        salon_firmado = _get_valor_auto(firmas, "salon", db, estudiante.id_estudiante, periodo_id)

        faltantes = [c for c in CAMPOS_FIRMAS if not _get_valor_auto(firmas, c, db, estudiante.id_estudiante, periodo_id) and c not in no_aplica]
        campos_aplican = [c for c in CAMPOS_FIRMAS if c not in no_aplica]
        estudiantes_data.append({
            "id_estudiante": estudiante.id_estudiante,
            "nombre": estudiante.nombre,
            "semaforo": _calcular_semaforo(firmas_dict, no_aplica),
            "salon_firmado": salon_firmado,
            "firmas_completadas": len(campos_aplican) - len(faltantes),
            "total_firmas": len(campos_aplican),
            "firmas_faltantes": faltantes,
        })
    
    return {
        "id_salon": salon.id_salon,
        "grado": salon.grado,
        "grupo": salon.grupo,
        "total_estudiantes": len(estudiantes_data),
        "pendientes_salon": sum(1 for e in estudiantes_data if not e["salon_firmado"]),
        "estudiantes": estudiantes_data,
    }

def _auto_banda(db: Session, estudiante_id: int) -> Optional[bool]:
    asociado = db.query(EstudianteBanda).filter(
        EstudianteBanda.id_estudiante == estudiante_id,
        EstudianteBanda.activo == True
    ).first()
    if not asociado:
        return None 
    
    pendiente = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_estudiante == estudiante_id,
        PrestamoInstrumento.estado_entrega == "Pendiente"
    ).first()
    return pendiente is None

def _auto_uniforme(db: Session, estudiante_id: int) -> bool:
    pendiente = db.query(PrestamoObjeto).filter(
        PrestamoObjeto.id_estudiante == estudiante_id,
        PrestamoObjeto.estado_entrega == "Pendiente"
    ).first()
    return pendiente is None

def _auto_tesoreria(db: Session, estudiante_id: int, periodo_id: int) -> bool:
    matricula = db.query(Matricula).filter(
        Matricula.id_estudiante == estudiante_id,
        Matricula.id_periodo == periodo_id
    ).first()
    if not matricula:
        return True 
    
    pendiente = db.query(DetalleMatricula).filter(
        DetalleMatricula.id_matricula == matricula.id_matricula,
        DetalleMatricula.estado == "Pendiente"
    ).first()
    return pendiente is None

def _auto_salon(db: Session, estudiante_id: int) -> bool:
    if db.query(Prueba).filter(
        Prueba.id_estudiante == estudiante_id,
        Prueba.estado == "Pendiente"
    ).first():
        return False
    if db.query(Pupitre).filter(
        Pupitre.id_estudiante == estudiante_id,
        Pupitre.estado == "Pendiente"
    ).first():
        return False
    if db.query(PrestamoLibro).filter(
        PrestamoLibro.id_estudiante == estudiante_id,
        PrestamoLibro.estado == "Pendiente"
    ).first():
        return False
    return True

def _get_valor_auto(firma: FirmasPazYSalvo, campo: str, db: Session, estudiante_id: int, periodo_id: int) -> bool:
    if _get_valor_campo(firma, campo):
        return True
    if campo == "banda":
        auto = _auto_banda(db, estudiante_id)
        return auto if auto is not None else False
    elif campo == "uniforme":
        return _auto_uniforme(db, estudiante_id)
    elif campo == "tesoreria":
        return _auto_tesoreria(db, estudiante_id, periodo_id)
    elif campo == "salon":
        return _auto_salon(db, estudiante_id)
    return False