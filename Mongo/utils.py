# ============================
# utils.py — Helper para Mongo
# ============================

from bson import ObjectId
from Mongo.mongo import doctores, pacientes

# ============================
# DOCTORES
# ============================

def get_doctor_id(nombre: str):
    """
    Regresa el ID de un doctor dado su nombre.
    """
    doc_id = doctores.find_one({"nombre": nombre})

    if not doc_id:
        return "Doctor no encontrado"

    return doc_id["_id"]


def get_doctor_by_id(doctor_id: str):
    """
    Devuelve el documento completo del doctor si el ID es válido.
    """
    doc_nombre = doctores.find_one({"_id": doctor_id})

    if not doc_nombre:
        return "Doctor no encontrado"

    return doc_nombre


# ============================
# PACIENTES
# ============================

def get_paciente_id(nombre: str):
    """
    Regresa el ID de un paciente dado su nombre.
    """
    paciente_id = pacientes.find_one({"nombre": nombre})

    if not paciente_id:
        return "Paciente no encontrado"

    return paciente_id


def get_paciente_by_id(paciente_id: str):
    """
    Devuelve el documento completo del paciente si el ID es válido.
    """
    paciente_nombre = pacientes.find_one({"_id": paciente_id})

    if not paciente_nombre:
        return "Paciente no encontrado"

    return paciente_nombre
