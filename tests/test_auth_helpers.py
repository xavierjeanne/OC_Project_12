"""
Test helpers for authentication system
Utilities to create test employees with proper authentication
"""

from services.auth import AuthService
from models import Session


def create_test_employee_with_auth(employee_data, password="TestPassword123!"):
    """
    Create a test employee using AuthService for proper authentication

    Args:
        employee_data: Dict with name, email, role_id
        password: Password for the employee (default secure password)

    Returns:
        Employee data dict from AuthService
    """
    session = Session()
    try:
        auth_service = AuthService()

        # Use AuthService to create employee with password
        return auth_service.create_employee_with_password(
            name=employee_data["name"],
            email=employee_data["email"],
            role_id=employee_data["role_id"],
            password=password
        )
    finally:
        session.close()


def get_employee_by_id(employee_id):
    """Get employee by ID for tests"""
    from repositories.employee import EmployeeRepository

    session = Session()
    try:
        employee_repo = EmployeeRepository(session)
        return employee_repo.get_by_id(employee_id)
    finally:
        session.close()
