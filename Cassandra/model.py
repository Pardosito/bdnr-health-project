import datetime
import uuid

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

CREATE_INDEX_DOCTOR = "CREATE INDEX IF NOT EXISTS idx_visitas_doctor ON visitas_del_dia (doctor_id)"
CREATE_INDEX_PACIENTE = "CREATE INDEX IF NOT EXISTS idx_visitas_paciente ON visitas_del_dia (paciente_id)"

CREATE_RECETAS_POR_VISITA = """
    CREATE TABLE IF NOT EXISTS recetas_por_visita (
      paciente_id TEXT,
      doctor_id TEXT,
      visita_id TEXT,
      receta TEXT,
      fecha_registro TIMEUUID,
      PRIMARY KEY ((doctor_id), visita_id, fecha_registro)
    )
"""

CREATE_SIGNOS_VITALES_POR_VISITA = """
    CREATE TABLE IF NOT EXISTS signos_vitales_por_visita (
      paciente_id TEXT,
      doctor_id TEXT,
      visita_id TEXT,
      tipo_medicion TEXT,
      valor TEXT,
      fecha_registro TIMEUUID,
      PRIMARY KEY ((tipo_medicion, paciente_id), fecha_registro)
    )
"""

CREATE_DIAGNOSTICOS_POR_VISITA = """
    CREATE TABLE IF NOT EXISTS diagnosticos_por_visita (
      paciente_id TEXT,
      doctor_id TEXT,
      visita_id TEXT,
      diagnostico TEXT,
      fecha DATE,
      momento_registro TIMEUUID,
      PRIMARY KEY ((doctor_id), paciente_id, fecha, momento_registro)
    )
"""

# INSERTS DE REQUERIMIENTOS

# I1 - Registrar inicio visita
inicio_visita_stmt = """
    INSERT INTO visitas_por_paciente (paciente_id, doctor_id, timestamp_inicio, timestamp_fin)
    VALUES (?, ?, ?, ?)
"""

# I2 - Registrar fin visita
fin_visita_stmt = """
    UPDATE visitas_por_paciente
    SET timestamp_fin = now()
    WHERE paciente_id = ? AND timestamp_inicio = ?
"""

# I3 - Registrar signos vitales
signo_vital_registro_stmt = """
    INSERT INTO signos_vitales_por_visita (paciente_id, doctor_id, visita_id, tipo_medicion, valor, fecha_registro)
    VALUES (?, ?, ?, ?, ?, ?)
"""

# I4 - Registrar receta médica
recete_medica_registro_stmt = """
    INSERT INTO recetas_por_visita (paciente_id, doctor_id, visita_id, receta, fecha_registro)
    VALUES (?, ?, ?, ?, ?)
"""


# QUERY TIME

# Q1 - Obtener visitas del día
SELECT_VISITAS_POR_DIA = """
    SELECT fecha, paciente_id, doctor_id, hora_inicio, hora_fin, tipo_visita
    FROM visitas_del_dia
    WHERE fecha = ?
"""

# Q2 - Obtener recetas por doctor
SELECT_RECETAS_EMITIDAS = """
    SELECT doctor_id, receta, paciente_id, visita_id
    FROM recetas_por_visita
    WHERE doctor_id = ?
"""

# Q3 - Diagnóstico de paciente
SELECT_DIAGNOSTICO_DE_PACIENTE = """
    SELECT paciente_id, diagnostico, doctor_id, fecha
    FROM diagnosticos_por_visita
    WHERE doctor_id = ? AND paciente_id = ? AND fecha = ?
"""

# Q4 - Disponibilidad
SELECT_DISPONIBILIDAD_DOCTOR = """
    SELECT fecha, doctor_id, paciente_id, tipo_visita, hora_inicio, hora_fin
    FROM visitas_del_dia
    WHERE fecha = ? AND doctor_id = ?
"""

# Query para populate
INSERT_VISITA_DEL_DIA = """
    INSERT INTO visitas_del_dia (fecha, tipo_visita, paciente_id, doctor_id, hora_inicio, hora_fin)
    VALUES (?, ?, ?, ?, ?, ?)
"""
INSERT_DIAGNOSTICO = """
    INSERT INTO diagnosticos_por_visita (paciente_id, doctor_id, visita_id, diagnostico, fecha, momento_registro)
    VALUES (?, ?, ?, ?, ?, ?)
"""


def create_keyspace(session, keyspace, replication_factor):
    print("Creando keyspace...")
    session.execute(CREATE_KEYSPACE.format(keyspace, replication_factor))

def create_schema(session):
    print("Creando tablas e índices...")
    session.execute(CREATE_VISITAS_POR_PACIENTE)
    session.execute(CREATE_VISITAS_DEL_DIA)
    session.execute(CREATE_INDEX_DOCTOR)
    session.execute(CREATE_INDEX_PACIENTE)

    session.execute(CREATE_RECETAS_POR_VISITA)
    session.execute(CREATE_SIGNOS_VITALES_POR_VISITA)
    session.execute(CREATE_DIAGNOSTICOS_POR_VISITA)