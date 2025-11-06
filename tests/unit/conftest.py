"""
Configuration fixture for unit tests
Unit tests with mocked database interactions
"""

import pytest
from unittest.mock import MagicMock
from models import Role


@pytest.fixture
def mock_session():
    """Mock database session for unit tests"""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.all.return_value = []
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
def mock_roles():
    """Mock roles for unit tests"""
    sales_role = MagicMock(spec=Role)
    sales_role.id = 1
    sales_role.name = "sales"
    sales_role.description = "Sales team"

    support_role = MagicMock(spec=Role)
    support_role.id = 2
    support_role.name = "support"
    support_role.description = "Support team"

    management_role = MagicMock(spec=Role)
    management_role.id = 3
    management_role.name = "management"
    management_role.description = "Management team"

    admin_role = MagicMock(spec=Role)
    admin_role.id = 4
    admin_role.name = "admin"
    admin_role.description = "Admin team"

    return {
        "sales": sales_role,
        "support": support_role,
        "management": management_role,
        "admin": admin_role,
    }


@pytest.fixture
def mock_employee_data():
    """Mock employee data"""
    return {
        "id": 1,
        "employee_number": "EMP001",
        "name": "Test User",
        "email": "test@example.com",
        "role": "sales",
        "role_id": 1,
    }


@pytest.fixture
def mock_customer_data():
    """Mock customer data"""
    return {
        "id": 1,
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "0123456789",
        "company_name": "ACME Corp",
    }
