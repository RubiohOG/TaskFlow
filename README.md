# TaskFlow - Gestor de Tareas Colaborativo

TaskFlow es una aplicación web desarrollada con **Flask** para la gestión colaborativa de proyectos y tareas, con una interfaz moderna, soporte para adjuntos, comentarios, perfiles de usuario y modo claro/oscuro.

Creada con el objetivo de facilitar la gestión de proyectos y tareas entre alumnos de distintas nacionalidades, esta aplicación responde a las dificultades que pueden surgir al utilizar otros tipos de software universitario, ya sea por barreras idiomáticas o por interfaces poco intuitivas. Además, su diseño sencillo y accesible la hace perfectamente aplicable en empresas de cualquier sector que deseen gestionar sus proyectos de manera eficiente y con una interfaz fácil de usar.

---

## Características principales

- **Gestión de usuarios:** Registro, login seguro, edición de perfil, cambio de contraseña, subida de foto de perfil.
- **Roles:** Soporte para roles de usuario y administrador.
- **Proyectos:** Creación y gestión de proyectos, asignación de miembros.
- **Tareas:** Creación, asignación, edición y seguimiento de tareas con prioridades y fechas límite.
- **Comentarios:** Añade comentarios a las tareas.
- **Archivos adjuntos:** Sube y gestiona archivos en las tareas.
- **Interfaz Kanban:** Visualización de tareas por estado (Todo, En progreso, Completado).
- **Modo claro/oscuro:** Conmutador de tema persistente.
- **UI moderna:** Bootstrap 5, FontAwesome, toasts y modals para una experiencia fluida.
- **Organización modular:** Uso de Blueprints para separar la lógica de autenticación, proyectos, tareas, etc.

---

## Tecnologías utilizadas

- **Backend:** Flask, Flask-WTF, WTForms, Flask-Login, Sirope, Redis, Werkzeug.
- **Frontend:** Bootstrap 5, Jinja2, JavaScript, FontAwesome.
- **Almacenamiento:** Redis (a través de Sirope) usando serialización Pickle.
- **Gestión de sesiones:** Flask-Login.
- **Organización:** Blueprints de Flask para modularidad y escalabilidad.

---

## Guía de Funcionalidades de Taskflow

### 1. **Registro y Acceso de Usuarios**
- **Registro:**  
  Los nuevos usuarios pueden crear una cuenta proporcionando un nombre de usuario, correo electrónico y contraseña. El sistema valida que el nombre y el correo no estén ya registrados.
- **Inicio de sesión:**  
  Los usuarios registrados pueden acceder introduciendo su nombre de usuario y contraseña. Existe la opción de recordar la sesión.

### 2. **Gestión y Configuración del Perfil**
- **Edición de perfil:**  
  Cada usuario puede acceder a su perfil para modificar su correo electrónico, empresa (opcional) y cambiar su foto de perfil.  
- **Cambio de contraseña:**  
  Desde la misma sección de perfil, el usuario puede actualizar su contraseña de forma segura.
- **Foto de perfil:**  
  Se puede subir una imagen personalizada, que se mostrará en la barra superior y en los comentarios.

### 3. **Creación y Gestión de Proyectos**
- **Crear proyecto:**  
  Los usuarios pueden crear nuevos proyectos, asignándoles un título y una descripción.
- **Gestión de miembros:**  
  El creador del proyecto puede añadir o eliminar miembros, permitiendo la colaboración entre varios usuarios.
- **Edición y eliminación:**  
  Los proyectos pueden ser editados o eliminados por su propietario.

### 4. **Gestión de Tareas**
- **Crear tarea:**  
  Dentro de cada proyecto, se pueden crear tareas especificando título, descripción, prioridad, estado y fecha de vencimiento.
- **Asignación:**  
  Las tareas pueden ser asignadas a cualquier miembro del proyecto.
- **Edición y actualización:**  
  Se pueden modificar los detalles de la tarea, cambiar su estado (por ejemplo, de “En progreso” a “Hecho”) y actualizar la información relevante.
- **Eliminación:**  
  Las tareas pueden ser eliminadas si ya no son necesarias.

