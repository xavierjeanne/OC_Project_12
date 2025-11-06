"""
Additional fixtures for coverage tests

"""

import pytest

from models import Role
from repositories import (
    CustomerRepository,
    EmployeeRepository,
    ContractRepository,
    EventRepository,
)
from services.auth import AuthService


@pytest.fixture
def coverage_session(test_db):
    """Session for coverage tests - uses roles from conftest.py"""
    yield test_db


@pytest.fixture
def coverage_roles(coverage_session):
    """Retrieve roles created in conftest.py - avoids DetachedInstanceError"""
    roles_data = {}
    for role_name in ["sales", "support", "management", "admin"]:
        role = coverage_session.query(Role).filter_by(name=role_name).first()
        if role:
            roles_data[role_name] = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
            }

    # Return a dict-like object that allows accessing both id and full role
    class RoleHelper:

        def __init__(self, session, roles_data):
            self.session = session
            self.roles_data = roles_data

        def __getitem__(self, key):
            if key not in self.roles_data:
                raise KeyError(f"Role '{key}' not found")

            # Return fresh role object from current session
            role_id = self.roles_data[key]["id"]
            return self.session.query(Role).filter(Role.id == role_id).first()

    return RoleHelper(coverage_session, roles_data)


@pytest.fixture
def customer_repo_coverage(coverage_session):
    """Repository customer pour tests de couverture"""
    return CustomerRepository(coverage_session)


@pytest.fixture
def employee_repo_coverage(coverage_session):
    """Repository employee pour tests de couverture"""
    return EmployeeRepository(coverage_session)


@pytest.fixture
def contract_repo_coverage(coverage_session):
    """Repository contract pour tests de couverture"""
    return ContractRepository(coverage_session)


@pytest.fixture
def event_repo_coverage(coverage_session):
    """Repository event pour tests de couverture"""
    return EventRepository(coverage_session)


@pytest.fixture
def auth_service_coverage():
    """Service d'authentification pour tests"""
    return AuthService()
