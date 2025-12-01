import os
from . import model
from cassandra.cluster import Cluster
from Mongo.utils import get_doctor_id, get_paciente_id, get_doctor_by_id, get_paciente_by_id
from .utils import get_visita_id, get_visita_activa, visitasEnum, medicionesEnum
import uuid
from connect import get_cassandra
from datetime import date, datetime

session = get_cassandra()

def registro_inicio_visita(paciente, doctor):
  paciente_id = get_paciente_id(paciente)
  doctor_id = get_doctor_id(doctor)

  try:
    stmt = session.prepare(model.inicio_visita_stmt)
    session.execute(stmt, [str(paciente_id), str(doctor_id), uuid.uuid1(), None])
    print("Visita iniciada exitosamente")
  except Exception as e:
    print(f"Error iniciando visita: {e}")


def registro_fin_visita(paciente):
  paciente_id = get_paciente_id(paciente)
  hora_inicio = get_visita_activa(session, paciente_id)

  try:
    stmt = session.prepare(model.fin_visita_stmt)
    session.execute(stmt, [str(paciente_id), hora_inicio])
    print("Visita finalizada exitosamente")
  except Exception as e:
    print(f"Error finalizando visita: {e}")

def obtener_visitas_del_dia(fecha):
  objeto_fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
  try:
    stmt = session.prepare(model.SELECT_VISITAS_POR_DIA)
    rows = session.execute(stmt, [objeto_fecha])
    rows_list = list(rows)
    print(f"Consultando visitas para fecha={objeto_fecha} — filas encontradas: {len(rows_list)}")
    if not rows_list:
      return
    for row in rows_list:
      print(f"DOCTOR: {get_doctor_by_id(row.doctor_id)}   PACIENTE: {get_paciente_by_id(row.paciente_id)}   TIPO VISITA: {row.tipo_visita}  HORA INICIO: {row.hora_inicio}")
  except Exception as e:
    print(f"Error obteniendo visitas: {e}")

def registrar_signo_vital(nombre_paciente, nombre_doctor, tipo_medicion, valor):
  paciente = get_paciente_id(nombre_paciente)
  doctor = get_doctor_id(nombre_doctor)

  if paciente is None:
    print(f"Paciente '{nombre_paciente}' no encontrado en MongoDB (get_paciente_id devolvió None).")
    return None
  if doctor is None:
    print(f"Doctor '{nombre_doctor}' no encontrado en MongoDB (get_doctor_id devolvió None).")
    return None

  enum_member = None
  try:
    for m in medicionesEnum:
      if m.name.lower() == str(tipo_medicion).strip().lower():
        enum_member = m
        break
  except Exception:
    enum_member = None

  if enum_member is None:
    valid = ", ".join([m.name for m in medicionesEnum])
    print(f"Tipo de medición inválido: '{tipo_medicion}'. Valores válidos: {valid}")
    return None

  visita = get_visita_activa(session, paciente)
  if visita is None:
    print(f"No se encontró visita activa para paciente_id={paciente}. El signo será registrado sin referencia de visita.")

  try:
    stmt = session.prepare(model.signo_vital_registro_stmt)
    session.execute(stmt, [str(paciente), str(doctor), str(visita) if visita is not None else None, enum_member.name, str(valor), uuid.uuid1()])
    print(f"Signo vital {enum_member.name} registrado correctamente para paciente_id={paciente}.")
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
    session.execute(stmt, [str(paciente), str(doctor), str(visita) if visita is not None else visita_id, receta])
    print(f"Receta por doctor {nombre_doctor} guardada correctamente")
  except Exception as e:
    print(f"Error guardando receta: {e}")

def consultar_recetas_por_doctor(nombre_doctor):
  doctor = get_doctor_id(nombre_doctor)
  try:
    stmt = session.prepare(model.SELECT_RECETAS_EMITIDAS)
    rows = session.execute(stmt, [str(doctor)])
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
    diagnotisco = session.execute(stmt, [str(doctor), str(paciente), fecha])
    # diagnotisco puede ser un cursor; iterar para mostrar resultados
    for row in diagnotisco:
      print(f"DOCTOR: {get_doctor_by_id(row.doctor_id)}  PACIENTE: {get_paciente_by_id(row.paciente_id)}   DIAGNOSTICO: {row.diagnostico}  FECHA: {row.fecha}")
  except Exception as e:
    print(f"Error obteniendo diágnostico: {e}")

def verificar_disponibilidad_doctor(nombre_doctor, fecha): #Se le debe pasar fehca
  doctor = get_doctor_id(nombre_doctor)
  try:
    stmt = session.prepare(model.SELECT_DISPONIBILIDAD_DOCTOR)
    rows = session.execute(stmt, [fecha, str(doctor)])
    for row in rows:
      print(f"DOCTOR: {get_doctor_by_id(row.doctor_id)}   PACIENTE: {get_paciente_by_id(row.paciente_id)}   TIPO_VISITA: {row.tipo_visita}  FEHCHA: {row.fecha}")
  except Exception as e:
    print(f"Error obteniendo disponibilidad: {e}")

