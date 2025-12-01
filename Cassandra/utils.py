from datetime import datetime
import uuid
from cassandra.query import SimpleStatement

def get_visita_id(session, fecha_busqueda, doctor_id, paciente_id):
    query = """
        SELECT hora_inicio
        FROM visitas_del_dia
        WHERE fecha = ?
          AND doctor_id = ?
          AND paciente_id = ?
    """

    try:
        # fecha_busqueda debe ser un tipo date(), ej: date(2023, 10, 27)
        stmt = session.prepare(query)
        row = session.execute(stmt, [fecha_busqueda, doctor_id, paciente_id]).one()

        return row.hora_inicio if row else None

    except Exception as e:
        print(f"Error buscando visita: {e}")
        return None

def obtener_visita_activa(session, paciente_id):
    query = """
        SELECT timestamp_inicio, timestamp_fin
        FROM visitas_por_paciente
        WHERE paciente_id = ?
        LIMIT 1
    """
    stmt = session.prepare(query)
    row = session.execute(stmt, [paciente_id]).one()

    if row:
        if row.timestamp_fin is None:
            return row.timestamp_inicio
        else:
            print("El paciente no tiene visitas activas.")
            return None
    return None