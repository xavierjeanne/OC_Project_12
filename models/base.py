"""
Base configuration for SQLAlchemy models
"""

from sqlalchemy.orm import declarative_base, sessionmaker
from db.config import engine

# Base class for all models
Base = declarative_base()

# Session factory
Session = sessionmaker(bind=engine)


def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(engine)
    print("All tables created successfully.")
