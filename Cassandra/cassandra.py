import os
import model
from cassandra.cluster import Cluster
from Mongo.utils import get_doctor_id, get_paciente_id, get_doctor_by_id, get_paciente_by_id
from utils import get_visita_id, get_visita_activa
import uuid

CLUSTER_IPS = os.getenv('CASSANDRA_CLUSTER_IPS', '127.0.0.1')
KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'health_service')
REPLICATION_FACTOR = os.getenv('CASSANDRA_REPLICATION_FACTOR', '1')
cluster = Cluster(CLUSTER_IPS.split(","))
session = cluster.connect()

model.create_keyspace(session, KEYSPACE, REPLICATION_FACTOR)
session.set_keyspace(KEYSPACE)

model.create_schema(session)

def registro_inicio_visita(paciente, doctor):
  paciente_id = get_paciente_id(paciente)
  doctor_id = get_doctor_id(doctor)

  try:
    stmt = session.prepare(model.inicio_visita_stmt)
    session.execute(stmt, [paciente_id, doctor_id, uuid.uuid1(), None])
    print("Visita iniciada exitosamente")
  except Exception as e:
    print(f"Error iniciando visita: {e}")


def registro_fin_visita(paciente):
  paciente_id = get_paciente_id(paciente)
  hora_inicio = get_visita_activa(session, paciente_id)

  try:
    stmt = session.prepare(model.fin_visita_stmt)
    session.execute(stmt, [paciente_id, hora_inicio])
    print("Visita finalizada exitosamente")
  except Exception as e:
    print(f"Error finalizando visita: {e}")

def obtener_visitas_del_dia():
  try:
    stmt = session.prepare(model.SELECT_VISITAS_POR_DIA)
    rows = session.execute(stmt)
    for row in rows:
      print(f"DOCTOR: {get_doctor_by_id(row.doctor_id)}   PACIENTE: {get_paciente_by_id(row.paciente_id)}   TIPO VISITA: {row.tipo_visita}  HORA INICIO: {row.hora_inicio}")
  except Exception as e:
    print(f"Error obteniendo visitas: {e}")

def registrar_signo_vital():
  pass

def registrar_receta_por_visita():
  pass

def consultar_recetas_por_doctor():
  pass

def obtener_diagnostico_tratamiento_paciente(): #Se le debe pasar fecha
  pass

def verificar_disponibilidad_doctor(): #Se le debe pasar fehca
  pass

