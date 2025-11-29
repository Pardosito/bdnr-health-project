from bson import ObjectId

#registro de paciente
def registrar_paciente(db, data):
    return db.pacientes.insert_one(data).inserted_id


#consultar paciente
def consultar_paciente(db, valor):
    try:
        obj = ObjectId(valor)
        doc = db.pacientes.find_one({"_id": obj})
        if doc:
            return doc
    except:
        pass

    return db.pacientes.find_one({"nombre": valor})