### 5. **Comentarios y Colaboración**
- **Añadir comentarios:**  
  Los usuarios pueden comentar en cada tarea para facilitar la comunicación y el seguimiento del trabajo.
- **Visualización:**  
  Los comentarios muestran la foto y el nombre del usuario que los escribió, junto con la fecha y hora.

### 6. **Gestión de Archivos Adjuntos**
- **Subir archivos:**  
  Es posible adjuntar archivos a cada tarea, permitiendo compartir documentos, imágenes u otros recursos relevantes.
- **Descargar y eliminar:**  
  Los archivos pueden ser descargados por los miembros del proyecto o eliminados si ya no son necesarios.

---

## Instalación

### Requisitos previos

- Python 3.6 o superior
- pip (gestor de paquetes de Python)
- Redis Server (local o remoto)

### Pasos para la instalación

1. **Clona el repositorio:**
   ```sh
   git clone <url-del-repositorio>
   cd Taskflow
   ```

2. **Crea un entorno virtual e instala dependencias:**
   ```sh
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Asegúrate de tener Redis en funcionamiento:**
   - Windows: Descarga desde https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt-get install redis-server`
   - macOS: `brew install redis`

4. **Configura las variables de entorno (opcional):**
   Crea un archivo `.env` o usa `env.example` como plantilla:
   ```
   SECRET_KEY=tu_clave_secreta
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=tu_contraseña_redis  # si es necesario
   ```

5. **Inicializa el sistema (opcional):**
   ```sh
   python setup.py
   ```

6. **Ejecuta la aplicación:**
   ```sh
   python run.py
   ```

7. **Abre en el navegador:**
   ```
   http://localhost:5000
   ```

---

## Usuarios por defecto

- **Administrador:**
  - Usuario: admin
  - Contraseña: admin123

- **Usuario de prueba:**
  - Usuario: testuser
  - Contraseña: testuser123

---

## Estructura del proyecto

```
Taskflow/
├── app/
│   ├── auth/               # Blueprint de autenticación (login, registro, perfil)
│   ├── main/               # Rutas principales (dashboard, landing)
│   ├── projects/           # Blueprint de proyectos
│   ├── tasks/              # Blueprint de tareas
│   ├── static/
│   │   ├── css/            # Estilos personalizados
│   │   ├── js/             # Scripts JS personalizados
│   │   └── profile_pics/   # Imágenes de perfil de usuario
│   ├── templates/
│   │   ├── auth/           # Plantillas de autenticación
│   │   ├── projects/       # Plantillas de proyectos
│   │   ├── tasks/          # Plantillas de tareas
│   │   └── main/           # Plantillas generales
│   ├── models.py           # Modelos de datos (User, Project, Task, etc.)
│   ├── persistence.py      # Lógica de almacenamiento con Sirope/Redis
│   └── ...
├── instance/               # Configuración local (si se usa)
├── requirements.txt        # Dependencias del proyecto
├── run.py                  # Script principal para ejecutar la app
├── setup.py                # Script de inicialización/configuración
└── README.md               # Este archivo
```

---

## Notas sobre archivos y recursos

- **Imágenes de perfil:**  
  Las imágenes subidas por los usuarios se guardan en `app/static/profile_pics/`.  
  Si un usuario no sube imagen, se usa la imagen por defecto `default.png` en esa misma carpeta.

- **Archivos adjuntos:**  
  Los archivos adjuntos a tareas se almacenan en una carpeta específica dentro de `static` (puedes personalizar la ruta en la configuración).

- **Modo claro/oscuro:**  
  El usuario puede alternar entre temas y la preferencia se guarda en el navegador.

---

## Desarrollo y contribución

- El proyecto está organizado usando **Blueprints** para facilitar la escalabilidad y el mantenimiento.
- Los modelos y la lógica de persistencia están desacoplados de las vistas.
- Los formularios usan **Flask-WTF** y **WTForms** para validación y seguridad.
- La interfaz es completamente responsiva y moderna gracias a **Bootstrap 5**.

---

## Licencia

Este proyecto es educativo y puede ser adaptado  libremente para fines académicos.
