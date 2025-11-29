from bson import ObjectId
from .collections import get_collections


def crear_expediente(paciente_id):
    _, _, expedientes = get_collections()
    data = {
        "paciente_id": ObjectId(paciente_id),
        "alergias": [],
        "padecimientos": [],
        "tratamientos": []
    }
    expedientes.insert_one(data)
    return "Expediente creado correctamente."


def agregar_padecimiento(paciente_id, diagnostico):
    _, _, expedientes = get_collections()
    exp = expedientes.find_one({"paciente_id": ObjectId(paciente_id)})

    if not exp:
        return "El paciente no tiene expediente."

    expedientes.update_one(
        {"paciente_id": ObjectId(paciente_id)},
        {"$push": {"padecimientos": diagnostico}}
    )
    return "Padecimiento agregado."
