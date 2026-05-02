import pydgraph
import json
import re
from collections import Counter, defaultdict

_QUERY_MEDS_UID = """query q($uid: string) {
  data(func: uid($uid)) {
    uid
    nombre
    ~para { uid incluye { nombre } }
  }
}"""

_QUERY_MEDS_EQ = """query q($cond: string) {
  data(func: eq(nombre, $cond)) {
    uid
    nombre
    ~para { uid incluye { nombre } }
  }
}"""

_QUERY_MEDS_RE = """query q($re: string) {
  data(func: regexp(nombre, $re)) {
    uid
    nombre
    ~para { uid incluye { nombre } }
  }
}"""


def _extract_meds_from_data(d):
    if not d:
        return []
    meds_list = []
    for tratamiento in d[0].get('~para', []):
        meds = [m.get('nombre') for m in tratamiento.get('incluye', []) if m.get('nombre')]
        if meds:
            meds_list.append(meds)
    for med in meds_list:
        for m in med:
            print(f"MEDICAMENTO: {m}")
    return meds_list


# 1. Medicamentos recetados juntos para una condición
def meds_recetados_juntos(client, nombre_condicion):
    if isinstance(nombre_condicion, str) and re.match(r"^0x[0-9a-fA-F]+$", nombre_condicion.strip()):
        try:
            res = client.txn(read_only=True).query(_QUERY_MEDS_UID, variables={'$uid': nombre_condicion.strip()})
            return _extract_meds_from_data(json.loads(res.json).get('data'))
        except Exception:
            pass

    try:
        res = client.txn(read_only=True).query(_QUERY_MEDS_EQ, variables={'$cond': nombre_condicion})
        meds = _extract_meds_from_data(json.loads(res.json).get('data'))
        if meds:
            return meds
    except Exception:
        pass

    try:
        pat = '(?i)' + re.escape(nombre_condicion)
        res = client.txn(read_only=True).query(_QUERY_MEDS_RE, variables={'$re': pat})
        return _extract_meds_from_data(json.loads(res.json).get('data'))
    except Exception:
        return None


# 2. Sugerir segunda opinión
def sugerir_segunda_opinion(client, paciente_id):
    query = """query q($pid: string) {
      var(func: eq(id, $pid)) {
        mis_docs as ~atiende { uid }
        diagnosticado_con {
            mi_condicion as uid
        }
      }

      sugerencias(func: type(Doctor)) @filter(not uid(mis_docs)) {
        nombre
        especialidad
        prescribe {
           para @filter(uid(mi_condicion)) {
             uid
           }
        }
      }
    }"""

    variables = {'$pid': str(paciente_id)}
    res = client.txn(read_only=True).query(query, variables=variables)
    data = json.loads(res.json)

    candidatos = []
    for doc in data.get('sugerencias', []):
        if doc.get('prescribe'):
            candidatos.append(doc['nombre'])

    for candidato in candidatos:
      print(f"DOCTOR: {candidato}")


def _detectar_interacciones(mis_meds, mis_meds_nombres):
    alertas = []
    for med in mis_meds:
        for interaccion in med.get('interactua_con', []):
            if interaccion['nombre'] in mis_meds_nombres:
                alerta = f"INTERACCIÓN: {med['nombre']} <-> {interaccion['nombre']}"
                if alerta not in alertas:
                    alertas.append(alerta)
    return alertas


def _detectar_alergias(mis_meds_nombres, alergias):
    return [
        f"ALERGIA: El paciente está tomando {med} y es alérgico."
        for med in mis_meds_nombres
        if med in alergias
    ]


# 3. Detectar conflictos de tratamiento
def detectar_conflictos_tratamiento(client, paciente_id):
    query = """query q($pid: string) {
      paciente(func: eq(id, $pid)) {
        nombre
        recibe {
          incluye {
            uid
            nombre
            interactua_con {
              uid
              nombre
            }
          }
        }
        es_alergico {
          uid
          nombre
        }
      }
    }"""

    variables = {'$pid': str(paciente_id)}
    res = client.txn(read_only=True).query(query, variables=variables)
    data = json.loads(res.json)

    if not data['paciente']:
        return "Paciente no encontrado"

    paciente_node = data['paciente'][0]

    mis_meds = []
    mis_meds_nombres = set()
    for t in paciente_node.get('recibe', []):
        for m in t.get('incluye', []):
            mis_meds.append(m)
            mis_meds_nombres.add(m['nombre'])

    alergias = [a['nombre'] for a in paciente_node.get('es_alergico', [])]
    alertas = _detectar_interacciones(mis_meds, mis_meds_nombres)
    alertas += _detectar_alergias(mis_meds_nombres, alergias)

    if not alertas:
        return "No se detectaron conflictos."

    for alerta in alertas:
        print(alerta)


