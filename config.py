# Configuration de la connexion PostgreSQL
# Ne pas versionner ce fichier dans git
import os

DB_CONFIG = {
    'host': os.getenv('CRM_DB_HOST', ''),
    'port': os.getenv('CRM_DB_PORT', ''),
    'database': os.getenv('CRM_DB_NAME', ''),
    'user': os.getenv('CRM_DB_USER', ''),
    'password': os.getenv('CRM_DB_PASSWORD', ''),
}

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
