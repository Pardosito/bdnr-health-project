import pydgraph
import json
from collections import Counter, defaultdict

# 1. Medicamentos recetados juntos para una condición
def meds_recetados_juntos(client, nombre_condicion):
    import re

    def _extract_meds_from_data(d):
        meds_list = []
        if not d:
            return meds_list
        node = d[0]
        for tratamiento in node.get('~para', []):
            meds = [m.get('nombre') for m in tratamiento.get('incluye', []) if m.get('nombre')]
            if meds:
                meds_list.append(meds)
        for med in meds_list:
          for m in med:
            print(f"MEDICAMENTO: {m}")

    uid_match = False
    if isinstance(nombre_condicion, str) and re.match(r"^0x[0-9a-fA-F]+$", nombre_condicion.strip()):
        uid_match = True
        query_uid = """query q($uid: string) {
          data(func: uid($uid)) {
            uid
            nombre
            ~para { uid incluye { nombre } }
          }
        }"""
        try:
            res = client.txn(read_only=True).query(query_uid, variables={'$uid': nombre_condicion.strip()})
            data = json.loads(res.json)
            return _extract_meds_from_data(data.get('data'))
        except Exception:
            pass

    query_eq = """query q($cond: string) {
      data(func: eq(nombre, $cond)) {
        uid
        nombre
        ~para { uid incluye { nombre } }
      }
    }"""
    try:
        res = client.txn(read_only=True).query(query_eq, variables={'$cond': nombre_condicion})
        data = json.loads(res.json)
        meds = _extract_meds_from_data(data.get('data'))
        if meds:
            return meds
    except Exception:
        pass

    try:
        pat = '(?i)' + re.escape(nombre_condicion)
        query_re = """query q($re: string) {
          data(func: regexp(nombre, $re)) {
            uid
            nombre
            ~para { uid incluye { nombre } }
          }
        }"""
        res = client.txn(read_only=True).query(query_re, variables={'$re': pat})
        data = json.loads(res.json)
        return _extract_meds_from_data(data.get('data'))
    except Exception:
        return


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

    tratamientos = paciente_node.get('recibe', [])
    for t in tratamientos:
        for m in t.get('incluye', []):
            mis_meds.append(m)
            mis_meds_nombres.add(m['nombre'])

    alertas = []

    for med in mis_meds:
        interacciones = med.get('interactua_con', [])
        for interaccion in interacciones:
            if interaccion['nombre'] in mis_meds_nombres:
                alerta = f"INTERACCIÓN: {med['nombre']} <-> {interaccion['nombre']}"
                if alerta not in alertas:
                    alertas.append(alerta)

    alergias = [a['nombre'] for a in paciente_node.get('es_alergico', [])]
    for med_nombre in mis_meds_nombres:
        if med_nombre in alergias:
            alertas.append(f"ALERGIA: El paciente está tomando {med_nombre} y es alérgico.")

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
        med_docs_map = defaultdict(set)

        for trat in p.get('recibe', []):
            docs = trat.get('recetado_por', []) or trat.get('~prescribe', [])
            meds = trat.get('incluye', [])

            nombre_doc = docs[0]['nombre'] if docs else "Desconocido"

            for m in meds:
                med_docs_map[m['nombre']].add(nombre_doc)

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