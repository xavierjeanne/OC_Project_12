"""
Models package - Import all models for easy access
"""

# Import base first
from models.base import Base, Session, init_db

# Import all models
from models.role import Role
from models.employee import Employee
from models.customer import Customer
from models.contract import Contract
from models.event import Event

# Make all models available at package level
__all__ = [
    "Base",
    "Session",
    "init_db",
    "Role",
    "Employee",
    "Customer",
    "Contract",
    "Event",
]
