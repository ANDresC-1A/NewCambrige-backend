import sys
import traceback
from sqlalchemy.orm import Session
from app.modules.importacion.repositories.staging_repository import StagingRepository
from app.modules.importacion.schemas import CargaMasivaRequest, CargaIndividualRequest
from app.modules.secretaria.models import CredencialesLogin
from playwright.sync_api import sync_playwright
from app.modules.importacion.scraper.driver_setup import crear_driver
from app.modules.importacion.scraper.autenticacion import autenticar
from app.modules.importacion.scraper.navegacion import navegar_y_generar_listado, navegar_pagina2_y_descargar_pdfs, navegar_y_descargar_docentes
from app.modules.importacion.scraper.extraccion import extraer_estudiantes, extraer_docentes, extraer_titulares_de_pdfs
from app.modules.importacion.salon_resolver import SalonResolverService

class ImportacionService:
    def __init__(self, db: Session):
        self.repo = StagingRepository(db)

    def ejecutar_carga_masiva(self, request: CargaMasivaRequest, usuario_id: int = None):
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="masiva", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        for idx, datos in enumerate(request.datos):
            try:
                if request.tipo == "estudiante":
                    self.repo.insertar_staging_estudiante(ejecucion.id, datos)
                    reg_est += 1
                elif request.tipo == "docente":
                    self.repo.insertar_staging_docente(ejecucion.id, datos)
                    reg_doc += 1
                else:
                    raise ValueError(f"Tipo desconocido: {request.tipo}")
            except Exception as e:
                errores += 1
                doc_ref = datos.get("documento") or f"Fila {idx}"
                self.repo.registrar_error(ejecucion.id, request.tipo, str(e), str(doc_ref))

        self.repo.finalizar_ejecucion(
            ejecucion_id=ejecucion.id,
            estado="completado" if errores == 0 else "completado_con_errores",
            reg_est=reg_est,
            reg_doc=reg_doc,
            errores=errores
        )

        if request.tipo == "estudiante" and reg_est > 0:
            SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)

        return {"ejecucion_id": ejecucion.id, "estado": "completado", "insertados": reg_est + reg_doc, "errores": errores}

    def ejecutar_carga_individual(self, request: CargaIndividualRequest, usuario_id: int = None):
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="individual", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            if request.tipo == "estudiante":
                self.repo.insertar_staging_estudiante(ejecucion.id, request.datos)
                reg_est += 1
            elif request.tipo == "docente":
                self.repo.insertar_staging_docente(ejecucion.id, request.datos)
                reg_doc += 1
            else:
                raise ValueError(f"Tipo desconocido: {request.tipo}")
        except Exception as e:
            errores += 1
            doc_ref = request.datos.get("documento") or "Registro individual"
            self.repo.registrar_error(ejecucion.id, request.tipo, str(e), str(doc_ref))

        self.repo.finalizar_ejecucion(
            ejecucion_id=ejecucion.id,
            estado="completado" if errores == 0 else "error",
            reg_est=reg_est,
            reg_doc=reg_doc,
            errores=errores
        )

        if request.tipo == "estudiante" and reg_est > 0:
            SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)

        return {"ejecucion_id": ejecucion.id, "estado": "completado" if errores == 0 else "error", "errores": errores}

    def _obtener_credenciales(self):
        credencial = self.repo.db.query(CredencialesLogin).first()
        if not credencial:
            credencial = CredencialesLogin(
                url="https://www.webcolegios.com/clararincon/",
                nombre_usuario="60267973",
                password_hash="0870"
            )
            self.repo.db.add(credencial)
            self.repo.db.commit()
            self.repo.db.refresh(credencial)
        return credencial

    def _procesar_estudiantes(self, ejecucion_id, context, page, url, usuario, password):
        reg_est = 0
        errores = 0
        
        print("INICIO autenticar (estudiantes)", flush=True)
        if not autenticar(page, url=url, usuario=usuario, password=password, tipo_usuario="Administrativo"):
            raise Exception("Fallo la autenticacion en WebColegios")
        print("FIN autenticar", flush=True)

        print("INICIO navegar_y_generar_listado", flush=True)
        page_estudiantes = navegar_y_generar_listado(context, page, tipo_datos="Estudiantes")
        print("FIN navegar_y_generar_listado", flush=True)
        if not page_estudiantes:
            raise Exception("No se pudo obtener el listado de estudiantes")
        
        print("INICIO extraer_estudiantes", flush=True)
        estudiantes_extraidos = extraer_estudiantes(page_estudiantes)
        print("FIN extraer_estudiantes", flush=True)
        
        print("INICIO insercion staging_estudiantes", flush=True)
        for est in estudiantes_extraidos:
            try:
                self.repo.insertar_staging_estudiante(ejecucion_id, est)
                reg_est += 1
            except Exception as e:
                errores += 1
                self.repo.registrar_error(ejecucion_id, "estudiante", f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}", est.get("documento", ""))
        print("FIN insercion staging_estudiantes", flush=True)

        page_estudiantes.close()
        return reg_est, errores

    def _procesar_docentes(self, ejecucion_id, context, page, url, usuario, password):
        reg_doc = 0
        errores = 0

        # Re-autenticar para la FASE B y evitar bloqueo de sesión (Acceso Denegado)
        print("INICIO re-autenticar para FASE B (Titulares)", flush=True)
        context.clear_cookies()
        if not autenticar(page, url=url, usuario=usuario, password=password, tipo_usuario="Administrativo"):
            raise Exception("Fallo la autenticacion en WebColegios para FASE B")
        print("FIN re-autenticar para FASE B", flush=True)
        
        print("INICIO navegar_pagina2_y_descargar_pdfs", flush=True)
        rutas_titulares = navegar_pagina2_y_descargar_pdfs(context, page)
        print("FIN navegar_pagina2_y_descargar_pdfs", flush=True)
        
        print("INICIO extraer_titulares_de_pdfs", flush=True)
        titulares = extraer_titulares_de_pdfs(rutas_titulares)
        print("FIN extraer_titulares_de_pdfs", flush=True)

        # Re-autenticar nuevamente antes de la fase de lista de docentes para evitar estado corrupto de sesión
        print("INICIO re-autenticar para DOCENTES LISTA", flush=True)
        context.clear_cookies()
        if not autenticar(page, url=url, usuario=usuario, password=password, tipo_usuario="Administrativo"):
            raise Exception("Fallo la re-autenticacion en WebColegios para docentes")
        print("FIN re-autenticar para DOCENTES LISTA", flush=True)

        print("INICIO navegar_y_descargar_docentes", flush=True)
        ruta_docentes = navegar_y_descargar_docentes(page)
        print("FIN navegar_y_descargar_docentes", flush=True)
        if not ruta_docentes:
            raise Exception("No se pudo descargar listado de docentes")

        print("INICIO extraer_docentes", flush=True)
        docentes_extraidos = extraer_docentes(page=None, titulares=titulares)
        print("FIN extraer_docentes", flush=True)
        
        print("INICIO insercion staging_docentes", flush=True)
        for doc in docentes_extraidos:
            try:
                self.repo.insertar_staging_docente(ejecucion_id, doc)
                reg_doc += 1
            except Exception as e:
                errores += 1
                self.repo.registrar_error(ejecucion_id, "docente", f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}", doc.get("documento", ""))
        print("FIN insercion staging_docentes", flush=True)

        return reg_doc, errores

    def iniciar_scraping_estudiantes(self, usuario_id: int = None):
        credencial = self._obtener_credenciales()
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="scraping_estudiantes", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            with sync_playwright() as p:
                browser, context, page = crear_driver(p)
                try:
                    r_est, err = self._procesar_estudiantes(ejecucion.id, context, page, credencial.url, credencial.nombre_usuario, credencial.password_hash)
                    reg_est += r_est
                    errores += err
                    if r_est > 0:
                        SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)
                except Exception as ex_inner:
                    print(f"EXCEPCION INTERNA CAPTURADA: {type(ex_inner).__name__} - {str(ex_inner)}\n{traceback.format_exc()}", flush=True)
                    raise ex_inner
                finally:
                    context.close()
                    browser.close()

            estado_final = "completado" if errores == 0 else "completado_con_errores"
        except Exception as ex:
            print(f"EXCEPCION EXTERNA CAPTURADA: {type(ex).__name__} - {str(ex)}\n{traceback.format_exc()}", flush=True)
            self.repo.registrar_error(ejecucion.id, "sistema", f"{type(ex).__name__}: {str(ex)}\n{traceback.format_exc()}")
            errores += 1
            estado_final = "error"

        self.repo.finalizar_ejecucion(ejecucion.id, estado_final, reg_est, reg_doc, errores)
        
        return {
            "ejecucion_id": ejecucion.id,
            "estado": estado_final,
            "registros_estudiantes": reg_est,
            "registros_docentes": reg_doc,
            "errores": errores
        }

    def iniciar_scraping_docentes(self, usuario_id: int = None):
        credencial = self._obtener_credenciales()
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="scraping_docentes", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            with sync_playwright() as p:
                browser, context, page = crear_driver(p)
                try:
                    r_doc, err = self._procesar_docentes(ejecucion.id, context, page, credencial.url, credencial.nombre_usuario, credencial.password_hash)
                    reg_doc += r_doc
                    errores += err
                except Exception as ex_inner:
                    print(f"EXCEPCION INTERNA CAPTURADA: {type(ex_inner).__name__} - {str(ex_inner)}\n{traceback.format_exc()}", flush=True)
                    raise ex_inner
                finally:
                    context.close()
                    browser.close()

            estado_final = "completado" if errores == 0 else "completado_con_errores"
        except Exception as ex:
            print(f"EXCEPCION EXTERNA CAPTURADA: {type(ex).__name__} - {str(ex)}\n{traceback.format_exc()}", flush=True)
            self.repo.registrar_error(ejecucion.id, "sistema", f"{type(ex).__name__}: {str(ex)}\n{traceback.format_exc()}")
            errores += 1
            estado_final = "error"

        self.repo.finalizar_ejecucion(ejecucion.id, estado_final, reg_est, reg_doc, errores)
        
        return {
            "ejecucion_id": ejecucion.id,
            "estado": estado_final,
            "registros_estudiantes": reg_est,
            "registros_docentes": reg_doc,
            "errores": errores
        }

    def iniciar_scraping(self, usuario_id: int = None):
        credencial = self._obtener_credenciales()
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="scraping", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            with sync_playwright() as p:
                browser, context, page = crear_driver(p)
                try:
                    # Estudiantes
                    r_est, err1 = self._procesar_estudiantes(ejecucion.id, context, page, credencial.url, credencial.nombre_usuario, credencial.password_hash)
                    reg_est += r_est
                    errores += err1
                    if r_est > 0:
                        SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)

                    # Docentes
                    r_doc, err2 = self._procesar_docentes(ejecucion.id, context, page, credencial.url, credencial.nombre_usuario, credencial.password_hash)
                    reg_doc += r_doc
                    errores += err2

                except Exception as ex_inner:
                    print(f"EXCEPCION INTERNA CAPTURADA: {type(ex_inner).__name__} - {str(ex_inner)}\n{traceback.format_exc()}", flush=True)
                    raise ex_inner
                finally:
                    context.close()
                    browser.close()

            estado_final = "completado" if errores == 0 else "completado_con_errores"
        except Exception as ex:
            print(f"EXCEPCION EXTERNA CAPTURADA: {type(ex).__name__} - {str(ex)}\n{traceback.format_exc()}", flush=True)
            self.repo.registrar_error(ejecucion.id, "sistema", f"{type(ex).__name__}: {str(ex)}\n{traceback.format_exc()}")
            errores += 1
            estado_final = "error"

        self.repo.finalizar_ejecucion(ejecucion.id, estado_final, reg_est, reg_doc, errores)
        
        return {
            "ejecucion_id": ejecucion.id,
            "estado": estado_final,
            "registros_estudiantes": reg_est,
            "registros_docentes": reg_doc,
            "errores": errores
        }

    def obtener_ejecuciones(self, limit: int = 100, skip: int = 0):
        return self.repo.obtener_ejecuciones(limit, skip)

    def obtener_ejecucion(self, id: int):
        return self.repo.obtener_ejecucion(id)
        
    def obtener_errores(self, limit: int = 100, skip: int = 0):
        return self.repo.obtener_errores(limit, skip)

    def sincronizar_estudiantes(self, ejecucion_id: int):
        from app.modules.estudiantes.models import Estudiante
        from app.modules.importacion.models import StagingEstudiante

        estudiantes_staging = self.repo.db.query(StagingEstudiante).filter(
            StagingEstudiante.ejecucion_id == ejecucion_id
        ).all()

        procesados = 0
        insertados = 0
        actualizados = 0
        rechazados = 0

        for stg in estudiantes_staging:
            procesados += 1
            try:
                # Validacion 1: id_salon NO puede ser NULL
                if stg.id_salon is None:
                    raise ValueError("id_salon es NULL")

                # Validacion 2: documento NO puede ser NULL
                if not stg.documento or str(stg.documento).strip() == "":
                    raise ValueError("documento es NULL o vacio")

                doc_str = str(stg.documento).strip()
                
                # Validacion 3: documento NO debe exceder 10 caracteres (sin truncar silenciosamente)
                if len(doc_str) > 10:
                    raise ValueError(f"documento excede 10 caracteres: '{doc_str}'")

                # Validacion 4: nombre puede truncarse a 100 caracteres
                nom_str = str(stg.nombre).strip() if stg.nombre else ""
                if len(nom_str) > 100:
                    nom_str = nom_str[:100]

                # Logica de Sincronizacion
                est_existente = self.repo.db.query(Estudiante).filter(Estudiante.documento == doc_str).first()
                if est_existente:
                    est_existente.nombre = nom_str
                    est_existente.id_salon = stg.id_salon
                    actualizados += 1
                else:
                    nuevo_est = Estudiante(
                        documento=doc_str,
                        nombre=nom_str,
                        id_salon=stg.id_salon
                    )
                    self.repo.db.add(nuevo_est)
                    insertados += 1
                
                # Commit individual para evitar que un fallo (FK o unique) afecte al lote completo
                self.repo.db.commit()

            except Exception as e:
                self.repo.db.rollback()
                rechazados += 1
                self.repo.registrar_error(
                    ejecucion_id=ejecucion_id,
                    tipo_origen="sincronizacion_estudiante",
                    mensaje=str(e),
                    registro_referencia=stg.documento
                )

        # Confirmar que el commit de inserciones fue exitoso (al procesarse individualmente ya est\u00e1 en BD).
        # Ahora procedemos con la limpieza de los registros temporales.
        try:
            self.repo.db.query(StagingEstudiante).filter(
                StagingEstudiante.ejecucion_id == ejecucion_id
            ).delete(synchronize_session=False)
            self.repo.db.commit()
        except Exception as e:
            self.repo.db.rollback()
            self.repo.registrar_error(ejecucion_id, "limpieza_staging", f"Fallo al limpiar staging: {str(e)}")

        return {
            "procesados": procesados,
            "insertados": insertados,
            "actualizados": actualizados,
            "rechazados": rechazados
        }
