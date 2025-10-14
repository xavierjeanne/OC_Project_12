"""
Repository package for CRM application
Data access layer using Repository Pattern
"""

from .base import BaseRepository
from .contract import ContractRepository
from .customer import CustomerRepository
from .employee import EmployeeRepository
from .event import EventRepository

__all__ = [
    "BaseRepository",
    "CustomerRepository",
    "EmployeeRepository",
    "ContractRepository",
    "EventRepository",
]
