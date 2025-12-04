from Mongo.mongo import expedientes
from Mongo.utils import get_paciente_id
from bson import ObjectId


#crear expediente
def crear_expediente(identificador: str) -> dict:
    """Crea un expediente vacío para un paciente."""

    paciente_id = None

    if ObjectId.is_valid(identificador):
        paciente_id = ObjectId(identificador)
    else:
        raw_paciente = get_paciente_id(identificador)
        if isinstance(raw_paciente, dict):
            paciente_id = raw_paciente["_id"]
        elif isinstance(raw_paciente, ObjectId):
            paciente_id = raw_paciente
        else:
             return {"error": f"No se encontró paciente con nombre '{identificador}'"}

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

    exp = expedientes.find_one({"paciente_id": paciente_id})

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

    exp = expedientes.find_one({"paciente_id": paciente_id})

    if not exp:
        return {"error": "El paciente no tiene expediente."}

    expedientes.update_one(
        {"paciente_id": ObjectId(paciente_id)},
        {"$push": {"alergias": alergia}}
    )

    return {"mensaje": "Alergia agregada."}



#agregar padecimiento
def agregar_padecimiento(nombre: str, diagnostico: str):
    """Agrega un diagnóstico/padecimiento al expediente."""

    paciente_id = get_paciente_id(nombre)
    if not paciente_id:
        return f"Error: No se encontró ningún paciente"

    exp = expedientes.find_one({"paciente_id": paciente_id})
    if not exp:
        return "El paciente no tiene expediente."

    expedientes.update_one(
        {"paciente_id": paciente_id},
        {"$push": {"padecimientos": diagnostico}}
    )

    return "Padecimiento agregado."


#agregar tratamiento
def agregar_tratamiento(paciente_id: str, tratamiento: str):
    """Agrega un tratamiento al expediente del paciente."""

    if not ObjectId.is_valid(paciente_id):
        return {"error": "ID inválido."}

    exp = expedientes.find_one({"paciente_id": paciente_id})
    if not exp:
        return {"error": "El paciente no tiene expediente."}

    expedientes.update_one(
        {"paciente_id": ObjectId(paciente_id)},
        {"$push": {"tratamientos": tratamiento}}
    )

    return {"mensaje": "Tratamiento agregado."}
