from Mongo.mongo import expedientes
from datetime import datetime

# Utilidad interna: convertir fecha_nac a edad
def _calcular_edad(fecha_nac_str):
    try:
        fecha = datetime.strptime(fecha_nac_str, "%Y-%m-%d")
        hoy = datetime.today()
        return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
    except Exception:
        return None

# 1. Requerimiento 9
# Edad promedio + frecuencia de medicamentos
def edad_promedio_y_meds(diagnostico: str):
    pipeline = [
        # unimos expediente + paciente
        {"$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }},
        {"$unwind": "$paciente"},

        # Convertir fecha_nac a edad
        {"$addFields": {
            "edad": {
                "$function": {
                    "body": """
                    function(fecha_nac) {
                        try {
                            let fn = new Date(fecha_nac);
                            let hoy = new Date();
                            let edad = hoy.getFullYear() - fn.getFullYear();
                            if (hoy.getMonth() < fn.getMonth() ||
                               (hoy.getMonth() === fn.getMonth() && hoy.getDate() < fn.getDate())) {
                                edad--;
                            }
                            return edad;
                        } catch(e) { return null; }
                    }
                    """,
                    "args": ["$paciente.fecha_nac"],
                    "lang": "js"
                }
            }
        }},

        # separar padecimientos
        {"$unwind": "$padecimientos"},

        # solo el diasgnostico buscado
        {"$match": {"padecimientos": diagnostico}},

        # si existen multiples tratamientos los separa
        {"$unwind": {
            "path": "$tratamientos",
            "preserveNullAndEmptyArrays": True
        }},

        # agrupar
        {"$group": {
            "_id": "$padecimientos",
            "edad_promedio": {"$avg": "$edad"},
            "frecuencia_medicamentos": {"$sum": 1}
        }}
    ]

    return list(expedientes.aggregate(pipeline))


# Requerimiento 10
# Bucket de edades por diagnóstico
def buckets_por_edad(diagnostico: str):
    pipeline = [
        {"$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }},
        {"$unwind": "$paciente"},

        # convertir fecha_nac a edad
        {"$addFields": {
            "edad": {
                "$function": {
                    "body": """
                    function(fecha_nac) {
                        try {
                            let fn = new Date(fecha_nac);
                            let hoy = new Date();
                            let edad = hoy.getFullYear() - fn.getFullYear();
                            if (hoy.getMonth() < fn.getMonth() ||
                               (hoy.getMonth() === fn.getMonth() && hoy.getDate() < fn.getDate())) {
                                edad--;
                            }
                            return edad;
                        } catch(e) { return null; }
                    }
                    """,
                    "args": ["$paciente.fecha_nac"],
                    "lang": "js"
                }
            }
        }},

        {"$unwind": "$padecimientos"},

        {"$match": {"padecimientos": diagnostico}},

        # bucke ice challenge
        {"$bucket": {
            "groupBy": "$edad",
            "boundaries": [0, 18, 30, 45, 60, 150],
            "default": "Fuera de rango",
            "output": {"total": {"$sum": 1}}
        }}
    ]

    return list(expedientes.aggregate(pipeline))
