"""
Configuration centralisée des fixtures de test PostgreSQL
Tests avec la même base de données que la production
"""
import os
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models.base import Base
import models
import services.auth

# Charger les variables d'environnement
load_dotenv()

# Configuration base de données de test PostgreSQL
DB_TEST_USER = os.getenv("DB_TEST_USER", os.getenv("DB_USER"))
DB_TEST_PASSWORD = os.getenv("DB_TEST_PASSWORD", os.getenv("DB_PASSWORD"))
DB_TEST_HOST = os.getenv("DB_TEST_HOST", os.getenv("DB_HOST", "localhost"))
DB_TEST_PORT = os.getenv("DB_TEST_PORT", os.getenv("DB_PORT", "5433"))
DB_TEST_NAME = os.getenv("DB_TEST_NAME", "epic_events_test")


def get_test_database_url():
    """Construire l'URL de la base de données de test PostgreSQL"""
    return (
        f"postgresql+psycopg2://{DB_TEST_USER}:{DB_TEST_PASSWORD}@"
        f"{DB_TEST_HOST}:{DB_TEST_PORT}/{DB_TEST_NAME}"
    )


@pytest.fixture(scope="session")
def test_engine():
    """
    Engine PostgreSQL pour tests - partagé pour la session
    Créé une fois par session de test
    """
    test_url = get_test_database_url()
    engine = create_engine(test_url, echo=False)
    
    # Vérifier la connexion
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"PostgreSQL test database not available: {e}")
    
    # Créer les tables une fois pour la session
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # Créer les rôles de base nécessaires pour les tests
    from models import Role
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    
    try:
        # Créer les rôles de base s'ils n'existent pas
        existing_roles = session.query(Role).count()
        if existing_roles == 0:
            base_roles = [
                Role(name="sales", description="Sales team - Customer and contract management"),
                Role(name="support", description="Support team - Event management and customer service"), 
                Role(name="management", description="Management - Full system access"),
                Role(name="admin", description="System administrator - Full system access")
            ]
            
            for role in base_roles:
                session.add(role)
            
            session.commit()
            print(f"Created {len(base_roles)} base roles for tests")
    except Exception as e:
        session.rollback()
        print(f"Error creating base roles: {e}")
    finally:
        session.close()
    
    yield engine
    
    # Cleanup final
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """
    Session PostgreSQL pour tests avec rollback automatique
    Chaque test a sa propre transaction qui est annulée
    """
    # Créer une connexion et transaction
    connection = test_engine.connect()
    transaction = connection.begin()
    
    # Créer session factory liée à cette connexion
    SessionClass = sessionmaker(bind=connection)
    session = SessionClass()
    
    # Patcher les modules qui utilisent Session
    patches = [
        patch.object(models, 'Session', lambda: session),
        patch('services.auth.Session', lambda: session),
        patch('repositories.base.Session', lambda: session),
    ]
    
    # Démarrer tous les patches
    for p in patches:
        p.start()
    
    try:
        yield session
    finally:
        # Arrêter tous les patches
        for p in patches:
            p.stop()
        
        # Rollback de la transaction (annule tous les changements)
        session.close()
        transaction.rollback()
        connection.close()