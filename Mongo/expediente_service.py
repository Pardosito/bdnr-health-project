from bson import ObjectId

#crear expediente
def crear_expediente(db, data):
    return db.expedientes.insert_one(data).inserted_id


#obtener expediente
def obtener_expediente(db, paciente_id):
    try:
        paciente_id = ObjectId(paciente_id)
    except:
        return None

    return db.expedientes.find_one({"paciente_id": paciente_id})


#consultar el historial completo
def consultar_historial(db, valor):
    # Buscar paciente por nombre o ID
    try:
        obj_id = ObjectId(valor)
        paciente = db.pacientes.find_one({"_id": obj_id})
    except:
        paciente = db.pacientes.find_one({"nombre": valor})

    if not paciente:
        return None, None

    expediente = db.expedientes.find_one({"paciente_id": paciente["_id"]})
    return paciente, expediente


#añadir padecimiento crónico
def agregar_padecimiento(db, paciente_id, nuevo_padecimiento):
    try:
        obj_id = ObjectId(paciente_id)
    except:
        return None

    return db.expedientes.update_one(
        {"paciente_id": obj_id},
        {"$push": {"padecimientos": nuevo_padecimiento}}
    )
