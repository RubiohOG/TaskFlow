# TaskFlow - Gestor de Tareas Colaborativo

Una aplicación web desarrollada con Flask para gestionar proyectos y tareas colaborativas.

## Características

- **Gestión de usuarios**: Registro, login y roles (administrador/usuario)
- **Proyectos**: Crear y gestionar proyectos con miembros del equipo
- **Tareas**: Crear, asignar y hacer seguimiento de tareas
- **Comentarios**: Añadir comentarios a las tareas
- **Archivos adjuntos**: Subir archivos a las tareas
- **Interfaz Kanban**: Visualización del flujo de trabajo de tareas (Todo, En progreso, Completado)

## Tecnologías usadas

- **Backend**: Flask, Sirope, Redis
- **Frontend**: Bootstrap 5, JavaScript, Jinja2
- **Almacenamiento**: Sirope/REDIS
- **Autenticación**: Flask-Login

## Requisitos del proyecto

Esta aplicación cumple con los requisitos especificados:
- Aplicación web con Flask
- Formularios con Jinja2
- Autenticación de usuarios con Flask-Login
- Almacenamiento con Sirope/REDIS

## Instalación

### Requisitos previos

- Python 3.6 o superior
- pip (administrador de paquetes de Python)
- Redis Server (local o remoto)

### Pasos para la instalación

1. Clonar el repositorio:
   ```
   git clone <url-del-repositorio>
   cd Taskflow
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   venv\Scripts\activate (Windows)
   source venv/bin/activate (Linux/Mac)
   pip install -r requirements.txt
   ```

3. Asegúrate de tener Redis en funcionamiento:
   - Windows: Descarga Redis para Windows desde https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt-get install redis-server`
   - macOS: `brew install redis`

4. Configurar las variables de entorno (opcional):
   ```
   # .env
   SECRET_KEY=tu_clave_secreta
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=tu_contraseña_redis  # si es necesario
   ```

5. Inicializar el sistema:
   ```
   python setup.py
   ```

6. Ejecutar la aplicación:
   ```
   python run.py
   ```

7. Abrir en el navegador:
   ```
   http://localhost:5000
   ```

## Usuarios por defecto

- **Administrador**:
  - Usuario: admin
  - Contraseña: admin123

- **Usuario de prueba**:
  - Usuario: testuser
  - Contraseña: testuser123

## Estructura del proyecto

```
Taskflow/
├── app/                    # Código principal de la aplicación
│   ├── auth/               # Autenticación y registro
│   ├── main/               # Rutas principales
│   ├── projects/           # Gestión de proyectos
│   ├── tasks/              # Gestión de tareas
│   ├── static/             # Archivos estáticos (CSS, JS)
│   ├── templates/          # Plantillas Jinja2
│   ├── __init__.py         # Inicialización de la aplicación
│   ├── models.py           # Modelos de datos
│   └── persistence.py      # Funciones de persistencia con Sirope
├── instance/               # Configuración local
├── uploads/                # Archivos subidos
├── requirements.txt        # Dependencias
├── run.py                  # Script para ejecutar la aplicación
└── setup.py                # Script para configurar la aplicación
```

## Desarrollo

### Ejecutar con modo de depuración

```
python run.py
```

### Realizar migraciones de base de datos

```
flask db init
flask db migrate -m "Mensaje de migración"
flask db upgrade
``` 