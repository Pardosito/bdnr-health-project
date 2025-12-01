import os
import model
from cassandra.cluster import Cluster
from Mongo.utils import get_doctor_id, get_paciente_id, get_doctor_by_id, get_paciente_by_id
from utils import get_visita_id, get_visita_activa, visitasEnum, medicionesEnum
import uuid
from connect import get_cassandra

session = get_cassandra()

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

def registrar_signo_vital(nombre_paciente, nombre_doctor, tipo_medicion: medicionesEnum, valor):
  paciente = get_paciente_id(nombre_paciente)
  doctor = get_doctor_id(nombre_doctor)
  visita = get_visita_activa(session, paciente)
  if tipo_medicion.name not in medicionesEnum:
    raise "Tipo de medición no válida"
  tipo_medicion = tipo_medicion
  valor = valor
  try:
    stmt = session.prepare(model.signo_vital_registro_stmt)
    session.execute(stmt, [paciente, doctor, visita, tipo_medicion.name, valor, uuid.uuid1()])
    print(f"Signo vital {tipo_medicion} registrado correctamente")
  except Exception as e:
    print(f"Error al registrar signo vital: {e}")

def registrar_receta_por_visita(nombre_paciente, nombre_doctor, visita_id, receta):
  paciente = get_paciente_id(nombre_paciente)
  doctor = get_doctor_id(nombre_doctor)
  visita = get_visita_activa(session, paciente)
  if not receta:
    raise "La receta necesita contenido para ser guardada"
  receta = receta
  try:
    stmt = session.prepare(model.recete_medica_registro_stmt)
    session.execute(stmt, [paciente, doctor, visita, receta])
    print(f"Receta por doctor {nombre_doctor} guardada correctamente")
  except Exception as e:
    print(f"Error guardando receta: {e}")

def consultar_recetas_por_doctor(nombre_doctor):
  doctor = get_doctor_id(nombre_doctor)
  try:
    stmt = session.prepare(model.SELECT_RECETAS_EMITIDAS)
    rows = session.execute(stmt, [doctor])
    if not rows:
      print(f"Doctor {nombre_doctor} no tiene citas almacenadas")
      return None
    for row in rows:
      print(f"DOCTOR: {get_doctor_by_id(row.doctor_id)}   PACIENTE: {row.paciente_id}   RECETA: {row.receta}")
  except Exception as e:
    print(f"Error obteniendo recetas: {e}")

def obtener_diagnostico_tratamiento_paciente(nombre_doctor, nombre_paciente, fecha): #Se le debe pasar fecha
  doctor = get_doctor_id(nombre_doctor)
  paciente = get_paciente_id(nombre_paciente)
  try:
    stmt = session.prepare(model.SELECT_DIAGNOSTICO_DE_PACIENTE)
    diagnotisco = session.execute(stmt, [doctor, paciente, fecha])
    print(f"DOCTOR: {get_doctor_by_id(diagnotisco.doctor_id)}  PACIENTE: {get_paciente_by_id(diagnotisco.pacient_id)}   DIAGNOSTICO: {diagnotisco.diagnostico}  FECHA: {diagnotisco.fecha}")
  except Exception as e:
    print(f"Error obteniendo diágnostico: {e}")

def verificar_disponibilidad_doctor(nombre_doctor, fecha): #Se le debe pasar fehca
  doctor = get_doctor_id(nombre_doctor)
  try:
    stmt = session.prepare(model.SELECT_DISPONIBILIDAD_DOCTOR)
    rows = session.execute(stmt, [fecha, doctor])
    for row in rows:
      print(f"DOCTOR: {get_doctor_by_id(row.doctor_id)}   PACIENTE: {get_paciente_by_id(row.paciente_id)}   TIPO_VISITA: {row.tipo_visita}  FEHCHA: {row.fecha}")
  except Exception as e:
    print(f"Error obteniendo disponibilidad: {e}")

