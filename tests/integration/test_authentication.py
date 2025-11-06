"""
Tests for authentication system
Tests password hashing, login attempts, user creation, etc.
Migré vers SQLite in-memory pour des performances optimales
"""

import pytest

from models import Employee, Role
from services.auth import AuthService


@pytest.fixture
def auth_session(test_db):
    """Setup session for auth tests - roles are already created at session level"""
    return test_db


@pytest.fixture
def auth_service():
    """Create AuthService instance"""
    return AuthService()


@pytest.fixture
def test_roles(auth_session):
    """Get test roles - returns fresh objects attached to current session"""
    roles_data = {}
    roles = auth_session.query(Role).all()

    # Store role IDs instead of objects to avoid DetachedInstanceError
    for role in roles:
        roles_data[role.name] = {
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

    return RoleHelper(auth_session, roles_data)


class TestAuthService:
    """Test AuthService functionality"""

    def test_password_hashing(self, auth_service):
        """Test that password hashing works correctly"""
        password = "TestPassword123!"

        # Test hashing
        hashed = auth_service.hash_password(password)

        assert hashed is not None
        assert hashed != password  # Should be different from original
        assert len(hashed) > 50  # Argon2 hashes are long
        assert hashed.startswith("$argon2")  # Argon2 format

    def test_password_verification(self, auth_service):
        """Test password verification"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"

        hashed = auth_service.hash_password(password)

        # Correct password should verify
        assert auth_service.verify_password(hashed, password)

        # Wrong password should not verify
        assert not auth_service.verify_password(hashed, wrong_password)

    def test_create_employee_with_password(
        self, auth_service, test_roles, auth_session
    ):
        """Test creating employee with password"""
        employee_data = auth_service.create_employee_with_password(
            name="Test User",
            email="test@example.com",
            role_id=test_roles["sales"].id,
            password="SecurePass123!",
        )

        # Check returned data
        assert employee_data["name"] == "Test User"
        assert employee_data["email"] == "test@example.com"
        assert employee_data["role_id"] == test_roles["sales"].id
        assert employee_data["employee_number"].startswith("EMP")

        # Verify employee was created in database
        employee = (
            auth_session.query(Employee)
            .filter_by(employee_number=employee_data["employee_number"])
            .first()
        )

        assert employee is not None
        assert employee.password_hash is not None
        assert employee.password_hash != "SecurePass123!"  # Should be hashed

    def test_employee_number_generation(self, auth_service, test_roles, auth_session):
        """Test auto-generation of employee numbers"""
        # Clear existing employees first
        auth_session.query(Employee).delete()
        auth_session.commit()

        # Create first employee
        emp1 = auth_service.create_employee_with_password(
            name="Employee 1",
            email="emp1@example.com",
            role_id=test_roles["sales"].id,
            password="TestPassword123!",
        )

        # Create second employee
        emp2 = auth_service.create_employee_with_password(
            name="Employee 2",
            email="emp2@example.com",
            role_id=test_roles["support"].id,
            password="TestPassword123!",
        )

        # Check sequential numbering
        assert emp1["employee_number"] == "EMP001"
        assert emp2["employee_number"] == "EMP002"

    def test_authenticate_user_success(self, auth_service, test_roles, auth_session):
        """Test successful user authentication"""
        password = "AuthTestPassword123!"

        # Create test user
        employee_data = auth_service.create_employee_with_password(
            name="Auth Test User",
            email="authtest@example.com",
            role_id=test_roles["sales"].id,
            password=password,
        )

        # Test authentication
        success, employee, message = auth_service.authenticate_user(
            employee_data["employee_number"], password
        )

        assert success is True
        assert employee is not None

        # Check employee data through fresh session to avoid detached instance
        fresh_employee = (
            auth_session.query(Employee)
            .filter_by(employee_number=employee_data["employee_number"])
            .first()
        )
        assert fresh_employee.name == "Auth Test User"

        assert "successful" in message.lower()

    def test_authenticate_user_wrong_password(self, auth_service, test_roles):
        """Test authentication with wrong password"""
        # Create test user
        employee_data = auth_service.create_employee_with_password(
            name="Wrong Pass Test",
            email="wrongpass@example.com",
            role_id=test_roles["sales"].id,
            password="CorrectPassword123!",
        )

        # Test with wrong password
        success, employee, message = auth_service.authenticate_user(
            employee_data["employee_number"], "WrongPassword123!"
        )

        assert success is False
        assert employee is None
        assert (
            "invalid password" in message.lower()
            or "attempts remaining" in message.lower()
        )

    def test_authenticate_nonexistent_user(self, auth_service):
        """Test authentication with non-existent user"""
        success, employee, message = auth_service.authenticate_user(
            "EMP999", "AnyPasswordTest123!"
        )

        assert success is False
        assert employee is None
        assert "invalid employee number" in message.lower()

    def test_login_attempts_locking(self, auth_service, test_roles):
        """Test that account locks after failed attempts"""
        # Create test user
        employee_data = auth_service.create_employee_with_password(
            name="Lock Test User",
            email="locktest@example.com",
            role_id=test_roles["sales"].id,
            password="CorrectPassword123!",
        )

        employee_number = employee_data["employee_number"]

        # Make 5 failed attempts (should lock on 5th)
        for i in range(5):
            success, employee, message = auth_service.authenticate_user(
                employee_number, "WrongPasswordTest123!"
            )
            assert success is False

        # 6th attempt should show account locked
        success, employee, message = auth_service.authenticate_user(
            employee_number, "WrongPasswordTest123!"
        )

        assert success is False
        assert "locked" in message.lower()

        # Even correct password should fail when locked
        success, employee, message = auth_service.authenticate_user(
            employee_number, "CorrectPassword123!"
        )

        assert success is False
        assert "locked" in message.lower()

    def test_successful_login_resets_attempts(
        self, auth_service, test_roles, auth_session
    ):
        """Test that successful login resets failed attempts"""
        # Create test user
        employee_data = auth_service.create_employee_with_password(
            name="Reset Test User",
            email="resettest@example.com",
            role_id=test_roles["sales"].id,
            password="ResetPassword123!",
        )

        employee_number = employee_data["employee_number"]

        # Make 2 failed attempts
        for i in range(2):
            auth_service.authenticate_user(employee_number, "WrongPasswordTest123!")

        # Successful login should reset counter
        success, employee, message = auth_service.authenticate_user(
            employee_number, "ResetPassword123!"
        )

        assert success is True

        # Check that failed attempts were reset
        employee = (
            auth_session.query(Employee)
            .filter_by(employee_number=employee_number)
            .first()
        )

        assert employee.failed_login_attempts == 0
        assert employee.last_login is not None


class TestEmployeeModel:
    """Test Employee model authentication methods"""

    def test_employee_generate_number(self, auth_session):
        """Test static employee number generation"""
        # Should start with EMP001 when no employees exist
        auth_session.query(Employee).delete()
        auth_session.commit()

        number = Employee.generate_employee_number(auth_session)
        assert number == "EMP001"
