from connect import get_mongo, get_cassandra, get_dgraph

# servicios de mondongo
from Mongo.doctores_service import (
    registrar_doctor,
    buscar_doctor,
    filtrar_por_especialidad
)

from Mongo.pacientes_service import (
    registrar_paciente,
    consultar_paciente,
    filtrar_pacientes,
    obtener_info_medica
)

from Mongo.expedientes_service import (
    crear_expediente,
    agregar_padecimiento
)

from Mongo.pipelines import (
    edad_promedio_y_meds,
    buckets_por_edad
)


def main():

    print("Conectando a bases de datos...")
    get_mongo()
    get_cassandra()
    get_dgraph()

    print("\n=== Plataforma de Integración de Datos de Salud ===")

    while True:
        print("\n--- MongoDB ---")
        print("1. Registrar nuevo doctor")
        print("2. Buscar doctor por nombre")
        print("3. Buscar doctor por especialidad")
        print("4. Registrar nuevo paciente")
        print("5. Crear expediente para paciente")
        print("6. Buscar paciente por nombre")
        print("7. Buscar pacientes por filtros")
        print("8. Mostrar alergias, padecimientos y tratamientos del paciente")
        print("9. Añadir padecimiento a expediente de un paciente")
        print("10. Pipeline — edad promedio y frecuencia de medicamentos")
        print("11. Pipeline — buckets de edad por padecimiento")

        print("\n--- Cassandra ---")
        print("12. Registrar inicio/fin de visita médica")
        print("13. Consultar historial de visitas de un paciente")
        print("14. Consultar visitas programadas para un día")
        print("15. Registrar medición de signos vitales")
        print("16. Mostrar historial de signo vital")
        print("17. Guardar receta médica")
        print("18. Consultar recetas por rango de fechas")
        print("19. Historial de accesos a expedientes")
        print("20. Diagnósticos de un doctor por fecha")
        print("21. Diagnóstico + tratamiento por fecha")
        print("22. Disponibilidad de doctor")

        print("\n--- Dgraph ---")
        print("23. Pacientes de doctor vistos por otro especialista")
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
            # mondongo
            case 1:
                print("\n--- Registrar nuevo doctor ---")
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
                nombre = input("Nombre o ID del doctor: ")
                print(buscar_doctor(nombre))

            case 3:
                print("\n--- Buscar doctor por especialidad ---")
                esp = input("Especialidad: ")
                print(filtrar_por_especialidad(esp))

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
                print("\n--- Crear expediente médico ---")
                pid = input("ID del paciente: ")
                print(crear_expediente(pid))

            case 6:
                print("\n--- Consultar paciente + expediente ---")
                nombre = input("Nombre o ID del paciente: ")
                paciente, expediente = consultar_paciente(nombre)
                print("Paciente:", paciente)
                print("Expediente:", expediente)

            case 7:
                print("\n--- Filtrar pacientes ---")
                sexo = input("Sexo (ENTER para ignorar): ")
                filtros = {}
                if sexo:
                    filtros["sexo"] = sexo
                print(filtrar_pacientes(filtros))

            case 8:
                print("\n--- Información médica del paciente ---")
                nombre = input("Nombre o ID: ")
                print(obtener_info_medica(nombre))

            case 9:
                print("\n--- Añadir padecimiento ---")
                pid = input("ID paciente: ")
                pade = input("Padecimiento: ")
                print(agregar_padecimiento(pid, pade))

            case 10:
                print("\n--- Pipeline: edad promedio + frecuencia medicamentos ---")
                diag = input("Padecimiento: ")
                print(edad_promedio_y_meds(diag))

            case 11:
                print("\n--- Pipeline: buckets de edad ---")
                diag = input("Padecimiento: ")
                print(buckets_por_edad(diag))


            # demas modulos
            case 12:
                print("Función Cassandra — registrar visita")

            case 0:
                break

            case _:
                print("Error, escoga opción válida")


if __name__ == "__main__":
    main()
