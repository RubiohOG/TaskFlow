from app import create_app
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

app = create_app()

if __name__ == '__main__':
    # debug_mode = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    debug_mode = False
    app.run(debug=debug_mode)