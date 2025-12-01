import datetime
import logging
import random
import uuid
from cassandra import session

# creación de tablas

CREATE_KEYSPACE = """
    CREATE KEYSPACE IF NOT EXISTS {}
    WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': {} }}
"""

CREATE_VISITAS_POR_PACIENTE = """
    CREATE TABLE IF NOT EXISTS visitas_por_paciente (
      paciente_id TEXT,
      doctor_id TEXT,
      timestamp_inicio TIMEUUID,
      timestamp_fin TIMEUUID,
      PRIMARY KEY ((paciente_id), timestamp_inicio)
    ) WITH CLUSTERING ORDER BY (timestamp_inicio DESC)
"""

CREATE_VISITAS_DEL_DIA = """
    CREATE TABLE IF NOT EXISTS visitas_del_dia (
      fecha DATE,
      tipo_visita TEXT,
      paciente_id TEXT,
      doctor_id TEXT,
      hora_inicio TIMEUUID,
      hora_fin TIMEUUID,
      PRIMARY KEY ((fecha), tipo_visita, hora_inicio)
    )
"""

CREATE_INDEX_DOCTOR = "CREATE INDEX IF NOT EXISTS index_visitas_doctor ON visitas_del_dia (doctor_id)"
CREATE_INDEX_PACIENTE = "CREATE INDEX IF NOT EXISTS index_visitas_paciente ON visitas_del_dia (paciente_id)"

CREATE_RECETAS_POR_VISITA = """
    CREATE TABLE IF NOT EXISTS recetas_por_visita (
      paciente_id TEXT,
      doctor_id TEXT,
      visita_id TEXT,
      receta TEXT,
      PRIMARY KEY ((doctor_id), visita_id)
    )
"""

CREATE_SIGNOS_VITALES_POR_VISITA = """
    CREATE TABLE IF NOT EXISTS signos_vitales_por_visita (
      paciente_id TEXT,
      doctor_id TEXT,
      visita_id TEXT,
      tipo_medicion TEXT,
      valor TEXT,
      timestamp TIMEUUID,
      PRIMARY KEY ((tipo_medicion, paciente_id), timestamp)
    )
"""

CREATE_DIAGNOSTICOS_POR_VISITA = """
    CREATE TABLE IF NOT EXISTS diagnosticos_por_visita (
      paciente_id TEXT,
      doctor_id TEXT,
      visita_id TEXT,
      diagnostico TEXT,
      fecha DATE
      PRIMARY KEY ((doctor_id), paciente_id, fecha)
    )
"""

# REQUERIMIENTOS
# INSERTS

# BULK INSERTS
# connect.py deberá llamar a estas funciones de bulk insert
def bulk_inserts(self):
  pass


# INSERTS DE REQUERIMIENTOS

# I1 - Registrar inicio visita (Esté deberá incluir paciente y doctor ID)
inicio_visita_stmt = session.prepare(
  "INSERT INTO visitas_por_paciente (paciente_id, doctor_id, timestamp_inicio, timestamp_fin) VALUES (?, ?, ?, ?)" # ULTIMO VALOR DEBERÁ SER NULO O INDICAR 0, YA QUE LA SESION SIGUE ACTIVA
)
# I2 - Registrar fin visita (Se usará paciente ID y timestamp para encontrar la visita a la que se debe registrar el fin)
fin_visita_stmt = session.prepare("""
  UPDATE visitas_por_paciente
  SET timestamp_fin = now()
  WHERE paciente_id = ? AND timestamp_inicio = ?
""")
# I3 - Registrar signos vitales durante visita (Será un insert por cada signo vital, deberá incluir ID de visita)
signo_vital_registro_stmt = session.prepare(
  "INSERT INTO signos_vitales_por_visita (paciente_id, doctor_id, visita_id, tipo_medicion, valor, timestamp) VALUES (?, ?, ?, ?, ?, ?)"
)
# I4 - Registrar receta médica generada durante una visita (Deberá insertarse junto con paciente y doctor ID)
recete_medica_registro_stmt = session.prepare(
  "INSERT INTO recetas_por_visita (paciente_id, doctor_id, visita_id, receta) VALUES (?, ?, ?, ?)"
)


# QUERY TIME

# Q1 - Obtener visitas del día, separando por tipo de visita
SELECT_VISITAS_POR_DIA = """
    SELECT fecha, paciente_id, doctor_id, hora_inicio, hora_fin
    FROM visitas_por_dia
    WHERE fecha = ?
"""
# Q2 - Obtener todas las recetas emitidas por un doctor (Se le debe de pasar doctor ID)
SELECT_RECETAS_EMITIDAS = """
    SELECT doctor_id, receta, paciente_id
    FROM recetas_por_visita
    WHERE doctor_id = ?
"""
# Q3 - Obtener diagnóstico y tratamiento de un paciente (Se le debe de pasar paciente ID y fecha)
SELECT_DIAGNOSTICO_DE_PACIENTE = """
    SELECT paciente_id, diagnostico, doctor_id
    FROM diagnosticos_por_visita
    WHERE doctor_id = ? AND paciente_id = ? AND fecha = ?
"""
# Q4 - Conocer disponibilidad de doctor en fecha y hora específica (Se le debe pasar doctor ID y fecha y hora)
SELECT_DISPONIBILIDAD_DOCTOR = """
    SELECT fecha, doctor_id, paciente_id, tipo_visita, hora_inicio, hora_fin
    FROM visitas_del_dia
    WHERE fecha = ? AND doctor_id = ?
"""

def create_keyspace(session, keyspace, replication_factor):
    print("creando keyspace")
    session.execute(CREATE_KEYSPACE.format(keyspace, replication_factor))

def create_schema(session):
    print("Creando tablas")
    session.execute(CREATE_VISITAS_POR_PACIENTE)
    session.execute(CREATE_VISITAS_DEL_DIA)
    session.execute(CREATE_RECETAS_POR_VISITA)
    session.execute(CREATE_SIGNOS_VITALES_POR_VISITA)
    session.execute(CREATE_DIAGNOSTICOS_POR_VISITA)
