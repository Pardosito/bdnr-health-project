from connect import get_mongo, get_cassandra, get_dgraph

# SERVICIOS MONGO
from Mongo.services.doctors_service import (
    registrar_doctor,
    buscar_doctor_por_nombre,
    buscar_por_especialidad
)

from Mongo.services.pacientes_service import (
    registrar_paciente,
    obtener_paciente_y_expediente,
    filtrar_pacientes,
    obtener_info_medica
)

from Mongo.services.expediente_service import (
    crear_expediente,
    agregar_padecimiento
)

from Mongo.pipelines.aggregations import (
    edad_promedio_y_meds,
    buckets_por_edad
)

# SERVICIOS CASSANDRA
from Cassandra.cassandra import (
    registro_inicio_visita,
    registro_fin_visita,
    obtener_visitas_del_dia,
    registrar_signo_vital,
    registrar_receta_por_visita,
    consultar_recetas_por_doctor,
    obtener_diagnostico_tratamiento_paciente,
    verificar_disponibilidad_doctor
)

# SERVICIOS DGRAPH
from Dgraph.queries import (
    meds_recetados_juntos,
    sugerir_segunda_opinion,
    detectar_conflictos_tratamiento,
    pacientes_polifarmacia,
    analizar_propagacion_contagiosa,
    detectar_sobredosis,
    analizar_red_doctor,
    padecimientos_por_especialidad,
)


# ======================
# SUBMENU MONGO
# ======================
def submenu_mongo():
    while True:
        print("\n=== MONDONGO  ===")
        print("1. Registrar nuevo doctor")
        print("2. Buscar doctor por nombre")
        print("3. Buscar doctor por especialidad")
        print("4. Registrar nuevo paciente")
        print("5. Crear expediente para paciente")
        print("6. Consultar paciente + expediente")
        print("7. Filtrar pacientes")
        print("8. Mostrar info médica del paciente")
        print("9. Añadir padecimiento a paciente")
        print("10. Pipeline: edad promedio + frecuencia medicamentos")
        print("11. Pipeline: buckets de edad")
        print("0. Regresar\n")

        choice = int(input("Seleccione una opción Mongo: "))

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
                nombre = input("Nombre o fragmento: ")
                print(buscar_doctor_por_nombre(nombre))

            case 3:
                esp = input("Especialidad: ")
                print(buscar_por_especialidad(esp))

            case 4:
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

            case 5:
                nombre = input("Nombre del paciente: ")
                print(crear_expediente(nombre))

            case 6:
                nombre = input("Nombre o ID: ")
                print(obtener_paciente_y_expediente(nombre))

            case 7:
                sexo = input("Sexo (ENTER para omitir): ")
                filtros = {}
                if sexo:
                    filtros["sexo"] = sexo
                print(filtrar_pacientes(filtros))

            case 8:
                nombre = input("Nombre o ID: ")
                print(obtener_info_medica(nombre))

            case 9:
                nombre = input("Nombre del paciente: ")
                pade = input("Padecimiento: ")
                print(agregar_padecimiento(nombre, pade))

            case 10:
                diag = input("Padecimiento: ")
                print(edad_promedio_y_meds(diag))

            case 11:
                diag = input("Padecimiento: ")
                print(buckets_por_edad(diag))

            case 0:
                return

            case _:
                print("Opción inválida.")



# ======================
# SUBMENU CASSANDRA
# ======================
def submenu_cassandra():
    while True:
        print("\n=== CASSANDRA ===")
        print("1. Registrar inicio de visita")
        print("2. Registrar fin de visita")
        print("3. Obtener visitas programadas por día")
        print("4. Registrar signo vital")
        print("5. Guardar receta médica")
        print("6. Consultar recetas por doctor")
        print("7. Diagnóstico + tratamiento por fecha")
        print("8. Disponibilidad del doctor")
        print("0. Regresar\n")

        choice = int(input("Seleccione opción Cassandra: "))

        match choice:
            case 1:
                paciente = input("Paciente: ")
                doctor = input("Doctor: ")
                registro_inicio_visita(paciente, doctor)

            case 2:
                paciente = input("Paciente: ")
                registro_fin_visita(paciente)

            case 3:
                fecha = input("Fecha (YYYY-MM-DD): ")
                obtener_visitas_del_dia(fecha)

            case 4:
                paciente = input("Paciente: ")
                doctor = input("Doctor: ")
                tipo = input("Tipo medición: ")
                valor = input("Valor: ")
                registrar_signo_vital(paciente, doctor, tipo, valor)

            case 5:
                paciente = input("Paciente: ")
                doctor = input("Doctor: ")
                visita_id = input("Visita ID: ")
                receta = input("Receta: ")
                registrar_receta_por_visita(paciente, doctor, visita_id, receta)

            case 6:
                doctor = input("Doctor: ")
                consultar_recetas_por_doctor(doctor)

            case 7:
                doctor = input("Doctor: ")
                paciente = input("Paciente (opcional): ")
                fecha = input("Fecha: ")
                obtener_diagnostico_tratamiento_paciente(doctor, paciente or None, fecha)

            case 8:
                doctor = input("Doctor: ")
                fecha = input("Fecha: ")
                verificar_disponibilidad_doctor(doctor, fecha)

            case 0:
                return

            case _:
                print("Opción inválida.")



# ======================
# SUBMENU DGRAPH (CORREGIDO)
# ======================
def submenu_dgraph(dgraph):
    while True:
        print("\n=== DGRAPH ===")
        print("1. Propagación contagiosa")
        print("2. Medicamentos recetados juntos")
        print("3. Sugerir segunda opinión")
        print("4. Conflictos de tratamiento")
        print("5. Analizar red de doctor")
        print("6. Pacientes con polifarmacia")
        print("7. Posibles sobredosis")
        print("8. Padecimientos por especialidad")
        print("0. Regresar\n")

        choice = int(input("Seleccione opción Dgraph: "))

        match choice:
            case 1:
                print(analizar_propagacion_contagiosa(dgraph))

            case 2:
                cond = input("Condición: ")
                print(meds_recetados_juntos(dgraph, cond))

            case 3:
                pid = input("Paciente ID: ")
                print(sugerir_segunda_opinion(dgraph, pid))

            case 4:
                pid = input("Paciente ID: ")
                print(detectar_conflictos_tratamiento(dgraph, pid))

            case 5:
                did = input("Doctor ID: ")
                print(analizar_red_doctor(dgraph, did))

            case 6:
                umbral = input("Umbral (default 3): ")
                umbral_val = int(umbral) if umbral else 3
                print(pacientes_polifarmacia(dgraph, umbral_val))

            case 7:
                print(detectar_sobredosis(dgraph))

            case 8:
                print(padecimientos_por_especialidad(dgraph))

            case 0:
                return

            case _:
                print("Opción inválida.")



# ======================
# MENU PRINCIPAL
# ======================
def main():
    print("Conectando a bases de datos...")
    mongo = get_mongo()
    cassandra = get_cassandra()
    dgraph = get_dgraph()

    while True:
        print("\n=== Plataforma de Integración de Datos de Salud ===")
        print("1. MongoDB (Mondongo)")
        print("2. Cassandra")
        print("3. Dgraph")
        print("0. Salir\n")

        choice = int(input("Seleccione una base de datos: "))

        match choice:
            case 1:
                submenu_mongo()
            case 2:
                submenu_cassandra()
            case 3:
                submenu_dgraph(dgraph)   # ✔ AQUI SE PASA DGRAPH
            case 0:
                break
            case _:
                print("Opción inválida.")


if __name__ == "__main__":
    main()
