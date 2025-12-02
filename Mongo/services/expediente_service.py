from Mongo.mongo import expedientes
from bson import ObjectId


#crear expediente
def crear_expediente(paciente_id: str) -> dict:
    """Crea un expediente vacío para un paciente."""

    if not ObjectId.is_valid(paciente_id):
        return {"error": "ID de paciente inválido."}

    paciente_id = ObjectId(paciente_id)

    # Verificar si ya existe
    existente = expedientes.find_one({"paciente_id": paciente_id})
    if existente:
        return {"mensaje": "El paciente ya tiene expediente."}

    data = {
        "paciente_id": paciente_id,
        "alergias": [],
        "padecimientos": [],
        "tratamientos": []
    }

    expedientes.insert_one(data)
    return {"mensaje": "Expediente creado correctamente."}



#obtener expediente
def obtener_expediente(paciente_id: str):
    """Devuelve el expediente completo del paciente."""

    if not ObjectId.is_valid(paciente_id):
        return {"error": "ID de paciente inválido."}

    exp = expedientes.find_one({"paciente_id": ObjectId(paciente_id)})

    if not exp:
        return {"mensaje": "El paciente no tiene expediente."}

    # convertir ObjectId a string para imprimir bonita
    exp["_id"] = str(exp["_id"])
    exp["paciente_id"] = str(exp["paciente_id"])

    return exp



#agregar alergia
def agregar_alergia(paciente_id: str, alergia: str):
    """Agrega una alergia al expediente del paciente."""

    if not ObjectId.is_valid(paciente_id):
        return {"error": "ID inválido."}

    exp = expedientes.find_one({"paciente_id": ObjectId(paciente_id)})

    if not exp:
        return {"error": "El paciente no tiene expediente."}

    expedientes.update_one(
        {"paciente_id": ObjectId(paciente_id)},
        {"$push": {"alergias": alergia}}
    )

    return {"mensaje": "Alergia agregada."}



#agregar padecimiento
def agregar_padecimiento(paciente_id: str, diagnostico: str):
    """Agrega un diagnóstico/padecimiento al expediente."""

    if not ObjectId.is_valid(paciente_id):
        return {"error": "ID inválido."}

    exp = expedientes.find_one({"paciente_id": ObjectId(paciente_id)})
    if not exp:
        return {"error": "El paciente no tiene expediente."}

    expedientes.update_one(
        {"paciente_id": ObjectId(paciente_id)},
        {"$push": {"padecimientos": diagnostico}}
    )

    return {"mensaje": "Padecimiento agregado."}



#agregar tratamiento
def agregar_tratamiento(paciente_id: str, tratamiento: str):
    """Agrega un tratamiento al expediente del paciente."""

    if not ObjectId.is_valid(paciente_id):
        return {"error": "ID inválido."}

    exp = expedientes.find_one({"paciente_id": ObjectId(paciente_id)})
    if not exp:
        return {"error": "El paciente no tiene expediente."}

    expedientes.update_one(
        {"paciente_id": ObjectId(paciente_id)},
        {"$push": {"tratamientos": tratamiento}}
    )

    return {"mensaje": "Tratamiento agregado."}
