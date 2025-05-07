import sirope
import redis
import json
import os
import pickle
from flask import current_app, g
from app.models import User, Project, Task, Comment, Attachment
from datetime import datetime

# Variables globales para el seguimiento del estado
_sirope_instance = None
_deleted_project_ids = set()
_deleted_task_ids = set()  # Nuevo conjunto para tareas eliminadas

# Directorios para respaldos
_BACKUP_DIR = 'backup_projects'
_TASKS_BACKUP_DIR = 'backup_tasks'

def get_sirope():
    """Obtener o crear una instancia de Sirope y verificar conexión a Redis."""
    if 'sirope' not in g:
        try:
            # Inicializar Sirope
            g.sirope = sirope.Sirope()
            current_app.logger.info("Sirope inicializado correctamente")
            
            # Verificar conexión a Redis
            redis_client = g.sirope._redis
            redis_ping = redis_client.ping()
            current_app.logger.info(f"Conexión a Redis: {redis_ping}")
            
            # Cargar lista de elementos eliminados
            _load_deleted_projects(redis_client)
            _load_deleted_tasks(redis_client)
            
            # Nota: La restauración automática ahora se maneja en __init__.py
            # para evitar llamadas circulares
            
        except Exception as e:
            current_app.logger.error(f"ERROR DE CONEXIÓN: {str(e)}")
            raise RuntimeError(f"No se pudo conectar a Redis/Sirope: {str(e)}")
            
    return g.sirope

def _load_deleted_projects(redis_client):
    """Cargar IDs de proyectos eliminados."""
    global _deleted_project_ids
    try:
        # Intentar cargar lista de proyectos eliminados de Redis
        deleted_ids = redis_client.smembers("deleted_projects")
        if deleted_ids:
            _deleted_project_ids = {id.decode('utf-8') if isinstance(id, bytes) else id for id in deleted_ids}
            current_app.logger.info(f"Cargados {len(_deleted_project_ids)} IDs de proyectos eliminados")
    except Exception as e:
        current_app.logger.error(f"Error al cargar proyectos eliminados: {str(e)}")

def _save_deleted_project(project_id):
    """Guardar ID de proyecto eliminado en Redis."""
    try:
        # Guardar en Redis para persistencia
        s = get_sirope()
        s._redis.sadd("deleted_projects", str(project_id))
        current_app.logger.info(f"Proyecto {project_id} marcado como eliminado")
    except Exception as e:
        current_app.logger.error(f"Error al guardar proyecto eliminado: {str(e)}")

def _load_deleted_tasks(redis_client):
    """Cargar IDs de tareas eliminadas."""
    global _deleted_task_ids
    try:
        # Intentar cargar lista de tareas eliminadas de Redis
        deleted_ids = redis_client.smembers("deleted_tasks")
        if deleted_ids:
            _deleted_task_ids = {id.decode('utf-8') if isinstance(id, bytes) else id for id in deleted_ids}
            current_app.logger.info(f"Cargados {len(_deleted_task_ids)} IDs de tareas eliminadas")
    except Exception as e:
        current_app.logger.error(f"Error al cargar tareas eliminadas: {str(e)}")

def _save_deleted_task(task_id):
    """Guardar ID de tarea eliminada en Redis."""
    try:
        # Guardar en Redis para persistencia
        s = get_sirope()
        s._redis.sadd("deleted_tasks", str(task_id))
        current_app.logger.info(f"Tarea {task_id} marcada como eliminada")
    except Exception as e:
        current_app.logger.error(f"Error al guardar tarea eliminada: {str(e)}")

