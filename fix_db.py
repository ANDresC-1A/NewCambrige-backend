import psycopg2
import sys

try:
    conn = psycopg2.connect("postgresql://postgres:Chacho2708#@localhost:5432/newcambridge")
    cur = conn.cursor()
    print("Conectado a la BD")
    
    # Borrar las tablas staging conflictivas
    cur.execute("DROP TABLE IF EXISTS staging_estudiantes CASCADE;")
    cur.execute("DROP TABLE IF EXISTS staging_docentes CASCADE;")
    cur.execute("DROP TABLE IF EXISTS robot_logs CASCADE;")
    print("Tablas borradas")
    
    # Fijar la version oficial de alembic
    cur.execute("DELETE FROM alembic_version;")
    cur.execute("INSERT INTO alembic_version (version_num) VALUES ('8438a9245df3');")
    print("Alembic version actualizada a la cabecera oficial: 8438a9245df3")
    
    conn.commit()
    cur.close()
    conn.close()
    print("DB fix completado exitosamente.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
