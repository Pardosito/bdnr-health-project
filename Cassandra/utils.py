from datetime import datetime
import uuid
from enum import Enum

def get_visita_id(session, fecha_busqueda, doctor_id, paciente_id):
    query = """
        SELECT hora_inicio
        FROM visitas_del_dia
        WHERE fecha = ?
          AND doctor_id = ?
          AND paciente_id = ?
    """

    try:
        # fecha_busqueda debe ser tipo date(), ej: date(2023, 10, 27)
        stmt = session.prepare(query)
        row = session.execute(stmt, [fecha_busqueda, doctor_id, paciente_id]).one()

        return row.hora_inicio if row else None

    except Exception as e:
        print(f"Error buscando visita: {e}")
        return None

def get_visita_activa(session, paciente_id):
    query = """
        SELECT timestamp_inicio, timestamp_fin
        FROM visitas_por_paciente
        WHERE paciente_id = ?
        LIMIT 1
    """
    if paciente_id is None:
        print("[Cassandra.utils] get_visita_activa: paciente_id es None — no se puede consultar visita activa.")
        return None
    stmt = session.prepare(query)
    row = session.execute(stmt, [paciente_id]).one()

    if row:
        if row.timestamp_fin is None:
            return row.timestamp_inicio
        else:
            print("El paciente no tiene visitas activas.")
            return None
    return None

class visitasEnum(Enum):
        CONSULTA_INICIAL = 1
        CONSULTA_SEGUIMIENTO = 2
        URGENCIA = 3
        PREVENTIVA = 4
        POST_CIRUGIA = 5
        REVISION_MEDICA = 6


class medicionesEnum(Enum):
        PRESION = 1
        RITMO_CARDIACO = 2
        TEMPERATURA = 3
        OXIGENO = 4
        FREC_RESPIRATORIA = 5
        PESO = 6
        ESTATURA = 7


