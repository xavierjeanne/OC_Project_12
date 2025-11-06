"""
Centralized configuration of PostgreSQL test fixtures
Tests run against the same type of database as production
"""
import os
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models.base import Base
import models

# Charger les variables d'environnement
load_dotenv()

# Configuration base de données de test PostgreSQL
DB_TEST_USER = os.getenv("DB_TEST_USER", os.getenv("DB_USER"))
DB_TEST_PASSWORD = os.getenv("DB_TEST_PASSWORD", os.getenv("DB_PASSWORD"))
DB_TEST_HOST = os.getenv("DB_TEST_HOST", os.getenv("DB_HOST", "localhost"))
DB_TEST_PORT = os.getenv("DB_TEST_PORT", os.getenv("DB_PORT", "5433"))
DB_TEST_NAME = os.getenv("DB_TEST_NAME", "epic_events_test")


def get_test_database_url():
    """Build the PostgreSQL test database URL"""
    return (
        f"postgresql+psycopg2://{DB_TEST_USER}:{DB_TEST_PASSWORD}@"
        f"{DB_TEST_HOST}:{DB_TEST_PORT}/{DB_TEST_NAME}"
    )


@pytest.fixture(scope="session")
def test_engine():
    """
    PostgreSQL engine for tests - shared for the session
    Created once per test session
    """
    test_url = get_test_database_url()
    engine = create_engine(test_url, echo=False)

    # Verify the connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"PostgreSQL test database not available: {e}")

    # Create tables once for the session
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Create base roles required for tests
    from models import Role
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()

    try:
        # Create base roles if they do not exist
        existing_roles = session.query(Role).count()
        if existing_roles == 0:
            base_roles = [
                Role(
                    name="sales",
                    description="Sales team - Customer and contract management"
                ),
                Role(
                    name="support",
                    description="Support team - Event management and customer service"
                ),
                Role(name="management", description="Management - Full system access"),
                Role(name="admin",
                     description="System administrator - Full system access")
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
    PostgreSQL session for tests with automatic rollback
    Each test uses its own transaction which is rolled back
    """
    # Create a connection and start a transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session factory bound to this connection
    SessionClass = sessionmaker(bind=connection)
    session = SessionClass()

    # Patch modules that use Session
    patches = [
        patch.object(models, 'Session', lambda: session),
        patch('services.auth.Session', lambda: session),
        patch('repositories.base.Session', lambda: session),
    ]

    # Start all patches
    for p in patches:
        p.start()

    try:
        yield session
    finally:
        # Stop all patches
        for p in patches:
            p.stop()

        # Rollback the transaction (undo all changes)
        session.close()
        transaction.rollback()
        connection.close()
