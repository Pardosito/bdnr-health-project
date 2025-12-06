from connect import get_mongo, get_cassandra, get_dgraph

from Mongo.services.doctors_service import (
    registrar_doctor, buscar_doctor_por_nombre, buscar_por_especialidad
)
from Mongo.services.pacientes_service import (
    registrar_paciente, obtener_paciente_y_expediente, filtrar_pacientes, obtener_info_medica, buscar_paciente_por_nombre
)
from Mongo.services.expediente_service import (
    crear_expediente, agregar_padecimiento, agregar_tratamiento
)
from Mongo.pipelines.aggregations import (
    edad_promedio_y_meds, buckets_por_edad
)
from Mongo.utils import get_paciente_id, get_doctor_id

from Cassandra.cassandra import (
    registro_inicio_visita, registro_fin_visita, obtener_visitas_del_dia,
    registrar_signo_vital, registrar_receta_por_visita, consultar_recetas_por_doctor,
    obtener_diagnostico_tratamiento_paciente, verificar_disponibilidad_doctor,
    registrar_diagnostico_por_visita
)

from Dgraph.queries import (
    meds_recetados_juntos, sugerir_segunda_opinion, detectar_conflictos_tratamiento,
    pacientes_polifarmacia, analizar_propagacion_contagiosa, detectar_sobredosis,
    analizar_red_doctor, padecimientos_por_especialidad,
)


def submenu_admin():
    while True:
        print("\n--- GESTIÓN ADMINISTRATIVA Y REGISTROS ---")
        print("1. Registrar nuevo Doctor")
        print("2. Registrar nuevo Paciente")
        print("3. Crear Expediente a Paciente existente")
        print("4. Buscar Doctor (por nombre)")
        print("5. Buscar Doctor (por especialidad)")
        print("6. Filtrar Pacientes (Búsqueda avanzada)")
        print("7. Buscar Paciente")
        print("0. Regresar al menú principal")

        try:
            choice = int(input("\nSeleccione una opción: "))
        except ValueError:
            print("Entrada inválida.")
            continue

        match choice:
            case 1:
                data = {
                    "nombre": input("Nombre: "),
                    "especialidad": input("Especialidad: "),
                    "subespecialidad": input("Subespecialidad: "),
                    "cedula": input("Cédula: "),
                    "telefono": input("Teléfono: "),
                    "correo": input("Correo: "),
                    "consultorio": input("Consultorio: ")
                }
                print("ID generado:", registrar_doctor(data))

            case 2:
                data = {
                    "nombre": input("Nombre: "),
                    "fecha_nac": input("Fecha nacimiento (YYYY-MM-DD): "),
                    "sexo": input("Sexo: "),
                    "telefono": input("Teléfono: "),
                    "correo": input("Correo: "),
                    "cont_eme": input("Contacto emergencia: "),
                    "direccion": input("Dirección: "),
                    "seguro": input("Seguro: "),
                    "poliza": input("Póliza: ")
                }
                print("ID generado:", registrar_paciente(data))

            case 3:
                nombre = input("Nombre del paciente: ")
                print(crear_expediente(nombre))

            case 4:
                nombre = input("Nombre o fragmento: ")
                print(buscar_doctor_por_nombre(nombre))

            case 5:
                esp = input("Especialidad: ")
                print(buscar_por_especialidad(esp))

            case 6:
                sexo = input("Sexo (ENTER para omitir): ")
                filtros = {}
                if sexo:
                    filtros["sexo"] = sexo
                print(filtrar_pacientes(filtros))

            case 7:
                nombre = input ("Nombre: ")
                buscar_paciente_por_nombre(nombre)

            case 0:
                return
            case _:
                print("Opción no reconocida.")



def submenu_visitas():
    while True:
        print("\n--- CONTROL DE VISITAS Y AGENDA ---")
        print("1. Ver agenda del día (Citas programadas)")
        print("2. Consultar disponibilidad de Doctor")
        print("3. Registrar Check-In (Inicio de Visita)")
        print("4. Registrar Check-Out (Fin de Visita)")
        print("0. Regresar al menú principal")

        try:
            choice = int(input("\nSeleccione una opción: "))
        except ValueError:
            print("Entrada inválida.")
            continue

        match choice:
            case 1:
                fecha = input("Fecha (YYYY-MM-DD): ")
                obtener_visitas_del_dia(fecha)

            case 2:
                doctor = input("Doctor: ")
                fecha = input("Fecha a consultar (YYYY-MM-DD): ")
                verificar_disponibilidad_doctor(doctor, fecha)

            case 3:
                paciente = input("Paciente: ")
                doctor = input("Doctor: ")
                registro_inicio_visita(paciente, doctor)


            case 4:
                paciente = input("Paciente: ")
                registro_fin_visita(paciente)

            case 0:
                return
            case _:
                print("Opción no reconocida.")


