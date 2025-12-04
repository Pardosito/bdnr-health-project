from Mongo.mongo import expedientes
from Mongo.utils import get_paciente_id
from bson import ObjectId
from Cassandra.cassandra import session
from Cassandra import model
from datetime import date
from Mongo.utils import get_doctor_id
import uuid


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
def agregar_padecimiento(nombre_paciente: str, diagnostico: str, nombre_doctor: str = None):
    raw_id = get_paciente_id(nombre_paciente)
    if not raw_id:
        return "Error: No se encontró ningún paciente"

    paciente_id = ObjectId(raw_id)

    exp = expedientes.find_one({"paciente_id": paciente_id})
    if not exp:
        return "El paciente no tiene expediente creado."

    expedientes.update_one(
        {"paciente_id": paciente_id},
        {"$addToSet": {"padecimientos": diagnostico}}
    )

    mensaje = f"Padecimiento agregado a paciente {nombre_paciente}."

    if nombre_doctor:
        doc_id = get_doctor_id(nombre_doctor)
        if doc_id:
            try:
                stmt = session.prepare(model.INSERT_DIAGNOSTICO)
                today = date.today().strftime("%Y-%m-%d")
                session.execute(stmt, [str(paciente_id), str(doc_id), None, diagnostico, today, uuid.uuid1()])
            except Exception as e:
                mensaje += f"(Error sincronizando dbs: {e})"
        else:
            mensaje += " (No sincronizado: Doctor no encontrado)"
    else:
        mensaje += " (No sincronizado: Se requiere nombre del doctor)"

    return mensaje


#agregar tratamiento
def agregar_tratamiento(nombre_paciente: str, nombre_doctor: str, tratamiento: str):
    """Agrega un tratamiento al expediente del paciente."""
    tratamiento = tratamiento
    if not tratamiento:
        return "Se debe ingresar un tratamiento"

    raw_id = get_paciente_id(nombre_paciente)
    if not raw_id:
        return "Error: No se encontró ningún paciente"

    paciente_id = ObjectId(raw_id)

    exp = expedientes.find_one({"paciente_id": paciente_id})
    if not exp:
        return "El paciente no tiene expediente creado."

    expedientes.update_one(
        {"paciente_id": paciente_id},
        {"$addToSet": {"tratamientos": tratamiento}}
    )

    mensaje = f"Tratamiento {tratamiento} agregado."

    if nombre_doctor:
        doc_id = get_doctor_id(nombre_doctor)
        if doc_id:
            try:
                stmt = session.prepare(model.recete_medica_registro_stmt)
                session.execute(stmt, [str(paciente_id), str(doc_id), None, tratamiento, uuid.uuid1()])
            except Exception as e:
                mensaje += f"(Error sincronizando dbs: {e})"
        else:
            mensaje += " (No sincronizado: Doctor no encontrado)"
    else:
        mensaje += " (No sincronizado: Se requiere nombre del doctor)"

    return mensaje