# 4. Pacientes polifarmacia (muchos tratamientos/medicamentos)
def pacientes_polifarmacia(client, umbral=3):
    query = """query q() {
      pacientes(func: type(Paciente)) {
        nombre
        id
        count(recibe)
      }
    }"""

    res = client.txn(read_only=True).query(query)
    data = json.loads(res.json)

    resultado = []
    for p in data.get("pacientes", []):
        count = p.get("count(recibe)", 0)
        if count >= umbral:
            resultado.append({"nombre": p['nombre'], "tratamientos": count})

    for item in resultado:
        print(f"PACIENTE: {item['nombre']}, TRATAMIENTOS: {item['tratamientos']}")


# 5. Analizar propagación de diagnóstico contagioso
def analizar_propagacion_contagiosa(client):
    query = """query q() {
      var(func: eq(contagioso, true)) {
        cond as uid
      }

      var(func: uid(cond)) {
        ~para { trat as uid }
      }

      var(func: uid(trat)) {
        ~prescribe { doc_riesgo as uid }
      }

      pacientes_riesgo(func: uid(doc_riesgo)) {
        nombre_doctor: nombre
        id
        pacientes_expuestos: atiende {
           nombre
           id
        }
      }
    }"""

    res = client.txn(read_only=True).query(query)
    data = json.loads(res.json)
    riesgo = data.get("pacientes_riesgo", [])
    for item in riesgo:
        print(f"DOCTOR: {item.get('nombre_doctor')}")
        pacientes = item.get("pacientes_expuestos", [])
        for paciente in pacientes:
            print(f"PACIENTE EXPUESTO: {paciente['nombre']}")


def _analizar_meds_por_doctor(tratamientos):
    med_docs_map = defaultdict(set)
    for trat in tratamientos:
        docs = trat.get('recetado_por', []) or trat.get('~prescribe', [])
        nombre_doc = docs[0]['nombre'] if docs else "Desconocido"
        for m in trat.get('incluye', []):
            med_docs_map[m['nombre']].add(nombre_doc)
    return med_docs_map


# 6. Detectar sobredosis (mismo med, múltiples doctores)
def detectar_sobredosis(client):
    query = """query q() {
      pacientes(func: type(Paciente)) {
        nombre
        recibe {
          incluye { nombre }
          # reverse edge: desde Tratamiento hacia Doctor
          ~prescribe { nombre }
        }
      }
    }"""

    res = client.txn(read_only=True).query(query)
    data = json.loads(res.json)

    alertas = []
    for p in data.get('pacientes', []):
        med_docs_map = _analizar_meds_por_doctor(p.get('recibe', []))
        for med, doctores in med_docs_map.items():
            if len(doctores) > 1:
                alertas.append({
                    "paciente": p['nombre'],
                    "medicamento": med,
                    "doctores_involucrados": list(doctores)
                })

    for alerta in alertas:
      print(f"PACIENTE: {alerta['paciente']}, MEDICAMENTO: {alerta['medicamento']}, DOCTORES: {alerta['doctores_involucrados']}")


# 7. Red de doctores (co-tratamientos)
def analizar_red_doctor(client, doctor_id):
    query = """query q($did: string) {
      doctor(func: eq(id, $did)) {
        nombre
        atiende {
          nombre
          ~atiende {
             nombre
             id
             especialidad
          }
        }
      }
    }"""

    variables = {'$did': str(doctor_id)}
    res = client.txn(read_only=True).query(query, variables=variables)
    data = json.loads(res.json)

    colecciones = Counter()

    if data.get('doctor'):
        root_doc = data['doctor'][0]['nombre']
        for pac in data['doctor'][0].get('atiende', []):
            for colega in pac.get('~atiende', []):
                if colega['nombre'] != root_doc:
                    colecciones[colega['nombre']] += 1

    for doctor, cantidad in colecciones.items():
        print(f"DOCTOR: {doctor}, PACIENTES: {cantidad}")



# 8 y 9. Frecuencias por Especialidad
def padecimientos_por_especialidad(client):
    query = """query q() {
      especialidades(func: type(Especialidad)) {
        nombre
        ~tiene_especialidad {
           prescribe {
             para {
               nombre
             }
           }
        }
      }
    }"""

    res = client.txn(read_only=True).query(query)
    data = json.loads(res.json)

    reporte = {}

    for esp in data['especialidades']:
        condiciones_counter = Counter()

        for doc in esp.get('~tiene_especialidad', []):
            for trat in doc.get('prescribe', []):
                for cond in trat.get('para', []):
                    condiciones_counter[cond['nombre']] += 1

        reporte[esp['nombre']] = condiciones_counter.most_common(5)

    for especialidad, count in reporte.items():
      print(f"ESPECIALIDAD: {especialidad}, TOTAL: {count}")

def relacionar_doctor_tratamiento(client, doctor_uid, tratamiento_uid):
    txn = client.txn()
    try:
        data = {"uid": doctor_uid, "prescribe": [{"uid": tratamiento_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
    except Exception as e:
        print("Error relacionando doctor-tratamiento:", e)
    finally:
        txn.discard()
