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
        {"$match": {"padecimientos": diagnostico}},

        {"$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }},
        {"$unwind": "$paciente"},

        {"$addFields": {
            "edad": {
                "$function": {
                    "body": """
                    function(fecha_nac) {
                        try {
                            if (!fecha_nac) return null;
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
            },
            "cantidad_medicamentos": {
                "$cond": {
                    "if": {"$isArray": "$tratamientos"},
                    "then": {"$size": "$tratamientos"},
                    "else": 0
                }
            }
        }},

        {"$group": {
            "_id": None,
            "diagnostico": {"$first": diagnostico},
            "edad_promedio": {"$avg": "$edad"},
            "promedio_tratamientos_por_paciente": {"$avg": "$cantidad_medicamentos"}
        }}
    ]

    return list(expedientes.aggregate(pipeline))


    # Requerimiento 10
    # Bucket de edades por diagnóstico
def buckets_por_edad(diagnostico: str):
    pipeline = [
        {"$match": {"padecimientos": diagnostico}},

        {"$lookup": {
            "from": "pacientes",
            "localField": "paciente_id",
            "foreignField": "_id",
            "as": "paciente"
        }},
        {"$unwind": "$paciente"},

        {"$addFields": {
            "edad": {
                "$function": {
                    "body": """
                    function(fecha_nac) {
                        try {
                            if (!fecha_nac) return -1; // Retorna -1 si no hay fecha
                            let fn = new Date(fecha_nac);
                            let hoy = new Date();
                            let edad = hoy.getFullYear() - fn.getFullYear();
                            if (hoy.getMonth() < fn.getMonth() ||
                               (hoy.getMonth() === fn.getMonth() && hoy.getDate() < fn.getDate())) {
                                edad--;
                            }
                            return edad;
                        } catch(e) { return -1; }
                    }
                    """,
                    "args": ["$paciente.fecha_nac"],
                    "lang": "js"
                }
            }
        }},

        {"$match": {"edad": {"$gte": 0}}},

        {"$bucket": {
            "groupBy": "$edad",
            "boundaries": [0, 18, 30, 45, 60, 150],
            "default": "Otros",
            "output": {"total": {"$sum": 1}}
        }}
    ]

    return list(expedientes.aggregate(pipeline))