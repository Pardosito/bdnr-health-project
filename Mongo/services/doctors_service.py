from Mongo.mongo import doctores
from bson import ObjectId

#reguistro de doctrores
def registrar_doctor(data: dict) -> str:
    """Registra un nuevo doctor y regresa su ID."""
    result = doctores.insert_one(data)
    return str(result.inserted_id)


#búsqueda de doctor por ID
def buscar_doctor_por_id(doctor_id: str):
    """Busca un doctor usando su ObjectId."""
    if not ObjectId.is_valid(doctor_id):
        return {"error": "ID inválido."}

    doc = doctores.find_one({"_id": ObjectId(doctor_id)})
    if not doc:
        return {"error": "Doctor no encontrado."}

    return print(f"NOMBRE: {doc['nombre']}, ESPECIALIDAD: {doc['especialidad']}, SUBESPECIALIDAD: {doc['subespecialidad']}, CEDULA: {doc['cedula']}, TELEFONO: {doc['telefono']}, CORREO: {doc['correo']}, CONSULTORIO: {doc['consultorio']}")

#busqueda de doctor por nombre
def buscar_doctor_por_nombre(nombre: str):
    """Búsqueda flexible por nombre (regex)."""
    doc = doctores.find_one({"nombre": {"$regex": nombre, "$options": "i"}})
    if not doc:
        return {"error": "Doctor no encontrado."}
    else:
        return print(f"NOMBRE: {doc['nombre']}, ESPECIALIDAD: {doc['especialidad']}, SUBESPECIALIDAD: {doc['subespecialidad']}, CEDULA: {doc['cedula']}, TELEFONO: {doc['telefono']}, CORREO: {doc['correo']}, CONSULTORIO: {doc['consultorio']}")

#filtrado de doctores por especialidad
def buscar_por_especialidad(especialidad: str):
    """Devuelve solo los campos relevantes para mostrar al usuario."""
    resultados = list(doctores.find(
        {"especialidad": especialidad},
    ))

    if not resultados:
        return {"mensaje": "No hay doctores con esa especialidad."}

    for doc in resultados:
        return print(f"NOMBRE: {doc['nombre']}, ESPECIALIDAD: {doc['especialidad']}, SUBESPECIALIDAD: {doc['subespecialidad']}, CEDULA: {doc['cedula']}, TELEFONO: {doc['telefono']}, CORREO: {doc['correo']}, CONSULTORIO: {doc['consultorio']}")