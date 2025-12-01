import pydgraph
import json
from collections import Counter, defaultdict

# 1. Medicamentos recetados juntos para una condición
def meds_recetados_juntos(client, nombre_condicion):
    """
    Identifica qué medicamentos suelen ser recetados juntos para tratar una condición específica.
    Ruta: Condicion <- para - Tratamiento - incluye -> Medicamento
    """
    import re

    # Helpers: procesar el bloque 'data' y extraer listas de medicamentos por tratamiento
    def _extract_meds_from_data(d):
        meds_list = []
        if not d:
            return meds_list
        node = d[0]
        for tratamiento in node.get('~para', []):
            meds = [m.get('nombre') for m in tratamiento.get('incluye', []) if m.get('nombre')]
            if meds:
                meds_list.append(meds)
        return meds_list

    # 1) si el input parece un UID de Dgraph (ej. '0x1'), consultamos por uid
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
            # si falla el uid lookup continuamos con otros métodos
            pass

    # 2) Búsqueda exacta por nombre (eq)
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
        # No abortamos, probamos siguiente estrategia
        pass

    # 3) Fallback: búsqueda por regexp case-insensitive sobre el nombre
    # Escapamos la entrada para evitar que caracteres especiales rompan la regex
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
        return []


# 2. Sugerir segunda opinión
def sugerir_segunda_opinion(client, paciente_id):
    """
    Sugiere especialistas que hayan tratado la misma condición del paciente,
    excluyendo a sus doctores actuales.
    """
    # Paso 1: Obtener condición del paciente y sus doctores actuales
    query = """query q($pid: string) {
      var(func: eq(id, $pid)) {
        mis_docs as ~atiende { uid }
        diagnosticado_con {
            mi_condicion as uid
        }
      }

      # Buscar doctores que NO sean mis doctores
      # Y que hayan recetado tratamientos PARA mi condición
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

    # Filtrar doctores que efectivamente tienen tratamientos asociados a esa condición
    candidatos = []
    for doc in data.get('sugerencias', []):
        if doc.get('prescribe'): # Si la lista no está vacía, es que ha tratado la condición
            candidatos.append(doc['nombre'])

    return candidatos


# 3. Detectar conflictos de tratamiento
def detectar_conflictos_tratamiento(client, paciente_id):
    """
    Detecta interacciones negativas entre medicamentos que toma el paciente
    y alergias a medicamentos recetados.
    """
    query = """query q($pid: string) {
      paciente(func: eq(id, $pid)) {
        nombre
        # 1. Medicamentos que recibe actualmente
        recibe {
          incluye {
            uid
            nombre
            # Traer interacciones conocidas de estos medicamentos
            interactua_con {
              uid
              nombre
            }
          }
        }
        # 2. Alergias registradas
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

    # Aplanar lista de medicamentos que toma el paciente
    mis_meds = []
    mis_meds_nombres = set()

    tratamientos = paciente_node.get('recibe', [])
    for t in tratamientos:
        for m in t.get('incluye', []):
            mis_meds.append(m)
            mis_meds_nombres.add(m['nombre'])

    alertas = []

    # A) Verificar Interacciones (Medicamento A vs Medicamento B)
    for med in mis_meds:
        interacciones = med.get('interactua_con', [])
        for interaccion in interacciones:
            if interaccion['nombre'] in mis_meds_nombres:
                # Evitar duplicados A-B y B-A
                alerta = f"INTERACCIÓN: {med['nombre']} <-> {interaccion['nombre']}"
                if alerta not in alertas: # Check simple
                    alertas.append(alerta)

    # B) Verificar Alergias
    alergias = [a['nombre'] for a in paciente_node.get('es_alergico', [])]
    for med_nombre in mis_meds_nombres:
        if med_nombre in alergias:
            alertas.append(f"ALERGIA: El paciente está tomando {med_nombre} y es alérgico a él.")

    return alertas if alertas else ["No se detectaron conflictos."]


# 4. Pacientes polifarmacia (muchos tratamientos/medicamentos)
def pacientes_polifarmacia(client, umbral=3):
    """
    Identifica pacientes con más de 'umbral' tratamientos activos.
    """
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
    for p in data['pacientes']:
        count = p.get('count(recibe)', 0)
        if count >= umbral:
            resultado.append({"nombre": p['nombre'], "tratamientos": count})

    return resultado


# 5. Analizar propagación de diagnóstico contagioso
def analizar_propagacion_contagiosa(client):
    """
    Encuentra pacientes en riesgo: aquellos que fueron atendidos por doctores
    que han tratado condiciones contagiosas.
    Ruta: Condicion(contagioso) <- para - Tratamiento <- prescribe - Doctor -> atiende -> Paciente
    """
    # Reescribimos la consulta en pasos claros usando variables:
    # 1) encontrar condiciones contagiosas
    # 2) desde la condición tomar los Tratamientos (~para)
    # 3) desde esos Tratamientos tomar los Doctores que los prescriben (~prescribe)
    # 4) listar los pacientes atendidos por esos doctores
    query = """query q() {
      var(func: eq(contagioso, true)) {
        cond as uid
      }

      # tratamientos que apuntan a esas condiciones
      var(func: uid(cond)) {
        ~para { trat as uid }
      }

      # doctores que prescriben esos tratamientos
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
    # Devolver lista vacía de forma segura si la clave no existe
    return data.get('pacientes_riesgo', [])


# 6. Detectar sobredosis (mismo med, múltiples doctores)
def detectar_sobredosis(client):
    """
    Identifica pacientes que reciben el MISMO medicamento prescrito por DIFERENTES doctores.
    """
    # Ajustamos la consulta para obtener, desde cada Tratamiento, los doctores
    # que lo prescriben usando la reverse-edge ~prescribe. También traemos
    # los medicamentos que incluye cada tratamiento.
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
        # Mapear Medicamento -> Set de Doctores
        med_docs_map = defaultdict(set)

        for trat in p.get('recibe', []):
            # algunos grafos podrían usar nombres distintos, aceptamos ambas claves
            docs = trat.get('recetado_por', []) or trat.get('~prescribe', [])
            meds = trat.get('incluye', [])

            nombre_doc = docs[0]['nombre'] if docs else "Desconocido"

            for m in meds:
                med_docs_map[m['nombre']].add(nombre_doc)

        # Verificar si algún medicamento tiene > 1 doctor distinto
        for med, doctores in med_docs_map.items():
            if len(doctores) > 1:
                alertas.append({
                    "paciente": p['nombre'],
                    "medicamento": med,
                    "doctores_involucrados": list(doctores)
                })

    return alertas


# 7. Red de doctores (co-tratamientos)
def analizar_red_doctor(client, doctor_id):
    """
    Detecta con qué otros doctores comparte pacientes un doctor específico.
    """
    query = """query q($did: string) {
      doctor(func: eq(id, $did)) {
        nombre
        # Pacientes que atiende
        atiende {
          nombre
          # Qué otros doctores atienden a estos pacientes (excluyendo al original se filtra en post-proceso)
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

    if data['doctor']:
        root_doc = data['doctor'][0]['nombre']
        for pac in data['doctor'][0].get('atiende', []):
            for colega in pac.get('~atiende', []):
                if colega['nombre'] != root_doc:
                    colecciones[colega['nombre']] += 1

    return dict(colecciones)


# 8 y 9. Frecuencias por Especialidad
def padecimientos_por_especialidad(client):
    """
    Top 5 padecimientos más tratados por cada especialidad.
    """
    query = """query q() {
      especialidades(func: type(Especialidad)) {
        nombre
        # Doctores de esta especialidad
        ~tiene_especialidad {
           # Tratamientos que prescriben
           prescribe {
             # Condiciones que tratan
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

        # Navegar el grafo en JSON para contar
        for doc in esp.get('~tiene_especialidad', []):
            for trat in doc.get('prescribe', []):
                for cond in trat.get('para', []):
                    condiciones_counter[cond['nombre']] += 1

        # Top 5
        reporte[esp['nombre']] = condiciones_counter.most_common(5)

    return reporte

def relacionar_doctor_tratamiento(client, doctor_uid, tratamiento_uid):
    """
    Crea la relación: Doctor --prescribe--> Tratamiento
    """
    txn = client.txn()
    try:
        data = {"uid": doctor_uid, "prescribe": [{"uid": tratamiento_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
    except Exception as e:
        print("Error relacionando doctor-tratamiento:", e)
    finally:
        txn.discard()