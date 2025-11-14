from connect import get_mongo, get_cassandra
from db_tests import (
    mongo_registrar_doctor,
    mongo_buscar_por_especialidad,
    mongo_registrar_paciente,
    mongo_consultar_paciente,

    cassandra_registrar_visita,
    cassandra_historial_visitas,
    cassandra_visitas_del_dia
)


def main():

    print("Conectando a bases de datos...")
    mongo = get_mongo()
    cassandra = get_cassandra()

    print("\n=== Plataforma de Integración de Datos de Salud ===")

    while True:
        print("\n--- MongoDB ---")
        print("1. Registrar nuevo doctor")
        print("2. Buscar doctor por especialidad")
        print("3. Registrar nuevo paciente")
        print("4. Consultar perfil de paciente")

        print("\n--- Cassandra ---")
        print("5. Registrar inicio/fin de visita médica")
        print("6. Consultar historial de visitas de un paciente")
        print("7. Consultar visitas programadas para un día")

        print("\n0. Salir\n")

        choice = input("Seleccione una opción: ").strip()

        #mondongo
        if choice == "1":
            if mongo:
                mongo_registrar_doctor(mongo)
            else:
                print("[ERROR] MongoDB no está conectado.")

        elif choice == "2":
            if mongo:
                mongo_buscar_por_especialidad(mongo)
            else:
                print("[ERROR] MongoDB no está conectado.")

        elif choice == "3":
            if mongo:
                mongo_registrar_paciente(mongo)
            else:
                print("[ERROR] MongoDB no está conectado.")

        elif choice == "4":
            if mongo:
                mongo_consultar_paciente(mongo)
            else:
                print("[ERROR] MongoDB no está conectado.")

        #cassandra
        elif choice == "5":
            if cassandra:
                cassandra_registrar_visita(cassandra)
            else:
                print("[ERROR] Cassandra no está conectada.")

        elif choice == "6":
            if cassandra:
                cassandra_historial_visitas(cassandra)
            else:
                print("[ERROR] Cassandra no está conectada.")

        elif choice == "7":
            if cassandra:
                cassandra_visitas_del_dia(cassandra)
            else:
                print("[ERROR] Cassandra no está conectada.")

        #salida
        elif choice == "0":
            print("Saliendo del sistema.")
            break

        else:
            print("Opción inválida. Intente de nuevo.")


if __name__ == "__main__":
    main()

