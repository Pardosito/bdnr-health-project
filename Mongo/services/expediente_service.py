from Mongo.mongo import expedientes
from Mongo.utils import get_paciente_id
from bson import ObjectId
from Cassandra.cassandra import session
from Cassandra import model
from datetime import date
from Mongo.utils import get_doctor_id
import uuid
from connect import get_dgraph
from Dgraph import dgraph as dg_utils


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
    paciente_id = ObjectId(raw_id) if not isinstance(raw_id, ObjectId) else raw_id

    exp = expedientes.find_one({"paciente_id": paciente_id})
    if not exp:
        return "El paciente no tiene expediente creado."

    expedientes.update_one(
        {"paciente_id": paciente_id},
        {"$addToSet": {"padecimientos": diagnostico}}
    )

    mensaje = f"Padecimiento agregado a paciente {nombre_paciente}."

    doc_id_str = None
    if nombre_doctor:
        doc_id = get_doctor_id(nombre_doctor)
        if doc_id:
            doc_id_str = str(doc_id)
            try:
                stmt = session.prepare(model.INSERT_DIAGNOSTICO)
                today = date.today().strftime("%Y-%m-%d")
                session.execute(stmt, [str(paciente_id), str(doc_id), None, diagnostico, today, uuid.uuid1()])
            except Exception as e:
                mensaje += f"(Error Cassandra: {e})"

    client = get_dgraph()
    if client and doc_id_str:
        try:
            pac_uid = dg_utils.obtener_uid_por_id_mongo(client, str(paciente_id))
            doc_uid = dg_utils.obtener_uid_por_id_mongo(client, doc_id_str)

            cond_uid = dg_utils.crear_condicion(client, diagnostico, contagioso=False)

            if pac_uid and cond_uid:
                dg_utils.relacionar_paciente_condicion(client, pac_uid, cond_uid)
                mensaje += " [Dgraph: Diagnóstico vinculado]"

            if doc_uid and pac_uid:
                dg_utils.relacionar_doctor_atiende(client, doc_uid, pac_uid)

        except Exception as e:
            mensaje += f" [Dgraph Error: {e}]"

    return mensaje


#agregar tratamiento
def agregar_tratamiento(nombre_paciente: str, nombre_doctor: str, tratamiento: str):
    if not tratamiento: return "Se debe ingresar un tratamiento"

    raw_id = get_paciente_id(nombre_paciente)
    if not raw_id: return "Error: Paciente no encontrado"
    paciente_id = ObjectId(raw_id) if not isinstance(raw_id, ObjectId) else raw_id

    exp = expedientes.find_one({"paciente_id": paciente_id})
    if not exp: return "El paciente no tiene expediente."

    expedientes.update_one(
        {"paciente_id": paciente_id},
        {"$addToSet": {"tratamientos": tratamiento}}
    )
    mensaje = f"Tratamiento {tratamiento} agregado."

    doc_id_str = None
    if nombre_doctor:
        doc_id = get_doctor_id(nombre_doctor)
        if doc_id:
            doc_id_str = str(doc_id)
            try:
                stmt = session.prepare(model.recete_medica_registro_stmt)
                session.execute(stmt, [str(paciente_id), str(doc_id), None, tratamiento, uuid.uuid1()])
            except Exception as e:
                mensaje += f"(Error Cassandra: {e})"

    client = get_dgraph()
    if client and doc_id_str:
        try:
            pac_uid = dg_utils.obtener_uid_por_id_mongo(client, str(paciente_id))
            doc_uid = dg_utils.obtener_uid_por_id_mongo(client, doc_id_str)

            trat_uid = dg_utils.crear_tratamiento(client, tratamiento, "Duración no especificada")

            med_uid = dg_utils.crear_medicamento(client, tratamiento, "Dosis estándar")

            if pac_uid and trat_uid:
                dg_utils.relacionar_paciente_tratamiento(client, pac_uid, trat_uid)
                dg_utils.relacionar_tratamiento_medicamento(client, trat_uid, med_uid)

            if doc_uid and trat_uid:
                dg_utils.relacionar_doctor_tratamiento(client, doc_uid, trat_uid)
                mensaje += " [Dgraph: Tratamiento vinculado]"

        except Exception as e:
            mensaje += f" [Dgraph Error: {e}]"

    return mensaje