# Funciones de persistencia para usuarios
def save_user(user):
    """Guardar un usuario en la base de datos."""
    try:
        s = get_sirope()
        
        # Guardar directamente en Redis usando pickle
        serialized = pickle.dumps(user)
        s._redis.hset("User", str(user.id), serialized)
        current_app.logger.info(f"Usuario guardado directamente en Redis: {user.id}")
        
        return user.id
    except Exception as e:
        current_app.logger.error(f"Error al guardar usuario: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        raise

def load_object(oid):
    """Cargar un objeto por su OID, manejando diferentes formatos de ID de manera silenciosa."""
    s = get_sirope()
    try:
        # Intentar cargar directamente desde Redis
        obj_id_str = str(oid)
        
        # Intentar con diferentes clases conocidas
        for cls_name in ["Project", "Task", "User", "Comment", "Attachment"]:
            try:
                # Verificar si existe en Redis
                if s._redis.hexists(cls_name, obj_id_str):
                    # Obtener el objeto serializado
                    serialized = s._redis.hget(cls_name, obj_id_str)
                    if serialized:
                        # Deserializar el objeto
                        obj = pickle.loads(serialized)
                        current_app.logger.debug(f"Objeto {cls_name} cargado desde Redis con ID: {obj_id_str}")
                        return obj
            except Exception as e:
                current_app.logger.debug(f"Error al intentar cargar {cls_name} con ID {obj_id_str}: {str(e)}")
        
        # Si no se encontró, intentar usar Sirope como fallback
        try:
            return s.load(oid)
        except Exception as sirope_error:
            current_app.logger.debug(f"Error al cargar mediante Sirope: {str(sirope_error)}")
        
        # No se encontró el objeto
        return None
    except Exception as e:
        current_app.logger.error(f"Error general al cargar objeto con ID {oid}: {str(e)}")
        return None

def get_user_by_id(user_id):
    """Obtener un usuario por su ID."""
    s = get_sirope()
    try:
        # Intentar cargar directamente desde Redis
        obj_id_str = str(user_id)
        if s._redis.hexists("User", obj_id_str):
            # Obtener el objeto serializado
            serialized = s._redis.hget("User", obj_id_str)
            if serialized:
                # Deserializar el objeto
                obj = pickle.loads(serialized)
                current_app.logger.debug(f"Usuario cargado desde Redis con ID: {obj_id_str}")
                return obj
            
        # Si no se encontró, intentar fallback a load_object
        obj = load_object(user_id)
        if obj and isinstance(obj, User):
            return obj
        
        # No se encontró el usuario
        current_app.logger.debug(f"No se encontró el usuario con ID: {user_id}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error al buscar usuario por ID: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None

def get_user_by_username(username):
    """Obtener un usuario por su nombre de usuario."""
    s = get_sirope()
    try:
        # Obtener todas las claves de User en Redis
        user_keys = s._redis.hkeys("User")
        
        # Iterar por cada clave de usuario
        for user_id_bytes in user_keys:
            try:
                # Convertir de bytes a str si es necesario
                user_id = user_id_bytes
                if isinstance(user_id_bytes, bytes):
                    user_id = user_id_bytes.decode('utf-8')
                
                # Cargar el usuario
                serialized = s._redis.hget("User", user_id)
                if serialized:
                    user = pickle.loads(serialized)
                    # Verificar si el username coincide
                    if hasattr(user, 'username') and user.username == username:
                        return user
            except Exception as e:
                current_app.logger.debug(f"Error al procesar usuario {user_id}: {str(e)}")
                continue
        
        # Si llegamos aquí, no se encontró el usuario
        return None
    except Exception as e:
        current_app.logger.error(f"Error al buscar usuario por username: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None

def get_user_by_email(email):
    """Obtener un usuario por su email."""
    s = get_sirope()
    try:
        # Obtener todas las claves de User en Redis
        user_keys = s._redis.hkeys("User")
        
        # Iterar por cada clave de usuario
        for user_id_bytes in user_keys:
            try:
                # Convertir de bytes a str si es necesario
                user_id = user_id_bytes
                if isinstance(user_id_bytes, bytes):
                    user_id = user_id_bytes.decode('utf-8')
                
                # Cargar el usuario
                serialized = s._redis.hget("User", user_id)
                if serialized:
                    user = pickle.loads(serialized)
                    # Verificar si el email coincide
                    if hasattr(user, 'email') and user.email == email:
                        return user
            except Exception as e:
                current_app.logger.debug(f"Error al procesar usuario {user_id}: {str(e)}")
                continue
        
        # Si llegamos aquí, no se encontró el usuario
        return None
    except Exception as e:
        current_app.logger.error(f"Error al buscar usuario por email: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None

def get_all_users():
    """Obtener todos los usuarios."""
    s = get_sirope()
    try:
        users = []
        # Obtener todas las claves de User en Redis
        user_keys = s._redis.hkeys("User")
        
        # Iterar por cada clave de usuario
        for user_id_bytes in user_keys:
            try:
                # Convertir de bytes a str si es necesario
                user_id = user_id_bytes
                if isinstance(user_id_bytes, bytes):
                    user_id = user_id_bytes.decode('utf-8')
                
                # Cargar el usuario
                serialized = s._redis.hget("User", user_id)
                if serialized:
                    user = pickle.loads(serialized)
                    users.append(user)
            except Exception as e:
                current_app.logger.debug(f"Error al procesar usuario {user_id}: {str(e)}")
                continue
        
        return users
    except Exception as e:
        current_app.logger.error(f"Error al cargar todos los usuarios: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return []

# Funciones de persistencia para proyectos
def _ensure_backup_dir():
    """Asegurarse de que existe el directorio de respaldo para proyectos."""
    backup_path = os.path.join(current_app.instance_path, _BACKUP_DIR)
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    return backup_path

def _ensure_tasks_backup_dir():
    """Asegurarse de que existe el directorio de respaldo para tareas."""
    backup_path = os.path.join(current_app.instance_path, _TASKS_BACKUP_DIR)
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    return backup_path

def save_project(project):
    """Guardar un proyecto tanto en Redis como en archivo JSON de respaldo."""
    s = get_sirope()
    try:
        current_app.logger.info(f"=== GUARDANDO PROYECTO: {project.id} - {project.title} ===")
        
        # 1. GUARDAR EN REDIS
        serialized = pickle.dumps(project)
        s._redis.hset("Project", str(project.id), serialized)
        current_app.logger.info(f"Proyecto guardado en Redis: {project.id}")
        
        # 2. GUARDAR BACKUP EN JSON
        backup_path = _ensure_backup_dir()
        project_file = os.path.join(backup_path, f"{project.id}.json")
        
        # Datos para el backup JSON
        project_data = {
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'owner_id': project.owner_id,
            'created_at': project.created_at.isoformat() if hasattr(project, 'created_at') else datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'member_ids': project.member_ids if hasattr(project, 'member_ids') else []
        }
        
        # Guardar en archivo JSON
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=4)
        current_app.logger.info(f"Backup JSON guardado: {project_file}")
        
        # Eliminar de lista de eliminados si existe
        if str(project.id) in _deleted_project_ids:
            _deleted_project_ids.remove(str(project.id))
            
        current_app.logger.info(f"=== PROYECTO GUARDADO EXITOSAMENTE ===")
        return project.id
    except Exception as e:
        current_app.logger.error(f"ERROR AL GUARDAR PROYECTO: {str(e)}")
        raise

def get_project_by_id(project_id):
    """Obtener un proyecto por su ID."""
    # Verificar primero si está en la lista de eliminados
    if str(project_id) in _deleted_project_ids:
        current_app.logger.debug(f"El proyecto {project_id} está marcado como eliminado")
        return None
    
    s = get_sirope()
    try:
        # Intentar cargar directamente desde Redis
        obj_id_str = str(project_id)
        if s._redis.hexists("Project", obj_id_str):
            # Obtener el objeto serializado
            serialized = s._redis.hget("Project", obj_id_str)
            if serialized:
                # Deserializar el objeto
                obj = pickle.loads(serialized)
                current_app.logger.debug(f"Proyecto cargado desde Redis con ID: {obj_id_str}")
                return obj
            
        # Si no se encontró, intentar fallback a load_object
        obj = load_object(project_id)
        if obj and isinstance(obj, Project):
            return obj
        
        # No se encontró el proyecto
        current_app.logger.debug(f"No se encontró el proyecto con ID: {project_id}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error al buscar proyecto por ID: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None

# Funciones de diagnóstico para depuración
def list_all_projects_in_redis():
    """Función para listar todos los proyectos disponibles."""
    s = get_sirope()
    try:
        current_app.logger.info("=== LISTANDO TODOS LOS PROYECTOS ===")
        
        # 1. Intentar cargar proyectos de Redis primero
        all_projects = []
        project_ids = s._redis.hkeys("Project")
        current_app.logger.info(f"Encontrados {len(project_ids)} proyectos en Redis")
        
        # Cargar cada proyecto desde Redis
        for project_id_bytes in project_ids:
            try:
                # Convertir ID a string si es necesario
                project_id = project_id_bytes
                if isinstance(project_id_bytes, bytes):
                    project_id = project_id_bytes.decode('utf-8')
                
                # Ignorar proyectos eliminados
                if str(project_id) in _deleted_project_ids:
                    continue
                
                # Obtener datos del proyecto desde Redis
                serialized = s._redis.hget("Project", project_id)
                if serialized:
                    project = pickle.loads(serialized)
                    all_projects.append(project)
                    current_app.logger.info(f"Proyecto cargado desde Redis: {project.id} - {project.title}")
            except Exception as e:
                current_app.logger.warning(f"Error al cargar proyecto {project_id}: {str(e)}")
        
        # 2. Si no hay proyectos en Redis, cargar desde respaldos
        if not all_projects:
            current_app.logger.info("No se encontraron proyectos en Redis, cargando desde respaldos")
            
            # Cargar desde backups JSON
            backup_projects = _load_project_backups()
            for project in backup_projects:
                if str(project.id) not in _deleted_project_ids:
                    all_projects.append(project)
                    current_app.logger.info(f"Proyecto cargado desde backup: {project.id} - {project.title}")
        
        current_app.logger.info(f"Total de proyectos encontrados: {len(all_projects)}")
        return all_projects
        
    except Exception as e:
        current_app.logger.error(f"ERROR AL LISTAR PROYECTOS: {str(e)}")
        
        # Último recurso: intentar cargar solo desde backups
        try:
            backup_projects = _load_project_backups()
            current_app.logger.info(f"Recuperados {len(backup_projects)} proyectos desde backups como último recurso")
            return [p for p in backup_projects if str(p.id) not in _deleted_project_ids]
        except:
            return []

# Modificar get_projects_by_owner para utilizar la función de diagnóstico
def get_projects_by_owner(owner_id):
    """Obtener proyectos por ID del propietario."""
    try:
        current_app.logger.info(f"Buscando proyectos para el propietario: {owner_id}")
        
        # Listar todos los proyectos para diagnóstico
        all_projects = list_all_projects_in_redis()
        current_app.logger.info(f"Total de proyectos encontrados en Redis: {len(all_projects)}")
        
        # Filtrar por propietario
        owner_projects = []
        for project in all_projects:
            try:
                project_owner = getattr(project, 'owner_id', None)
                current_app.logger.debug(f"Proyecto {project.id} tiene propietario {project_owner}")
                
                if hasattr(project, 'owner_id') and project.owner_id == owner_id:
                    owner_projects.append(project)
                    current_app.logger.info(f"Proyecto coincide: ID={project.id}, Título={project.title}")
            except Exception as e:
                current_app.logger.error(f"Error al procesar proyecto en get_projects_by_owner: {str(e)}")
                continue
        
        current_app.logger.info(f"Encontrados {len(owner_projects)} proyectos para el propietario {owner_id}")
        return owner_projects
    except Exception as e:
        current_app.logger.error(f"Error al cargar proyectos por propietario: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return []

def get_projects_by_member(user_id):
    """Obtener proyectos donde un usuario es miembro."""
    try:
        # Listar todos los proyectos para diagnóstico
        all_projects = list_all_projects_in_redis()
        
        # Filtrar por miembro
        member_projects = []
        for project in all_projects:
            try:
                if hasattr(project, 'member_ids') and user_id in project.member_ids:
                    member_projects.append(project)
            except:
                continue
        
        current_app.logger.info(f"Encontrados {len(member_projects)} proyectos donde el usuario {user_id} es miembro")
        return member_projects
    except Exception as e:
        current_app.logger.error(f"Error al cargar proyectos por miembro: {str(e)}")
        return []

# Función auxiliar para eliminar objetos por ID
def delete_object_by_id(obj_id, class_type=None):
    """Eliminar un objeto por su ID de forma segura."""
    s = get_sirope()
    try:
        # Primero cargar el objeto para obtener su OID real
        obj = load_object(obj_id)
        if obj:
            # Si se especificó un tipo de clase, verificar que el objeto sea de ese tipo
            if class_type is not None and not isinstance(obj, class_type):
                current_app.logger.warning(f"El objeto con ID {obj_id} no es del tipo esperado {class_type.__name__}")
                return False
            
            # Añadir a la lista de eliminados según el tipo
            if class_type == Project:
                _deleted_project_ids.add(str(obj_id))
                _save_deleted_project(obj_id)
                current_app.logger.info(f"Añadido proyecto {obj_id} a la lista de eliminados")
            elif class_type == Task:
                _deleted_task_ids.add(str(obj_id))
                _save_deleted_task(obj_id)
                current_app.logger.info(f"Añadida tarea {obj_id} a la lista de eliminados")
            
            # Implementar eliminación usando directamente Redis
            try:
                # Obtener el tipo de clase para usar como namespace en Redis
                class_name = obj.__class__.__name__
                obj_id_str = str(obj.id)
                
                # Eliminar de los índices de Sirope (si existen)
                indexes = s._redis.smembers(f"_sirope_indexes_{class_name}")
                for idx in indexes:
                    try:
                        if isinstance(idx, bytes):
                            idx = idx.decode('utf-8')
                        s._redis.srem(f"_sirope_idx_{class_name}_{idx}_{obj_id_str}", obj_id_str)
                    except Exception as e:
                        current_app.logger.warning(f"Error al eliminar índice: {str(e)}")
                
                # Eliminar el objeto del hash principal
                result = s._redis.hdel(class_name, obj_id_str)
                
                # Eliminar también de almacenamiento suelto (por si acaso)
                s._redis.delete(f"{class_name}_{obj_id_str}")
                
                if result > 0:
                    current_app.logger.info(f"Objeto {class_name} con ID {obj_id} eliminado correctamente")
                    return True
                else:
                    current_app.logger.warning(f"El objeto {class_name} con ID {obj_id} no existía en Redis")
                    return False
            except Exception as e:
                current_app.logger.error(f"Error al eliminar objeto: {str(e)}")
                return False
        else:
            # Si no encontramos el objeto, procesarlo según el tipo
            if class_type == Project:
                _deleted_project_ids.add(str(obj_id))
                _save_deleted_project(obj_id)
                current_app.logger.info(f"Añadido proyecto {obj_id} a la lista de eliminados (no encontrado)")
                
                # Intentar eliminar directamente
                try:
                    if s._redis.hexists("Project", str(obj_id)):
                        s._redis.hdel("Project", str(obj_id))
                        return True
                except:
                    pass
            elif class_type == Task:
                _deleted_task_ids.add(str(obj_id))
                _save_deleted_task(obj_id)
                current_app.logger.info(f"Añadida tarea {obj_id} a la lista de eliminados (no encontrada)")
                
                # Intentar eliminar directamente
                try:
                    if s._redis.hexists("Task", str(obj_id)):
                        s._redis.hdel("Task", str(obj_id))
                        return True
                except:
                    pass
                
            current_app.logger.warning(f"No se encontró el objeto con ID {obj_id} para eliminar")
            return False
    except Exception as e:
        current_app.logger.error(f"Error al intentar eliminar objeto con ID {obj_id}: {str(e)}")
        
        # Último intento según el tipo
        try:
            if class_type == Project:
                _deleted_project_ids.add(str(obj_id))
                _save_deleted_project(obj_id)
                if s._redis.hexists("Project", str(obj_id)):
                    s._redis.hdel("Project", str(obj_id))
                    return True
            elif class_type == Task:
                _deleted_task_ids.add(str(obj_id))
                _save_deleted_task(obj_id)
                if s._redis.hexists("Task", str(obj_id)):
                    s._redis.hdel("Task", str(obj_id))
                    return True
        except:
            pass
            
        return False

def delete_project(project_id):
    """Eliminar un proyecto y todas sus tareas, comentarios y adjuntos."""
    # Primero cargamos el proyecto
    project = get_project_by_id(project_id)
    if not project:
        return False
    
    # Eliminar todas las tareas relacionadas
    tasks = get_tasks_by_project(project_id)
    for task in tasks:
        delete_task(task.id)
    
    # Eliminar el archivo de respaldo si existe
    try:
        backup_path = _ensure_backup_dir()
        backup_file = os.path.join(backup_path, f"{project_id}.json")
        if os.path.exists(backup_file):
            os.remove(backup_file)
            current_app.logger.info(f"Archivo de respaldo eliminado: {backup_file}")
    except Exception as e:
        current_app.logger.error(f"Error al eliminar archivo de respaldo: {str(e)}")
    
    # Finalmente, eliminar el proyecto usando nuestra función segura
    return delete_object_by_id(project_id, Project)

# Funciones de persistencia para tareas
def save_task(task):
    """Guardar una tarea tanto en Redis como en archivo JSON de respaldo."""
    s = get_sirope()
    try:
        current_app.logger.info(f"=== GUARDANDO TAREA: {task.id} - {task.title} ===")
        
        # 1. GUARDAR EN REDIS
        serialized = pickle.dumps(task)
        s._redis.hset("Task", str(task.id), serialized)
        current_app.logger.info(f"Tarea guardada en Redis: {task.id}")
        
        # 2. GUARDAR BACKUP EN JSON
        backup_path = _ensure_tasks_backup_dir()
        task_file = os.path.join(backup_path, f"{task.id}.json")
        
        # Datos para el backup JSON
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'project_id': task.project_id,
            'creator_id': task.creator_id,
            'assignee_id': task.assignee_id if hasattr(task, 'assignee_id') else None,
            'created_at': task.created_at.isoformat() if hasattr(task, 'created_at') else datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'due_date': task.due_date.isoformat() if hasattr(task, 'due_date') and task.due_date else None
        }
        
        # Guardar en archivo JSON
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=4)
        current_app.logger.info(f"Backup JSON guardado: {task_file}")
        
        # Eliminar de lista de eliminados si existe
        if str(task.id) in _deleted_task_ids:
            _deleted_task_ids.remove(str(task.id))
            
        current_app.logger.info(f"=== TAREA GUARDADA EXITOSAMENTE ===")
        return task.id
    except Exception as e:
        current_app.logger.error(f"ERROR AL GUARDAR TAREA: {str(e)}")
        raise

def get_task_by_id(task_id):
    """Obtener una tarea por su ID."""
    # Verificar primero si está en la lista de eliminados
    if str(task_id) in _deleted_task_ids:
        current_app.logger.debug(f"La tarea {task_id} está marcada como eliminada")
        return None
    
    s = get_sirope()
    try:
        # Intentar cargar directamente desde Redis
        obj_id_str = str(task_id)
        if s._redis.hexists("Task", obj_id_str):
            # Obtener el objeto serializado
            serialized = s._redis.hget("Task", obj_id_str)
            if serialized:
                # Deserializar el objeto
                obj = pickle.loads(serialized)
                current_app.logger.debug(f"Tarea cargada desde Redis con ID: {obj_id_str}")
                return obj
            
        # Si no se encontró, intentar fallback a load_object
        obj = load_object(task_id)
        if obj and isinstance(obj, Task):
            return obj
        
        # No se encontró la tarea
        current_app.logger.debug(f"No se encontró la tarea con ID: {task_id}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error al buscar tarea por ID: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None

def get_tasks_by_project(project_id):
    """Obtener tareas por ID del proyecto."""
    try:
        # Listar todas las tareas para diagnóstico
        all_tasks = list_all_tasks_in_redis()
        
        # Filtrar por proyecto
        project_tasks = []
        for task in all_tasks:
            try:
                if hasattr(task, 'project_id') and task.project_id == project_id:
                    project_tasks.append(task)
            except:
                continue
        
        current_app.logger.info(f"Encontradas {len(project_tasks)} tareas para el proyecto {project_id}")
        return project_tasks
    except Exception as e:
        current_app.logger.error(f"Error al cargar tareas por proyecto: {str(e)}")
        return []

def get_tasks_by_assignee(user_id):
    """Obtener tareas asignadas a un usuario."""
    try:
        # Listar todas las tareas para diagnóstico
        all_tasks = list_all_tasks_in_redis()
        
        # Filtrar por assignee
        assigned_tasks = []
        for task in all_tasks:
            try:
                if hasattr(task, 'assignee_id') and task.assignee_id == user_id:
                    assigned_tasks.append(task)
            except:
                continue
        
        current_app.logger.info(f"Encontradas {len(assigned_tasks)} tareas asignadas al usuario {user_id}")
        return assigned_tasks
    except Exception as e:
        current_app.logger.error(f"Error al cargar tareas por assignee: {str(e)}")
        return []

def delete_task(task_id):
    """Eliminar una tarea y todos sus comentarios y adjuntos."""
    global _deleted_task_ids
    
    # Primero cargamos la tarea
    task = get_task_by_id(task_id)
    
    # Marcar como eliminado en el seguimiento
    _deleted_task_ids.add(str(task_id))
    _save_deleted_task(task_id)
    
    # Eliminar el archivo de respaldo si existe
    try:
        backup_path = _ensure_tasks_backup_dir()
        backup_file = os.path.join(backup_path, f"{task_id}.json")
        if os.path.exists(backup_file):
            os.remove(backup_file)
            current_app.logger.info(f"Archivo de respaldo de tarea eliminado: {backup_file}")
    except Exception as e:
        current_app.logger.error(f"Error al eliminar archivo de respaldo de tarea: {str(e)}")
    
    if not task:
        current_app.logger.warning(f"No se encontró el objeto con ID {task_id} para eliminar")
        
        # Intentar eliminar directamente de Redis si existe
        try:
            s = get_sirope()
            if s._redis.hexists("Task", task_id):
                s._redis.hdel("Task", task_id)
                current_app.logger.info(f"Tarea {task_id} eliminada directamente de Redis")
                return True
        except Exception as e:
            current_app.logger.error(f"Error al eliminar tarea directamente de Redis: {str(e)}")
            
        return False
    
    # Eliminar comentarios
    comments = get_comments_by_task(task_id)
    for comment in comments:
        delete_object_by_id(comment.id, Comment)
    
    # Eliminar adjuntos
    attachments = get_attachments_by_task(task_id)
    for attachment in attachments:
        delete_object_by_id(attachment.id, Attachment)
    
    # Finalmente, eliminar la tarea
    success = delete_object_by_id(task_id, Task)
    
    # Intentar eliminar directamente de Redis si existe
    try:
        s = get_sirope()
        if s._redis.hexists("Task", task_id):
            s._redis.hdel("Task", task_id)
            success = True
            current_app.logger.info(f"Tarea {task_id} eliminada directamente de Redis como respaldo")
    except Exception as e:
        current_app.logger.error(f"Error al eliminar tarea directamente de Redis: {str(e)}")
    
    return success

# Funciones de persistencia para comentarios
def save_comment(comment):
    """Guardar un comentario en la base de datos."""
    s = get_sirope()
    oid = s.save(comment)
    return oid

def get_comments_by_task(task_id):
    """Obtener comentarios por ID de la tarea."""
    s = get_sirope()
    comments = list(s.filter(Comment, lambda c: c.task_id == task_id))
    # Ordenar comentarios por fecha de creación
    comments.sort(key=lambda c: c.created_at)
    return comments

# Funciones de persistencia para adjuntos
def save_attachment(attachment):
    """Guardar un adjunto en la base de datos (Redis)."""
    s = get_sirope()
    try:
        serialized = pickle.dumps(attachment)
        s._redis.hset("Attachment", str(attachment.id), serialized)
        return attachment.id
    except Exception as e:
        current_app.logger.error(f"Error al guardar adjunto: {str(e)}")
        return None

def get_attachments_by_task(task_id):
    """Obtener adjuntos por ID de la tarea (filtrado manual desde Redis)."""
    s = get_sirope()
    task_id_str = str(task_id)
    attachments = []
    for k in s._redis.hkeys('Attachment'):
        a = pickle.loads(s._redis.hget('Attachment', k))
        if str(a.task_id) == task_id_str:
            attachments.append(a)
    return attachments

# Funciones auxiliares para contar relaciones
def count_project_tasks(project_id):
    """Contar cuántas tareas tiene un proyecto."""
    tasks = get_tasks_by_project(project_id)
    return len(tasks) if tasks else 0

def count_project_members(project_id):
    """Contar cuántos miembros tiene un proyecto."""
    project = get_project_by_id(project_id)
    if project and hasattr(project, 'member_ids'):
        return len(project.member_ids)
    return 0

def get_project_owner(project_id):
    """Obtener el usuario propietario de un proyecto."""
    project = get_project_by_id(project_id)
    if project and project.owner_id:
        return get_user_by_id(project.owner_id)
    return None

# Funciones de mantenimiento y limpieza
def cleanup_corrupted_projects():
    """Limpia proyectos corruptos o parcialmente eliminados de Redis."""
    s = get_sirope()
    try:
        # Obtener todas las claves en Redis que sean proyectos
        project_data = s._redis.hgetall("Project")
        
        cleaned = 0
        for project_id, data in project_data.items():
            try:
                # Convertir a str si es bytes
                if isinstance(project_id, bytes):
                    project_id = project_id.decode('utf-8')
                
                # Intentar cargar y verificar el proyecto
                project = None
                try:
                    project = s.load(project_id)
                except Exception:
                    # Si hay error al cargar, considerarlo corrupto
                    current_app.logger.warning(f"Error al cargar proyecto {project_id}, marcando como eliminado")
                    _deleted_project_ids.add(str(project_id))
                    _save_deleted_project(project_id)
                    delete_object_by_id(project_id, Project)
                    cleaned += 1
                    continue
                
                # Si no tiene atributos básicos, considerarlo corrupto
                if not project or not hasattr(project, 'id') or not hasattr(project, 'title'):
                    current_app.logger.warning(f"Proyecto {project_id} corrupto, marcando como eliminado")
                    _deleted_project_ids.add(str(project_id))
                    _save_deleted_project(project_id)
                    delete_object_by_id(project_id, Project)
                    cleaned += 1
            except Exception as e:
                current_app.logger.error(f"Error al procesar proyecto {project_id}: {str(e)}")
                # Aún así intentamos eliminarlo
                try:
                    _deleted_project_ids.add(str(project_id))
                    _save_deleted_project(project_id)
                    s._redis.hdel("Project", project_id)
                    cleaned += 1
                except:
                    pass
        
        current_app.logger.info(f"Limpieza completada: {cleaned} proyectos corruptos eliminados")
        return cleaned
    except Exception as e:
        current_app.logger.error(f"Error durante la limpieza de proyectos: {str(e)}")
        return 0

def cleanup_corrupted_tasks():
    """Limpia tareas corruptas o parcialmente eliminadas de Redis."""
    s = get_sirope()
    try:
        # Obtener todas las claves en Redis que sean tareas
        task_data = s._redis.hgetall("Task")
        
        cleaned = 0
        for task_id, data in task_data.items():
            try:
                # Convertir a str si es bytes
                if isinstance(task_id, bytes):
                    task_id = task_id.decode('utf-8')
                
                # Intentar cargar y verificar la tarea
                task = None
                try:
                    task = s.load(task_id)
                except Exception:
                    # Si hay error al cargar, considerarla corrupta
                    current_app.logger.warning(f"Error al cargar tarea {task_id}, marcando como eliminada")
                    _deleted_task_ids.add(str(task_id))
                    _save_deleted_task(task_id)
                    delete_object_by_id(task_id, Task)
                    cleaned += 1
                    continue
                
                # Si no tiene atributos básicos, considerarla corrupta
                if not task or not hasattr(task, 'id') or not hasattr(task, 'title'):
                    current_app.logger.warning(f"Tarea {task_id} corrupta, marcando como eliminada")
                    _deleted_task_ids.add(str(task_id))
                    _save_deleted_task(task_id)
                    delete_object_by_id(task_id, Task)
                    cleaned += 1
            except Exception as e:
                current_app.logger.error(f"Error al procesar tarea {task_id}: {str(e)}")
                # Aún así intentamos eliminarla
                try:
                    _deleted_task_ids.add(str(task_id))
                    _save_deleted_task(task_id)
                    s._redis.hdel("Task", task_id)
                    cleaned += 1
                except:
                    pass
        
        current_app.logger.info(f"Limpieza completada: {cleaned} tareas corruptas eliminadas")
        return cleaned
    except Exception as e:
        current_app.logger.error(f"Error durante la limpieza de tareas: {str(e)}")
        return 0

def force_delete_marked_projects():
    """Asegurar que todos los proyectos marcados como eliminados se han eliminado físicamente."""
    s = get_sirope()
    try:
        count = 0
        for project_id in list(_deleted_project_ids):
            # Comprobar si aún existe en Redis
            if s._redis.hexists("Project", project_id):
                # Eliminar físicamente
                s._redis.hdel("Project", project_id)
                # Eliminar índices asociados
                indexes = s._redis.smembers(f"_sirope_indexes_Project")
                for idx in indexes:
                    s._redis.srem(f"_sirope_idx_Project_{idx}_{project_id}", project_id)
                count += 1
        current_app.logger.info(f"Forzada eliminación de {count} proyectos marcados como eliminados")
    except Exception as e:
        current_app.logger.error(f"Error al forzar eliminación de proyectos: {str(e)}")

def force_delete_marked_tasks():
    """Asegurar que todas las tareas marcadas como eliminadas se han eliminado físicamente."""
    s = get_sirope()
    try:
        count = 0
        for task_id in list(_deleted_task_ids):
            # Comprobar si aún existe en Redis
            if s._redis.hexists("Task", task_id):
                # Eliminar físicamente
                s._redis.hdel("Task", task_id)
                # Eliminar índices asociados
                indexes = s._redis.smembers(f"_sirope_indexes_Task")
                for idx in indexes:
                    s._redis.srem(f"_sirope_idx_Task_{idx}_{task_id}", task_id)
                count += 1
        current_app.logger.info(f"Forzada eliminación de {count} tareas marcadas como eliminadas")
    except Exception as e:
        current_app.logger.error(f"Error al forzar eliminación de tareas: {str(e)}")

def _load_project_backups():
    """Cargar proyectos desde los archivos de respaldo."""
    projects = []
    try:
        backup_path = _ensure_backup_dir()
        
        # Listar archivos JSON en el directorio
        backup_files = os.listdir(backup_path)
        current_app.logger.info(f"Encontrados {len(backup_files)} archivos de respaldo de proyectos en {backup_path}")
        
        for filename in backup_files:
            if filename.endswith('.json'):
                try:
                    file_path = os.path.join(backup_path, filename)
                    current_app.logger.info(f"Intentando cargar proyecto desde archivo: {file_path}")
                    
                    with open(os.path.join(backup_path, filename), 'r') as f:
                        project_data = json.load(f)
                        
                        # Verificar si este proyecto está en la lista de eliminados
                        project_id = project_data.get('id')
                        if project_id is None:
                            current_app.logger.warning(f"Archivo de respaldo {filename} no contiene ID de proyecto válido")
                            continue
                            
                        if str(project_id) in _deleted_project_ids:
                            current_app.logger.info(f"Proyecto {project_id} está en la lista de eliminados, se omite")
                            continue
                        
                        # Crear objeto Project desde los datos
                        project = Project(
                            title=project_data.get('title', 'Sin título'),
                            description=project_data.get('description', ''),
                            owner_id=project_data.get('owner_id')
                        )
                        
                        # Establecer el ID original
                        project.id = project_data.get('id')
                        
                        # Establecer miembros si existen
                        if 'member_ids' in project_data:
                            project.member_ids = project_data.get('member_ids', [])
                        
                        # Intentar convertir fechas
                        try:
                            if 'created_at' in project_data:
                                project.created_at = datetime.fromisoformat(project_data.get('created_at'))
                            if 'updated_at' in project_data:
                                project.updated_at = datetime.fromisoformat(project_data.get('updated_at'))
                        except:
                            pass
                        
                        projects.append(project)
                        current_app.logger.info(f"Proyecto cargado desde respaldo: ID={project.id}, Título={project.title}")
                except Exception as e:
                    current_app.logger.error(f"Error al cargar proyecto de respaldo {filename}: {str(e)}")
                    import traceback
                    current_app.logger.error(traceback.format_exc())
        
        current_app.logger.info(f"Total de proyectos cargados desde respaldos: {len(projects)}")
    except Exception as e:
        current_app.logger.error(f"Error al cargar proyectos de respaldo: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
    
    return projects

def _load_task_backups():
    """Cargar tareas desde los archivos de respaldo."""
    tasks = []
    try:
        backup_path = _ensure_tasks_backup_dir()
        for filename in os.listdir(backup_path):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(backup_path, filename), 'r') as f:
                        task_data = json.load(f)
                        
                        # Verificar si esta tarea está en la lista de eliminados
                        if str(task_data.get('id')) in _deleted_task_ids:
                            continue
                        
                        # Crear objeto Task desde los datos
                        task = Task(
                            title=task_data.get('title', 'Sin título'),
                            description=task_data.get('description', ''),
                            status=task_data.get('status', 'todo'),
                            priority=task_data.get('priority', 'medium'),
                            project_id=task_data.get('project_id'),
                            creator_id=task_data.get('creator_id')
                        )
                        
                        # Establecer el ID original
                        task.id = task_data.get('id')
                        
                        # Establecer assignee_id si existe
                        if task_data.get('assignee_id'):
                            task.assignee_id = task_data.get('assignee_id')
                        
                        # Intentar convertir fechas
                        try:
                            if task_data.get('created_at'):
                                task.created_at = datetime.fromisoformat(task_data.get('created_at'))
                            if task_data.get('updated_at'):
                                task.updated_at = datetime.fromisoformat(task_data.get('updated_at'))
                            if task_data.get('due_date'):
                                task.due_date = datetime.fromisoformat(task_data.get('due_date'))
                        except:
                            pass
                        
                        tasks.append(task)
                        current_app.logger.info(f"Tarea cargada desde respaldo: ID={task.id}, Título={task.title}")
                except Exception as e:
                    current_app.logger.error(f"Error al cargar tarea de respaldo {filename}: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"Error al cargar tareas de respaldo: {str(e)}")
    
    return tasks

# Llamar a la función de limpieza al iniciar la aplicación
def init_cleanup():
    """Realizar limpieza inicial al arrancar la aplicación."""
    try:
        s = get_sirope()
        
        # FORZAR CARGA DE TODOS LOS RESPALDOS SIN EXCEPCIÓN
        current_app.logger.info("==== RESTAURACIÓN FORZADA DE PROYECTOS ====")
        
        # RESTAURAR PROYECTOS DESDE JSON
        backup_projects = _load_project_backups()
        projects_restored = 0
        
        for project in backup_projects:
            try:
                # GUARDAR PROYECTO DIRECTAMENTE EN REDIS
                serialized = pickle.dumps(project)
                s._redis.hset("Project", str(project.id), serialized)
                current_app.logger.info(f"Proyecto restaurado en Redis: {project.id} - {project.title}")
                projects_restored += 1
            except Exception as e:
                current_app.logger.error(f"Error al restaurar proyecto {project.id}: {str(e)}")
        
        current_app.logger.info(f"Total: {projects_restored} proyectos restaurados exitosamente")
        
        # RESTAURAR TAREAS DESDE JSON
        current_app.logger.info("==== RESTAURACIÓN FORZADA DE TAREAS ====")
        backup_tasks = _load_task_backups()
        tasks_restored = 0
        
        for task in backup_tasks:
            try:
                # GUARDAR TAREA DIRECTAMENTE EN REDIS
                serialized = pickle.dumps(task)
                s._redis.hset("Task", str(task.id), serialized)
                current_app.logger.info(f"Tarea restaurada en Redis: {task.id} - {task.title}")
                tasks_restored += 1
            except Exception as e:
                current_app.logger.error(f"Error al restaurar tarea {task.id}: {str(e)}")
        
        current_app.logger.info(f"Total: {tasks_restored} tareas restauradas exitosamente")
        
    except Exception as e:
        current_app.logger.error(f"Error en restauración: {str(e)}")

def list_all_tasks_in_redis():
    """Función para listar todas las tareas disponibles."""
    s = get_sirope()
    try:
        current_app.logger.info("=== LISTANDO TODAS LAS TAREAS ===")
        
        # 1. Intentar cargar tareas de Redis primero
        all_tasks = []
        task_ids = s._redis.hkeys("Task")
        current_app.logger.info(f"Encontradas {len(task_ids)} tareas en Redis")
        
        # Cargar cada tarea desde Redis
        for task_id_bytes in task_ids:
            try:
                # Convertir ID a string si es necesario
                task_id = task_id_bytes
                if isinstance(task_id_bytes, bytes):
                    task_id = task_id_bytes.decode('utf-8')
                
                # Ignorar tareas eliminadas
                if str(task_id) in _deleted_task_ids:
                    continue
                
                # Obtener datos de la tarea desde Redis
                serialized = s._redis.hget("Task", task_id)
                if serialized:
                    task = pickle.loads(serialized)
                    all_tasks.append(task)
                    current_app.logger.info(f"Tarea cargada desde Redis: {task.id} - {task.title}")
            except Exception as e:
                current_app.logger.warning(f"Error al cargar tarea {task_id}: {str(e)}")
        
        # 2. Si no hay tareas en Redis, cargar desde respaldos
        if not all_tasks:
            current_app.logger.info("No se encontraron tareas en Redis, cargando desde respaldos")
            
            # Cargar desde backups JSON
            backup_tasks = _load_task_backups()
            for task in backup_tasks:
                if str(task.id) not in _deleted_task_ids:
                    all_tasks.append(task)
                    current_app.logger.info(f"Tarea cargada desde backup: {task.id} - {task.title}")
        
        current_app.logger.info(f"Total de tareas encontradas: {len(all_tasks)}")
        return all_tasks
        
    except Exception as e:
        current_app.logger.error(f"ERROR AL LISTAR TAREAS: {str(e)}")
        
        # Último recurso: intentar cargar solo desde backups
        try:
            backup_tasks = _load_task_backups()
            current_app.logger.info(f"Recuperadas {len(backup_tasks)} tareas desde backups como último recurso")
            return [t for t in backup_tasks if str(t.id) not in _deleted_task_ids]
        except:
            return []

def get_attachment_by_id(attachment_id):
    """Obtener un adjunto por su ID."""
    s = get_sirope()
    try:
        return s.load(attachment_id)
    except Exception:
        return None 