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
    return doc if doc else {"error": "Doctor no encontrado."}


#busqueda de doctor por nombre
def buscar_doctor_por_nombre(nombre: str):
    """Búsqueda flexible por nombre (regex)."""
    doc = doctores.find_one({"nombre": {"$regex": nombre, "$options": "i"}})
    return doc if doc else {"error": "Doctor no encontrado."}


#filtrado de doctores por especialidad
def buscar_por_especialidad(especialidad: str):
    """Devuelve solo los campos relevantes para mostrar al usuario."""
    resultados = list(doctores.find(
        {"especialidad": especialidad},
        {"_id": 1, "nombre": 1, "especialidad": 1, "subespecialidad": 1,
         "correo": 1, "consultorio": 1}
    ))

    if not resultados:
        return {"mensaje": "No hay doctores con esa especialidad."}

    return resultados
