from app import create_app
from app.models import User
from app.persistence import save_user, get_user_by_username
import os
import redis
import sys

def init_system():
    try:
        app = create_app()
        with app.app_context():
            # Ensure upload directory exists
            uploads_dir = os.path.join(os.path.dirname(app.instance_path), 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Verificar conexión a Redis
            try:
                r = redis.Redis(
                    host=app.config['REDIS_HOST'],
                    port=app.config['REDIS_PORT'],
                    password=app.config.get('REDIS_PASSWORD', None),
                    decode_responses=True
                )
                r.ping()  # Verificar que la conexión funciona
                print("Conexión a Redis establecida correctamente.")
            except redis.ConnectionError:
                print("ERROR: No se pudo conectar a Redis. Asegúrese de que el servidor Redis esté en ejecución.")
                print(f"Configuración: Host={app.config['REDIS_HOST']}, Puerto={app.config['REDIS_PORT']}")
                sys.exit(1)
            
            # Create admin user if it doesn't exist
            admin = get_user_by_username('admin')
            if admin is None:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin'
                )
                admin.set_password('admin123')
                save_user(admin)
                
                # Create a test user
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    role='user'
                )
                test_user.set_password('testuser123')
                save_user(test_user)
                
                print('Admin user created successfully!')
                print('Test user created successfully!')
            else:
                print('Admin user already exists.')
            
            print('System setup complete!')
            
    except Exception as e:
        print(f"ERROR: No se pudo inicializar el sistema: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    init_system() 