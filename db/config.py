# Chargement des variables d'environnement et configuration SQLAlchemy pour PostgreSQL
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Charger les variables d'environnement de production
load_dotenv()


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# URL de connexion PostgreSQL pour SQLAlchemy
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Créer l'engine SQLAlchemy
engine = create_engine(DATABASE_URL)


# Tester la connexion à la base de données


def test_connection():
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connexion réussie !", result.scalar())
    except Exception as e:
        print("Erreur de connexion :", e)


if __name__ == "__main__":
    test_connection()
