from datetime import datetime

# PIPELINE: Requerimiento 9: Edad promedio + conteo de medicamento por diagnóstico
pipeline_diagnostico_stats = [
    {
        "$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }
    },
    {"$unwind": "$paciente"},

    {"$match": {"padecimientos": "<DIAGNOSTICO>"}},

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
            "diagnostico": {"$first": "<DIAGNOSTICO>"},
            "edad_promedio": {"$avg": "$edad"},
            "veces_prescrito": {"$sum": 1}
        }
    }
]




# PIPELINE: Requerimiento 10: Buckets de edades por padecimiento
pipeline_buckets_edad = [
    {
        "$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }
    },
    {"$unwind": "$paciente"},

    {"$match": {"padecimientos": "<PADECIMIENTO>"}},

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
