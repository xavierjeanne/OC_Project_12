from sqlalchemy import create_engine

from db.config import SQLALCHEMY_DATABASE_URL


# Crée l'engine SQLAlchemy pour PostgreSQL
def get_engine():
    return create_engine(SQLALCHEMY_DATABASE_URL, echo=True)


if __name__ == "__main__":
    engine = get_engine()
    # Test de connexion
    try:
        with engine.connect() as connection:
            print("Connexion à la base PostgreSQL réussie !")
    except Exception as e:
        print(f"Erreur de connexion : {e}")
