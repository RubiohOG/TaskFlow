from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import uuid

class User(UserMixin):
    def __init__(self, username, email, password=None, role='user'):
        self.id = str(uuid.uuid4())  # Usar UUID como identificador único
        self.username = username
        self.email = email
        self.password_hash = None if password is None else generate_password_hash(password)
        self.role = role
        self.created_at = datetime.utcnow()
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)

class Project:
    def __init__(self, title, description, owner_id):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.owner_id = owner_id
        # Referencias a otros objetos
        self.member_ids = []  # Lista de IDs de usuarios miembros
        
    # Método para facilitar acceso a miembros del proyecto mediante almacenamiento
    def add_member(self, user_id):
        if user_id not in self.member_ids:
            self.member_ids.append(user_id)
    
    def remove_member(self, user_id):
        if user_id in self.member_ids:
            self.member_ids.remove(user_id)
    
    # Métodos adicionales para simular el comportamiento de ORM
    class TasksCollection:
        def __init__(self, project_id):
            self.project_id = project_id
        
        def count(self):
            # Importar aquí para evitar importaciones circulares
            from app.persistence import count_project_tasks
            return count_project_tasks(self.project_id)
    
    class MembersCollection:
        def __init__(self, project_id):
            self.project_id = project_id
        
        def count(self):
            # Importar aquí para evitar importaciones circulares
            from app.persistence import count_project_members
            return count_project_members(self.project_id)
    
    @property
    def tasks(self):
        return self.TasksCollection(self.id)
    
    @property
    def members(self):
        return self.MembersCollection(self.id)
    
    @property
    def owner(self):
        # Importar aquí para evitar importaciones circulares
        from app.persistence import get_user_by_id
        return get_user_by_id(self.owner_id)

class Task:
    def __init__(self, title, description, project_id, creator_id, status='todo', 
                 priority='medium', assignee_id=None, due_date=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.status = status  # todo, in_progress, done
        self.priority = priority  # low, medium, high
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.project_id = project_id
        self.creator_id = creator_id
        self.assignee_id = assignee_id
        self.due_date = due_date
    
    @property
    def project(self):
        # Importar aquí para evitar importaciones circulares
        from app.persistence import get_project_by_id
        return get_project_by_id(self.project_id)
    
    @property
    def creator(self):
        # Importar aquí para evitar importaciones circulares
        from app.persistence import get_user_by_id
        return get_user_by_id(self.creator_id)
    
    @property
    def assignee(self):
        # Importar aquí para evitar importaciones circulares
        from app.persistence import get_user_by_id
        return get_user_by_id(self.assignee_id) if self.assignee_id else None

class Comment:
    def __init__(self, content, task_id, user_id):
        self.id = str(uuid.uuid4())
        self.content = content
        self.created_at = datetime.utcnow()
        self.task_id = task_id
        self.user_id = user_id

class Attachment:
    def __init__(self, filename, file_path, task_id, user_id):
        self.id = str(uuid.uuid4())
        self.filename = filename
        self.file_path = file_path
        self.uploaded_at = datetime.utcnow()
        self.task_id = task_id
        self.user_id = user_id 