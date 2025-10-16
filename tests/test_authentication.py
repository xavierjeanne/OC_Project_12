"""
Tests for authentication system
Tests password hashing, login attempts, user creation, etc.
"""

import pytest

from db.config import engine
from models import Base, Employee, Role, Session
from services.auth import AuthService


@pytest.fixture(scope="session", autouse=True)
def setup_auth_database():
    """Setup database for auth tests"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Create roles needed for tests
    session = Session()
    try:
        # Create test roles
        roles_data = [
            {"name": "sales", "description": "Sales team"},
            {"name": "support", "description": "Support team"},
            {"name": "management", "description": "Management team"},
            {"name": "admin", "description": "Admin team"}
        ]

        for role_data in roles_data:
            role = Role(**role_data)
            session.add(role)

        session.commit()
        print("✅ Auth test database setup complete")
    finally:
        session.close()


@pytest.fixture
def auth_service():
    """Create AuthService instance"""
    return AuthService()


@pytest.fixture
def test_roles():
    """Get test roles"""
    session = Session()
    try:
        roles = session.query(Role).all()
        return {role.name: role for role in roles}
    finally:
        session.close()


class TestAuthService:
    """Test AuthService functionality"""

    def test_password_hashing(self, auth_service):
        """Test that password hashing works correctly"""
        password = "TestPassword123!"

        # Test hashing
        hashed = auth_service.hash_password(password)

        assert hashed is not None
        assert hashed != password  # Should be different from original
        assert len(hashed) > 50    # Argon2 hashes are long
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

    def test_create_employee_with_password(self, auth_service, test_roles):
        """Test creating employee with password"""
        employee_data = auth_service.create_employee_with_password(
            name="Test User",
            email="test@example.com",
            role_id=test_roles["sales"].id,
            password="SecurePass123!"
        )

        # Check returned data
        assert employee_data["name"] == "Test User"
        assert employee_data["email"] == "test@example.com"
        assert employee_data["role_id"] == test_roles["sales"].id
        assert employee_data["employee_number"].startswith("EMP")

        # Verify employee was created in database
        session = Session()
        try:
            employee = session.query(Employee).filter_by(
                employee_number=employee_data["employee_number"]
            ).first()

            assert employee is not None
            assert employee.password_hash is not None
            assert employee.password_hash != "SecurePass123!"  # Should be hashed
        finally:
            session.close()

    def test_employee_number_generation(self, auth_service, test_roles):
        """Test auto-generation of employee numbers"""
        # Clear existing employees first
        session = Session()
        try:
            session.query(Employee).delete()
            session.commit()
        finally:
            session.close()

        # Create first employee
        emp1 = auth_service.create_employee_with_password(
            name="Employee 1",
            email="emp1@example.com",
            role_id=test_roles["sales"].id,
            password="TestPassword123!"
        )

        # Create second employee
        emp2 = auth_service.create_employee_with_password(
            name="Employee 2",
            email="emp2@example.com",
            role_id=test_roles["support"].id,
            password="TestPassword123!"
        )

        # Check sequential numbering
        assert emp1["employee_number"] == "EMP001"
        assert emp2["employee_number"] == "EMP002"

    def test_authenticate_user_success(self, auth_service, test_roles):
        """Test successful user authentication"""
        password = "AuthTestPassword123!"

        # Create test user
        employee_data = auth_service.create_employee_with_password(
            name="Auth Test User",
            email="authtest@example.com",
            role_id=test_roles["sales"].id,
            password=password
        )

        # Test authentication
        success, employee, message = auth_service.authenticate_user(
            employee_data["employee_number"],
            password
        )

        assert success is True
        assert employee is not None

        # Check employee data through fresh session to avoid detached instance
        session = Session()
        try:
            fresh_employee = session.query(Employee).filter_by(
                employee_number=employee_data["employee_number"]
            ).first()
            assert fresh_employee.name == "Auth Test User"
        finally:
            session.close()

        assert "successful" in message.lower()

    def test_authenticate_user_wrong_password(self, auth_service, test_roles):
        """Test authentication with wrong password"""
        # Create test user
        employee_data = auth_service.create_employee_with_password(
            name="Wrong Pass Test",
            email="wrongpass@example.com",
            role_id=test_roles["sales"].id,
            password="CorrectPassword123!"
        )

        # Test with wrong password
        success, employee, message = auth_service.authenticate_user(
            employee_data["employee_number"],
            "WrongPassword123!"
        )

        assert success is False
        assert employee is None
        assert ("invalid password"
                in message.lower()
                or "attempts remaining"
                in message.lower())

    def test_authenticate_nonexistent_user(self, auth_service):
        """Test authentication with non-existent user"""
        success, employee, message = auth_service.authenticate_user(
            "EMP999",
            "AnyPasswordTest123!"
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
            password="CorrectPassword123!"
        )

        employee_number = employee_data["employee_number"]

        # Make 5 failed attempts (should lock on 5th)
        for i in range(5):
            success, employee, message = auth_service.authenticate_user(
                employee_number,
                "WrongPasswordTest123!"
            )
            assert success is False

        # 6th attempt should show account locked
        success, employee, message = auth_service.authenticate_user(
            employee_number,
            "WrongPasswordTest123!"
        )

        assert success is False
        assert "locked" in message.lower()

        # Even correct password should fail when locked
        success, employee, message = auth_service.authenticate_user(
            employee_number,
            "CorrectPassword123!"
        )

        assert success is False
        assert "locked" in message.lower()

    def test_successful_login_resets_attempts(self, auth_service, test_roles):
        """Test that successful login resets failed attempts"""
        # Create test user
        employee_data = auth_service.create_employee_with_password(
            name="Reset Test User",
            email="resettest@example.com",
            role_id=test_roles["sales"].id,
            password="ResetPassword123!"
        )

        employee_number = employee_data["employee_number"]

        # Make 2 failed attempts
        for i in range(2):
            auth_service.authenticate_user(employee_number, "WrongPasswordTest123!")

        # Successful login should reset counter
        success, employee, message = auth_service.authenticate_user(
            employee_number,
            "ResetPassword123!"
        )

        assert success is True

        # Check that failed attempts were reset
        session = Session()
        try:
            employee = session.query(Employee).filter_by(
                employee_number=employee_number
            ).first()

            assert employee.failed_login_attempts == 0
            assert employee.last_login is not None
        finally:
            session.close()


class TestEmployeeModel:
    """Test Employee model authentication methods"""

    def test_employee_generate_number(self):
        """Test static employee number generation"""
        session = Session()
        try:
            # Should start with EMP001 when no employees exist
            session.query(Employee).delete()
            session.commit()

            number = Employee.generate_employee_number(session)
            assert number == "EMP001"
        finally:
            session.close()
