# Requisitos:
# pip install pdfplumber psycopg2-binary unidecode
#
# Ejecutar:
# python Script_poblado.py
#
# =============================================================================

import re
import pdfplumber
import psycopg2

from datetime import datetime
from unidecode import unidecode

# =============================================================================
# CONFIG DB
# =============================================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "newcambridge",
    "user": "postgres",
    "password": "1234"
}

PDF_FILE = "datos_estudiantes_newcambridge.pdf"

# =============================================================================
# MAPA GRADOS
# =============================================================================

MAPA_GRADOS_DB = {

    "PRIMERO": 1,
    "SEGUNDO": 2,
    "TERCERO": 3,
    "CUARTO": 4,
    "QUINTO": 5,
    "SEXTO": 6,
    "SEPTIMO": 7,
    "OCTAVO": 8,
    "NOVENO": 9,
    "DECIMO": 10,
    "ONCE": 11,
    "JARDIN": 12,
    "PARVULOS": 13,
    "PREJARDIN": 14,
    "PREESCOLAR": 15,
    "TRANSICION": 16,
    "NURSERY":17,
}

# =============================================================================
# NORMALIZAR TEXTO
# =============================================================================

def normalizar_texto(texto):

    texto = unidecode(texto)
    texto = texto.upper().strip()

    return texto


# =============================================================================
# CONEXION
# =============================================================================

def get_connection():

    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )


# =============================================================================
# EXTRAER TEXTO PDF
# =============================================================================

def extraer_texto_pdf(pdf_path):

    texto_completo = ""

    with pdfplumber.open(pdf_path) as pdf:

        for pagina in pdf.pages:

            texto = pagina.extract_text()

            if texto:
                texto_completo += texto + "\n"

    return texto_completo


# =============================================================================
# EXTRAER BLOQUES
# =============================================================================

def extraer_datos(texto):

    estudiantes = []

    bloques = texto.split("Lista De Estudiantes")

    for bloque in bloques:

        if "Grado:" not in bloque:
            continue

        # ---------------------------------------------------------------------
        # DATOS DEL BLOQUE
        # ---------------------------------------------------------------------

        grado_match = re.search(r"Grado:\s*(.*?)\s+Curso:", bloque)
        curso_match = re.search(r"Curso:\s*(.*?)\s+Sede:", bloque)
        titular_match = re.search(r"Titular:\s*(.*?)\s+Fecha:", bloque)

        grado_pdf = grado_match.group(1).strip() if grado_match else ""
        curso_pdf = curso_match.group(1).strip() if curso_match else ""
        titular = titular_match.group(1).strip() if titular_match else ""

        grado_normalizado = normalizar_texto(grado_pdf)

        if grado_normalizado not in MAPA_GRADOS_DB:

            print(f"[WARNING] Grado no encontrado: {grado_pdf}")
            continue

        grado_id = MAPA_GRADOS_DB[grado_normalizado]

        # ---------------------------------------------------------------------
        # CURSO -> GRUPO
        # ---------------------------------------------------------------------

        grupo = int(curso_pdf)

        # ---------------------------------------------------------------------
        # ESTUDIANTES
        # ---------------------------------------------------------------------

        lineas = bloque.splitlines()

        for linea in lineas:

            linea = linea.strip()

            match = re.match(
                r"^\d+\s+(\d+)\s+(.+)$",
                linea
            )

            if match:

                documento = match.group(1).strip()
                nombre = match.group(2).strip()

                if "Page" in nombre:
                    continue

                estudiantes.append({
                    "documento": documento,
                    "nombre": nombre,
                    "grado_id": grado_id,
                    "grupo": grupo,
                    "titular": titular
                })

    return estudiantes


# =============================================================================
# OBTENER O CREAR PERIODO
# =============================================================================

def obtener_o_crear_periodo(cursor):

    cursor.execute("""
        SELECT id_periodo
        FROM periodo_academico
        WHERE nombre = '2026'
    """)

    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO periodo_academico (
            nombre,
            activo,
            fecha_inicio,
            fecha_fin
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id_periodo
    """, (
        "2026",
        True,
        datetime(2026, 2, 1),
        datetime(2026, 11, 30)
    ))

    return cursor.fetchone()[0]


# =============================================================================
# OBTENER O CREAR ROL
# =============================================================================

def obtener_o_crear_rol(cursor):

    cursor.execute("""
        SELECT id_rol
        FROM rol
        WHERE UPPER(nombre) = 'TITULAR'
    """)

    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO rol (nombre)
        VALUES ('TITULAR')
        RETURNING id_rol
    """)

    return cursor.fetchone()[0]


