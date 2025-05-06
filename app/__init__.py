from flask import Flask, render_template
from flask_login import LoginManager
import os

# Initialize extensions
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    
    # Redis configuration
    app.config['REDIS_HOST'] = os.environ.get('REDIS_HOST', 'localhost')
    app.config['REDIS_PORT'] = int(os.environ.get('REDIS_PORT', 6379))
    app.config['REDIS_PASSWORD'] = os.environ.get('REDIS_PASSWORD', None)
    
    # File upload configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(app.instance_path), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    login_manager.init_app(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.projects import bp as projects_bp
    app.register_blueprint(projects_bp)
    
    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)
    
    # Setup loader for Flask-Login
    from app.models import User
    from app.persistence import get_user_by_id
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from flask import current_app
            current_app.logger.info(f"Intentando cargar usuario con ID: {user_id}")
            user = get_user_by_id(user_id)
            if user:
                current_app.logger.info(f"Usuario cargado correctamente: {user.username}")
            else:
                # Si no se pudo cargar, intentar buscar el usuario ignorando errores de sirope
                from app.persistence import get_sirope
                s = get_sirope()
                try:
                    # Buscar directamente en Redis
                    users = s._redis.hgetall("User")
                    for uid, _ in users.items():
                        try:
                            current_user = s.load(uid)
                            if current_user and str(current_user.id) == str(user_id):
                                current_app.logger.info(f"Usuario encontrado por búsqueda alternativa: {current_user.username}")
                                return current_user
                        except:
                            continue
                except Exception as e:
                    current_app.logger.error(f"Error en búsqueda alternativa: {str(e)}")
                
                current_app.logger.warning(f"No se encontró usuario con ID: {user_id}")
            return user
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error al cargar usuario: {str(e)}")
            return None
    
    # Cleanup Sirope instance after each request
    @app.teardown_appcontext
    def teardown_sirope(exception):
        from flask import g
        if 'sirope' in g:
            # No es necesario hacer cleanup explícito con Redis
            g.pop('sirope', None)
    
    # Limpieza inicial de la base de datos
    with app.app_context():
        from app.persistence import init_cleanup
        init_cleanup()
    
    # Páginas de error personalizadas
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    return app 