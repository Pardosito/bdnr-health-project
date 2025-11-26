from Mongo.mongo import expedientes

def edad_promedio_y_meds(diagnostico):
    pipeline = [
        {"$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }},
        {"$unwind": "$paciente"},
        {"$unwind": "$padecimientos"},
        {"$unwind": "$tratamientos"},
        {"$match": {"padecimientos": diagnostico}},
        {"$group": {
            "_id": "$padecimientos",
            "edad_promedio": {"$avg": "$paciente.edad"},
            "frecuencia_medicamentos": {"$sum": 1}
        }}
    ]
    return list(expedientes.aggregate(pipeline))

def buckets_por_edad(diagnostico):
    pipeline = [
        {"$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }},
        {"$unwind": "$paciente"},
        {"$unwind": "$padecimientos"},
        {"$match": {"padecimientos": diagnostico}},
        {"$bucket": {
            "groupBy": "$paciente.edad",
            "boundaries": [0,18,30,45,60,150],
            "default": "Fuera de rango",
            "output": {"total": {"$sum": 1}}
        }}
    ]
    return list(expedientes.aggregate(pipeline))
