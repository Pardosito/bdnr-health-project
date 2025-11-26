from Mongo.mongo import expedientes
from bson import ObjectId

def crear_expediente(paciente_id):
    data = {
        "paciente_id": ObjectId(paciente_id),
        "alergias": [],
        "padecimientos": [],
        "tratamientos": []
    }
    expedientes.insert_one(data)
    return "Expediente creado correctamente."

def agregar_padecimiento(paciente_id, diagnostico):
    exp = expedientes.find_one({"paciente_id": ObjectId(paciente_id)})

    if not exp:
        return "El paciente no tiene expediente."

    expedientes.update_one(
        {"paciente_id": ObjectId(paciente_id)},
        {"$push": {"padecimientos": diagnostico}}
    )
    return "Padecimiento agregado."
