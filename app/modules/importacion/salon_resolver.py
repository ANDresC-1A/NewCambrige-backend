import unicodedata
from sqlalchemy.orm import Session
from app.modules.salon.models import Salon
from app.modules.importacion.models import StagingEstudiante
from app.shared.models import PeriodoAcademico

class SalonResolverError(Exception):
    pass

class SalonResolverService:

    _MAPEO_GRADOS = {
        "preescolar": 0,
        "primero": 1,
        "segundo": 2,
        "tercero": 3,
        "cuarto": 4,
        "quinto": 5,
        "sexto": 6,
        "septimo": 7,
        "octavo": 8,
        "noveno": 9,
        "decimo": 10,
        "once": 11,
        "parvulos": 12,
        "jardin": 13,
        "prejardin": 14,
        "transicion": 15
    }

    @staticmethod
    def _limpiar_texto(texto: str) -> str:
        if not texto:
            return ""
        # Convert to lowercase
        texto = texto.lower().strip()
        # Remove accents
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto

    @staticmethod
    def mapear_grado(grado_str: str) -> int:
        limpio = SalonResolverService._limpiar_texto(grado_str)
        if limpio in SalonResolverService._MAPEO_GRADOS:
            return SalonResolverService._MAPEO_GRADOS[limpio]
        raise SalonResolverError(f"Grado desconocido no se puede mapear: '{grado_str}'")

    @staticmethod
    def mapear_grupo(grupo_str: str) -> int:
        limpio = SalonResolverService._limpiar_texto(grupo_str).upper()
        if not limpio:
            raise SalonResolverError("Grupo vac\u00edo")
        
        # Simple letter to number mapping: A=1, B=2, C=3, etc.
        char = limpio[0]
        if 'A' <= char <= 'Z':
            return ord(char) - ord('A') + 1
        
        raise SalonResolverError(f"Grupo desconocido no se puede mapear: '{grupo_str}'")

    @staticmethod
    def obtener_periodo_activo(db: Session) -> PeriodoAcademico:
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
        if not periodo:
            raise SalonResolverError("No existe un periodo acad\u00e9mico activo")
        return periodo

    @staticmethod
    def resolver_o_crear_salon(db: Session, grado_int: int, grupo_int: int, id_periodo: int, cache: dict) -> int:
        key = (grado_int, grupo_int, id_periodo)
        
        # 1. Buscar en cach\u00e9 local (evita duplicidad concurrente/en el mismo lote)
        if key in cache:
            return cache[key]
        
        # 2. Buscar en base de datos
        salon = db.query(Salon).filter(
            Salon.grado == grado_int,
            Salon.grupo == grupo_int,
            Salon.id_periodo == id_periodo
        ).first()

        if salon:
            cache[key] = salon.id_salon
            return salon.id_salon

        # 3. Crear el sal\u00f3n si no existe
        nuevo_salon = Salon(
            grado=grado_int,
            grupo=grupo_int,
            id_periodo=id_periodo
            # id_usuario is nullable based on models.py
        )
        db.add(nuevo_salon)
        db.commit() # Important: commit to get the ID and avoid race conditions if used elsewhere
        db.refresh(nuevo_salon)
        
        cache[key] = nuevo_salon.id_salon
        return nuevo_salon.id_salon

    @staticmethod
    def procesar_staging_estudiantes(db: Session, ejecucion_id: int) -> dict:
        """
        Resuelve y asocia un id_salon a todos los registros de staging_estudiantes para la ejecuci\u00f3n dada.
        Retorna estad\u00edsticas.
        """
        try:
            periodo = SalonResolverService.obtener_periodo_activo(db)
        except SalonResolverError as e:
            return {"estado": "error", "mensaje": str(e)}

        estudiantes = db.query(StagingEstudiante).filter(
            StagingEstudiante.ejecucion_id == ejecucion_id,
            StagingEstudiante.id_salon == None
        ).all()

        if not estudiantes:
            return {"estado": "completado", "mensaje": "No hay estudiantes pendientes de resolver sal\u00f3n en esta ejecuci\u00f3n.", "procesados": 0}

        cache_salones = {}
        procesados = 0
        errores_mapeo = []

        for est in estudiantes:
            try:
                grado_int = SalonResolverService.mapear_grado(est.grado)
                grupo_int = SalonResolverService.mapear_grupo(est.curso) # WebColegios gives group in 'curso' field
                
                id_salon = SalonResolverService.resolver_o_crear_salon(
                    db, 
                    grado_int, 
                    grupo_int, 
                    periodo.id_periodo, 
                    cache_salones
                )
                
                est.id_salon = id_salon
                procesados += 1
            except SalonResolverError as e:
                errores_mapeo.append({"documento": est.documento, "grado": est.grado, "curso": est.curso, "error": str(e)})
        
        db.commit()
        
        return {
            "estado": "completado",
            "mensaje": f"Se resolvieron salones para {procesados} estudiantes.",
            "procesados": procesados,
            "salones_en_cache": len(cache_salones),
            "errores_mapeo": errores_mapeo
        }
