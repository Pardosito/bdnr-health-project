# ============================
# utils.py — Helper para Mongo
# ============================

from bson import ObjectId
from Mongo.services.doctors_service import (
    buscar_doctor_por_id,
    buscar_doctor_por_nombre
)
from Mongo.services.pacientes_service import (
    buscar_paciente_por_id,
    buscar_paciente_por_nombre
)


# ============================
# DOCTORES
# ============================

def get_doctor_id(nombre: str):
    """
    Regresa el ID de un doctor dado su nombre.
    """
    doc = buscar_doctor_por_nombre(nombre)
    if "error" in doc:
        return None
    return doc["_id"]


def get_doctor_by_id(doctor_id: str):
    """
    Devuelve el documento completo del doctor si el ID es válido.
    """
    return buscar_doctor_por_id(doctor_id)



# ============================
# PACIENTES
# ============================

def get_paciente_id(nombre: str):
    """
    Regresa el ID de un paciente dado su nombre.
    """
    pac = buscar_paciente_por_nombre(nombre)
    if "error" in pac:
        return None
    return pac["_id"]


def get_paciente_by_id(paciente_id: str):
    """
    Devuelve el documento completo del paciente si el ID es válido.
    """
    return buscar_paciente_por_id(paciente_id)
