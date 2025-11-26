# Integración MongoDB

Instrucciones para configurar la conexión de MongoDB usada por el paquete `Mongo`.

- Variables de entorno soportadas:
  - `MONGO_URI` - URI de conexión (por defecto `mongodb://localhost:27017/`)
  - `MONGO_DB` - Nombre de la base de datos (por defecto `health_platform`)

- Uso desde Python:

```py
from Mongo import init
cfg = init.init_db(mongo_uri="mongodb://user:pass@host:27017/", mongo_db="mi_bd")
# cfg contiene client, db, doctores, pacientes, expedientes
```

- Verificación desde línea de comandos:

```powershell
python -m Mongo.init --uri "mongodb://localhost:27017/" --db "health_platform"
```

Notas:
- Los módulos de servicio (`pacientes_services.py`, `doctors_service.py`, etc.) importan las colecciones desde `Mongo.mongo`. Asegúrate de inicializar la configuración (o establecer las variables de entorno) antes de ejecutar código que use esas importaciones, para evitar que las variables de colección queden como `None` si la conexión falla al importar.
- La creación de índices es idempotente y se realiza al inicializar la conexión.