# =============================================================================
# OBTENER O CREAR USUARIO
# =============================================================================

def obtener_o_crear_usuario(cursor, nombre_titular):

    cursor.execute("""
        SELECT id_usuario
        FROM usuario
        WHERE UPPER(nombre) = UPPER(%s)
    """, (nombre_titular,))

    row = cursor.fetchone()

    if row:
        return row[0]

    # contraseña temporal
    password_temp = "123456"

    cursor.execute("""
        INSERT INTO usuario (
            nombre,
            contrasena,
            estado
        )
        VALUES (%s, %s, %s)
        RETURNING id_usuario
    """, (
        nombre_titular,
        password_temp,
        True
    ))

    return cursor.fetchone()[0]


# =============================================================================
# OBTENER O CREAR ROL_USUARIO
# =============================================================================

def obtener_o_crear_rol_usuario(cursor, id_rol, id_usuario):

    cursor.execute("""
        SELECT *
        FROM rol_usuario
        WHERE id_rol = %s
        AND id_usuario = %s
    """, (
        id_rol,
        id_usuario
    ))

    row = cursor.fetchone()

    if row:
        return

    cursor.execute("""
        INSERT INTO rol_usuario (
            id_rol,
            id_usuario
        )
        VALUES (%s, %s)
    """, (
        id_rol,
        id_usuario
    ))


# =============================================================================
# OBTENER O CREAR SALON
# =============================================================================

def obtener_o_crear_salon(
    cursor,
    id_usuario,
    grado,
    grupo,
    id_periodo
):

    cursor.execute("""
        SELECT id_salon
        FROM salon
        WHERE grado = %s
        AND grupo = %s
        AND id_periodo = %s
    """, (
        grado,
        grupo,
        id_periodo
    ))

    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO salon (
            id_usuario,
            grado,
            grupo,
            id_periodo
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id_salon
    """, (
        id_usuario,
        grado,
        grupo,
        id_periodo
    ))

    return cursor.fetchone()[0]


# =============================================================================
# OBTENER O CREAR ESTUDIANTE
# =============================================================================

def obtener_o_crear_estudiante(
    cursor,
    nombre,
    documento,
    id_salon
):

    cursor.execute("""
        SELECT id_estudiante
        FROM estudiante
        WHERE documento = %s
    """, (documento,))

    row = cursor.fetchone()

    # -------------------------------------------------------------------------
    # SI EXISTE
    # -------------------------------------------------------------------------

    if row:

        id_estudiante = row[0]

        # FUTURO UPDATE
        # cursor.execute(...)

        return id_estudiante

    # -------------------------------------------------------------------------
    # CREAR
    # -------------------------------------------------------------------------

    cursor.execute("""
        INSERT INTO estudiante (
            nombre,
            telefono_acudiente,
            id_salon,
            documento
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id_estudiante
    """, (
        nombre,
        "",
        id_salon,
        documento
    ))

    return cursor.fetchone()[0]


# =============================================================================
# MAIN
# =============================================================================

def main():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        print("Leyendo PDF...")

        texto = extraer_texto_pdf(PDF_FILE)

        print("Extrayendo datos...")

        estudiantes = extraer_datos(texto)

        print(f"Total encontrados: {len(estudiantes)}")

        # ---------------------------------------------------------------------
        # CREAR BASES
        # ---------------------------------------------------------------------

        id_periodo = obtener_o_crear_periodo(cursor)

        id_rol = obtener_o_crear_rol(cursor)

        # ---------------------------------------------------------------------
        # RECORRER
        # ---------------------------------------------------------------------

        for est in estudiantes:

            id_usuario = obtener_o_crear_usuario(
                cursor,
                est["titular"]
            )

            obtener_o_crear_rol_usuario(
                cursor,
                id_rol,
                id_usuario
            )

            id_salon = obtener_o_crear_salon(
                cursor,
                id_usuario,
                est["grado_id"],
                est["grupo"],
                id_periodo
            )

            obtener_o_crear_estudiante(
                cursor,
                est["nombre"],
                est["documento"],
                id_salon
            )

        conn.commit()

        print("======================================")
        print("DATOS IMPORTADOS CORRECTAMENTE")
        print("======================================")

    except Exception as e:

        conn.rollback()

        print("ERROR:")
        print(e)

    finally:

        cursor.close()
        conn.close()


# =============================================================================
# EJECUCION
# =============================================================================

if __name__ == "__main__":
    main()