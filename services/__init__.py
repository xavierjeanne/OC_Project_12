"""
Services package for CRM application
Business logic layer
"""

# Import only when needed to avoid circular dependencies
# from .customer import CustomerService
# from .employee import EmployeeService
# from .contract import ContractService
# from .event import EventService

__all__ = [
    "CustomerService",
    "EmployeeService",
    "ContractService",
    "EventService",
    "AuthService",
    "JWTService",
    "AuthenticationManager",
]
