"""
Repository package for CRM application
Data access layer using Repository Pattern
"""

from .base_repository import BaseRepository
from .contract_repository import ContractRepository
from .customer_repository import CustomerRepository
from .employee_repository import EmployeeRepository
from .event_repository import EventRepository

__all__ = [
    "BaseRepository",
    "CustomerRepository",
    "EmployeeRepository",
    "ContractRepository",
    "EventRepository",
]
