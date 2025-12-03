from connect import get_mongo, get_cassandra, get_dgraph

#servicios mondongo
from Mongo.services.doctors_service import (
    registrar_doctor,
    buscar_doctor_por_id,
    buscar_doctor_por_nombre,
    buscar_por_especialidad
)

from Mongo.services.pacientes_service import (
    registrar_paciente,
    buscar_paciente_por_id,
    buscar_paciente_por_nombre,
    obtener_paciente_y_expediente,
    filtrar_pacientes,
    obtener_info_medica
)

from Mongo.services.expediente_service import (
    crear_expediente,
    obtener_expediente,
    agregar_alergia,
    agregar_padecimiento,
    agregar_tratamiento
)

from Mongo.pipelines.aggregations import (
    edad_promedio_y_meds,
    buckets_por_edad
)

# servicios cassandra
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

#servicios dgraph
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


def main():

    print("Conectando a bases de datos...")
    mongo = get_mongo()
    cassandra = get_cassandra()
    dgraph = get_dgraph()

    print("\n=== Plataforma de Integración de Datos de Salud ===")

    while True:

        #menu mondon
        print("\n--- MONDONGO ---")
        print("1. Registrar nuevo doctor")
        print("2. Buscar doctor por nombre")
        print("3. Buscar doctor por especialidad")
        print("4. Registrar nuevo paciente")
        print("5. Crear expediente para paciente")
        print("6. Consultar paciente + expediente")
        print("7. Filtrar pacientes")
        print("8. Mostrar info médica del paciente")
        print("9. Añadir padecimiento a paciente")
        print("10. Pipeline — edad promedio + frecuencia medicamentos")
        print("11. Pipeline — buckets de edad")

        #menu cassandra
        print("\n--- Cassandra ---")
        print("12. Registrar inicio/fin de visita médica")
        print("13. Consultar historial de visitas")
        print("14. Consultar visitas programadas por día")
        print("15. Registrar signo vital")
        print("16. Historial de signo vital")
        print("17. Guardar receta médica")
        print("18. Consultar recetas por rango")
        print("19. Historial de accesos")
        print("20. Diagnósticos emitidos por doctor en fecha")
        print("21. Diagnóstico + tratamiento por fecha")
        print("22. Disponibilidad del doctor")

        #menu dgraph
        print("\n--- Dgraph ---")
        print("23. Pacientes de un doctor que vio otro especialista")
        print("24. Medicamentos recetados juntos")
        print("25. Sugerir especialista para segunda opinión")
        print("26. Detectar conflictos de tratamiento")
        print("27. Analizar red de un doctor")
        print("28. Ruta de tratamiento de un paciente")
        print("29. Pacientes con muchos medicamentos")
        print("30. Posibles sobredosis")
        print("31. Referencias entre doctores")
        print("32. Frecuencia de tratamientos por especialidad")
        print("33. Padecimientos más comunes por especialidad")

        print("\n0. Salir\n")

        choice = int(input("Seleccione una opción: "))

        match choice:

            #Mondongo
            case 1:
                print("\n--- Registrar nuevo doctor (MongoDB) ---")
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
                print("\n--- Buscar doctor por nombre ---")
                nombre = input("Nombre o fragmento: ")
                print(buscar_doctor_por_nombre(nombre))

            case 3:
                esp = input("Especialidad: ")
                print(buscar_por_especialidad(esp))

            case 4:
                print("\n--- Registrar nuevo paciente ---")
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
                pid = input("ID del paciente: ")
                print(crear_expediente(pid))

            case 6:
                nombre = input("Nombre o ID: ")
                print(obtener_paciente_y_expediente(nombre))

            case 7:
                print("\n--- Filtrar pacientes ---")
                sexo = input("Sexo (ENTER para omitir): ")
                filtros = {}
                if sexo:
                    filtros["sexo"] = sexo
                print(filtrar_pacientes(filtros))

            case 8:
                nombre = input("Nombre o ID: ")
                print(obtener_info_medica(nombre))

            case 9:
                pid = input("ID del paciente: ")
                pade = input("Padecimiento: ")
                print(agregar_padecimiento(pid, pade))

            case 10:
                diag = input("Padecimiento: ")
                print(edad_promedio_y_meds(diag))

            case 11:
                diag = input("Padecimiento: ")
                print(buckets_por_edad(diag))

            #cassandra
            case 12:
                print("\n--- Registrar inicio de visita ---")
                paciente_nombre = input("Nombre del paciente: ")
                doctor_nombre = input("Nombre del doctor: ")
                registro_inicio_visita(paciente_nombre, doctor_nombre)

            case 13:
                print("\n--- Registrar fin de visita ---")
                paciente_nombre = input("Nombre del paciente: ")
                registro_fin_visita(paciente_nombre)

            case 14:
                fecha = input("Fecha: ")
                obtener_visitas_del_dia(fecha)

            case 15:
                paciente_nombre = input("Paciente: ")
                doctor_nombre = input("Doctor: ")
                tipo = input("Tipo medición: ")
                valor = input("Valor: ")
                registrar_signo_vital(paciente_nombre, doctor_nombre, tipo, valor)

            case 16:
                print("Funcionalidad no implementada.")

            case 17:
                paciente_nombre = input("Paciente: ")
                doctor_nombre = input("Doctor: ")
                visita_id = input("Visita ID: ")
                receta = input("Receta: ")
                registrar_receta_por_visita(paciente_nombre, doctor_nombre, visita_id, receta)

            case 18:
                doctor_nombre = input("Doctor: ")
                consultar_recetas_por_doctor(doctor_nombre)

            case 19:
                print("Funcionalidad no implementada.")

            case 20:
                doctor_nombre = input("Doctor: ")
                paciente_nombre = input("Paciente (opcional): ")
                fecha = input("Fecha (YYYY-MM-DD): ")
                obtener_diagnostico_tratamiento_paciente(
                    doctor_nombre, paciente_nombre or None, fecha
                )

            case 21:
                doctor_nombre = input("Doctor: ")
                paciente_nombre = input("Paciente: ")
                fecha = input("Fecha: ")
                obtener_diagnostico_tratamiento_paciente(
                    doctor_nombre, paciente_nombre, fecha
                )

            case 22:
                doctor_nombre = input("Doctor: ")
                fecha = input("Fecha: ")
                verificar_disponibilidad_doctor(doctor_nombre, fecha)


            #Dgraph
            case 23:
                print(analizar_propagacion_contagiosa(dgraph))

            case 24:
                cond = input("Condición: ")
                print(meds_recetados_juntos(dgraph, cond))

            case 25:
                pid = input("Paciente ID: ")
                print(sugerir_segunda_opinion(dgraph, pid))

            case 26:
                pid = input("Paciente ID: ")
                print(detectar_conflictos_tratamiento(dgraph, pid))

            case 27:
                did = input("Doctor ID: ")
                print(analizar_red_doctor(dgraph, did))

            case 28:
                pid = input("Paciente ID: ")
                print("Función no implementada — mostrando conflictos:")
                print(detectar_conflictos_tratamiento(dgraph, pid))

            case 29:
                umbral = input("Umbral (default 3): ")
                umbral_val = int(umbral) if umbral else 3
                print(pacientes_polifarmacia(dgraph, umbral_val))

            case 30:
                print(detectar_sobredosis(dgraph))

            case 31:
                did = input("Doctor ID: ")
                print(analizar_red_doctor(dgraph, did))

            case 32:
                print(padecimientos_por_especialidad(dgraph))

            case 33:
                print(padecimientos_por_especialidad(dgraph))

            #salir
            case 0:
                break

            case _:
                print("Opción inválida.")


if __name__ == "__main__":
    main()