def submenu_clinica(dgraph_client):
    while True:
        print("\n--- CONSULTA CLÍNICA ---")
        print("1. Ver Resumen Médico (Padecimientos)")
        print("2. Diagnosticar (Añadir Padecimiento)")
        print("3. Recetar (Añadir Tratamiento)")
        print("4. Historial de Diagnósticos por Fecha")
        print("5. Historial de Recetas emitidas por Doctor")
        print("6. Solicitar Segunda Opinión")
        print("7. Detectar Conflictos de Tratamiento")
        print("8. Registrar Signo Vital")
        print("0. Regresar al menú principal")

        try:
            choice = int(input("\nSeleccione una opción: "))
        except ValueError:
            print("Entrada inválida.")
            continue

        match choice:
            case 1:
                nombre = input("Nombre o ID del paciente: ")
                print(obtener_info_medica(nombre))

            case 2:
                nombre = input("Nombre del paciente: ")
                doc = input("Nombre del Doctor: ")
                pade = input("Diagnóstico/Padecimiento: ")
                doc_val = doc if doc.strip() else None
                print(agregar_padecimiento(nombre, pade, doc_val))

            case 3:
                nombre = input("Nombre del paciente: ")
                doc = input("Nombre del doctor: ")
                tratamiento = input("Medicamento/Tratamiento: ")
                print(agregar_tratamiento(nombre, doc, tratamiento))
                print(registrar_receta_por_visita(nombre, doc, tratamiento))

            case 4:
                doctor = input("Doctor: ")
                paciente = input("Paciente: ")
                fecha = input("Fecha (YYYY-MM-DD): ")
                obtener_diagnostico_tratamiento_paciente(doctor, paciente or None, fecha)

            case 5:
                doctor = input("Doctor: ")
                consultar_recetas_por_doctor(doctor)

            case 6:
                nombre = input("Nombre paciente: ")
                pid = get_paciente_id(nombre)
                print(sugerir_segunda_opinion(dgraph_client, pid))

            case 7:
                nombre = input("Nombre paciente: ")
                pid = get_paciente_id(nombre)
                print(detectar_conflictos_tratamiento(dgraph_client, pid))

            case 8:
                paciente = input("Paciente: ")
                doctor = input("Doctor: ")
                tipo = input("Tipo medición (PRESION, PESO, TEMPERATURA...): ")
                valor = input("Valor: ")
                registrar_signo_vital(paciente, doctor, tipo, valor)

            case 0:
                return
            case _:
                print("Opción no reconocida.")


def submenu_analitica(dgraph_client):
    while True:
        print("\n--- ANALÍTICA E INTELIGENCIA ---")
        print("1. Análisis de Propagación Contagiosa")
        print("2. Análisis de Medicamentos Recetados Juntos")
        print("3. Análisis de Red de Doctores (Colaboración)")
        print("4. Pacientes con Polifarmacia (Riesgo)")
        print("5. Detección de posibles Sobredosis")
        print("6. Top Padecimientos por Especialidad")
        print("7. Estadística: Edad Promedio por Padecimiento")
        print("8. Estadística: Distribución de Edades (Buckets)")
        print("0. Regresar al menú principal")

        try:
            choice = int(input("\nSeleccione una opción: "))
        except ValueError:
            print("Entrada inválida.")
            continue

        match choice:
            case 1:
                print(analizar_propagacion_contagiosa(dgraph_client))

            case 2:
                cond = input("Condición a analizar: ")
                print(meds_recetados_juntos(dgraph_client, cond))

            case 3:
                nombre = input("Nombre doctor: ")
                did = get_doctor_id(nombre)
                print(analizar_red_doctor(dgraph_client, did))

            case 4:
                umbral = input("Umbral medicamentos (default 3): ")
                umbral_val = int(umbral) if umbral else 3
                print(pacientes_polifarmacia(dgraph_client, umbral_val))

            case 5:
                print(detectar_sobredosis(dgraph_client))

            case 6:
                print(padecimientos_por_especialidad(dgraph_client))

            case 7:
                diag = input("Padecimiento: ")
                print(edad_promedio_y_meds(diag))

            case 8:
                diag = input("Padecimiento: ")
                print(buckets_por_edad(diag))

            case 0:
                return
            case _:
                print("Opción no reconocida.")


def main():
    print("Inicializando sistema y conectando a bases de datos...")
    get_mongo()
    get_cassandra()
    dgraph = get_dgraph()

    while True:
        print("\n===============================================")
        print("   PLATAFORMA INTEGRAL DE SALUD   ")
        print("===============================================")
        print("1. Administración y Registros")
        print("2. Gestión de Visitas y Agenda")
        print("3. Consulta Clínica (Doctores)")
        print("4. Analítica y Reportes")
        print("0. Salir")

        try:
            choice = int(input("\nSeleccione un módulo de trabajo: "))
        except ValueError:
            print("Por favor ingrese un número.")
            continue

        match choice:
            case 1:
                submenu_admin()
            case 2:
                submenu_visitas()
            case 3:
                submenu_clinica(dgraph)
            case 4:
                submenu_analitica(dgraph)
            case 0:
                print("Cerrando sistema. ¡Hasta luego!")
                break
            case _:
                print("Opción inválida.")


if __name__ == "__main__":
    main()