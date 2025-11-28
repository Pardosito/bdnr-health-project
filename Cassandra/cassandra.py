import os
import model

CLUSTER_IPS = os.getenv('CASSANDRA_CLUSTER_IPS', '127.0.0.1')
KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'health_service')
REPLICATION_FACTOR = os.getenv('CASSANDRA_REPLICATION_FACTOR', '1')

def registro_inicio_visita():
  pass

def registro_fin_visita():
  pass

def obtener_visitas_del_dia():
  pass

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

