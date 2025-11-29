from datetime import datetime
from bson import ObjectId

#requerimiento 9
def diagnostico_stats(db, diagnostico):
    pipeline = [
        {
            "$lookup": {
                "from": "pacientes",
                "localField": "paciente_id",
                "foreignField": "_id",
                "as": "paciente"
            }
        },
        {"$unwind": "$paciente"},

        {"$match": {"padecimientos": diagnostico}},

        {
            "$addFields": {
                "edad": {
                    "$dateDiff": {
                        "startDate": {"$dateFromString": {"dateString": "$paciente.fecha_nac"}},
                        "endDate": datetime.utcnow(),
                        "unit": "year"
                    }
                }
            }
        },

        {"$unwind": "$tratamientos"},

        {
            "$group": {
                "_id": "$tratamientos",
                "diagnostico": {"$first": diagnostico},
                "edad_promedio": {"$avg": "$edad"},
                "veces_prescrito": {"$sum": 1}
            }
        }
    ]

    return list(db.expedientes.aggregate(pipeline))


#requerimiento 10
def bucket_edades_por_padecimiento(db, padecimiento):
    pipeline = [
        {
            "$lookup": {
                "from": "pacientes",
                "localField": "paciente_id",
                "foreignField": "_id",
                "as": "paciente"
            }
        },
        {"$unwind": "$paciente"},

        {"$match": {"padecimientos": padecimiento}},

        {
            "$addFields": {
                "edad": {
                    "$dateDiff": {
                        "startDate": {"$dateFromString": {"dateString": "$paciente.fecha_nac"}},
                        "endDate": datetime.utcnow(),
                        "unit": "year"
                    }
                }
            }
        },

        {
            "$bucket": {
                "groupBy": "$edad",
                "boundaries": [0, 18, 30, 45, 60, 200],
                "default": "unknown",
                "output": {
                    "conteo_pacientes": {"$sum": 1},
                    "nombres": {"$push": "$paciente.nombre"}
                }
            }
        }
    ]

    return list(db.expedientes.aggregate(pipeline))
