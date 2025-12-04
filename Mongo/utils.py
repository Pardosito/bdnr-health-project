from bson import ObjectId
from Mongo.mongo import doctores, pacientes

# ============================
# DOCTORES
# ============================

def get_doctor_id(nombre: str):
    doc = doctores.find_one({"nombre": nombre})
    if not doc:
        return None  # Retorna None para manejar el error mejor
    return doc["_id"]

def get_doctor_by_id(doctor_id: str):
    """Devuelve el documento completo del doctor convirtiendo el str a ObjectId."""
    if not ObjectId.is_valid(doctor_id):
        return "ID de doctor inválido"

    # CORRECCIÓN: Usar ObjectId()
    doc = doctores.find_one({"_id": ObjectId(doctor_id)})

    if not doc:
        return "Doctor no encontrado"
    return doc

# ============================
# PACIENTES
# ============================

def get_paciente_id(nombre: str):
    pac = pacientes.find_one({"nombre": nombre})
    if not pac:
        return None
    return pac["_id"]

def get_paciente_by_id(paciente_id: str):
    """Devuelve el documento completo del paciente convirtiendo el str a ObjectId."""
    if not ObjectId.is_valid(paciente_id):
        return "ID de paciente inválido"

    # CORRECCIÓN: Usar ObjectId()
    pac = pacientes.find_one({"_id": ObjectId(paciente_id)})

    if not pac:
        return "Paciente no encontrado"
    return pac