from app import create_app, db
from app.models import User, Project, Task, Comment, Attachment
from flask_migrate import upgrade

def init_db():
    app = create_app()
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Admin user created successfully!')
        else:
            print('Admin user already exists.')

if __name__ == '__main__':
    init_db() 