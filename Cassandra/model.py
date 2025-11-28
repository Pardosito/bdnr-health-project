import datetime
import logging
import random
import uuid
from cassandra.query import BatchStatement
from cassandra.util import uuid_from_time

log = logging.getLogger()

# CREACIÓN DE TABLAS

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
      fecha TIMEUUID,
      tipo_visita TEXT,
      paciente_id TEXT,
      doctor_id TEXT,
      hora_inicio TIMEUUID,
      hora_fin TIMEUUID,
      PRIMARY KEY ((fecha), tipo_visita, hora_inicio)
    )
"""

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
      timestamp TIMEUUID,
      PRIMARY KEY ((doctor_id), timestamp, paciente_id, visita_id)
    )
"""

# REQUERIMIENTOS
# INSERTS

# BULK INSERTS
# connect.py deberá llamar a estas funciones de bulk insert


# INSERTS DE REQUERIMIENTOS

# I1 - Reigtrar inicio visita (Esté deberá incluir paciente y doctor ID)
# I2 - Registrar fin visita (Se usará paciente y doctor ID para encontrar la visita a la que se debe registrar el fin)
# I3 - Registrar signos vitales durante visita (Será un insert por cada signo vital, deberá incluir ID de visita)
# I4 - Registrar receta médica generada durante una visita (Deberá insertarse junto con paciente y doctor ID)


# QUERY TIME

# Q1 - Obtener visitas del día, separando por tipo de visita
# Q2 - Obtener todas las recetas emitidas por un doctor (Se le debe de pasar doctor ID)
# Q3 - Obtener diagnóstico y tratamiento de un paciente (Se le debe de pasar paciente ID y fecha)
# Q4 - Conocer disponibilidad de doctor en fecha y hora específica (Se le debe pasar doctor ID y fecha y hora)




def create_keyspace(session, keyspace, replication_factor):
    log.info(f"Creating keyspace: {keyspace} with replication factor {replication_factor}")
    session.execute(CREATE_KEYSPACE.format(keyspace, replication_factor))

def create_schema(session):
    log.info("Creating logistics schema")
    session.execute(CREATE_VISITAS_POR_PACIENTE)
    session.execute(CREATE_VISITAS_DEL_DIA)
    session.execute(CREATE_RECETAS_POR_VISITA)
    session.execute(CREATE_SIGNOS_VITALES_POR_VISITA)
    session.execute(CREATE_DIAGNOSTICOS_POR_VISITA)
