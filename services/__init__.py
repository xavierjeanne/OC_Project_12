"""
Services package for CRM application
Business logic layer
"""

from .customer import CustomerService
from .employee import EmployeeService
from .contract import ContractService
from .event import EventService

__all__ = [
    "CustomerService",
    "EmployeeService",
    "ContractService",
    "EventService",
]
