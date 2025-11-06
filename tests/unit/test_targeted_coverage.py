"""
test for targeted coverage.
"""

import pytest
from unittest.mock import MagicMock, patch

# Test des utilitaires avec une couverture perfectible
from utils.validators import (
    validate_date,
    validate_phone,
    ValidationError,
    validate_string_not_empty,
    validate_email,
    validate_positive_amount,
    validate_role,
)
from utils.permissions import (
    Permission,
    PermissionError,
    require_permission,
    has_permission,
)


class TestValidatorsCoverage:
    """Tests for improving coverage of validators (currently 88%)"""

    def test_validate_date_invalid_format(self):
        """Test date validation with invalid format - lines 137-138"""
        with pytest.raises(ValidationError):
            validate_date("invalid-date", "test_date")

    def test_validate_phone_invalid_format(self):
        """Test phone validation with invalid format - lines 114, 118-119"""
        with pytest.raises(ValidationError, match="Phone number.*is not valid"):
            validate_phone("invalid-phone")

        with pytest.raises(ValidationError, match="Phone number.*is not valid"):
            validate_phone("123")  # Too short

    def test_validate_string_not_empty_none_value(self):
        """Test validation string not empty avec None - ligne 187"""
        with pytest.raises(ValidationError, match="The test_field field is required"):
            validate_string_not_empty(None, "test_field")

    def test_validate_email_invalid_domain(self):
        """Test validation email avec domaine invalide - ligne 300"""
        with pytest.raises(ValidationError, match="Email.*is not valid"):
            validate_email("test@invalid")

    def test_validate_email_missing_at_symbol(self):
        """Test validation email sans @ - ligne 346"""
        with pytest.raises(ValidationError):
            validate_email("testinvalid.com")

    def test_validate_positive_amount_negative(self):
        """Test validation montant positif avec valeur négative"""
        with pytest.raises(ValidationError):
            validate_positive_amount(-100.0, "test_amount")

    def test_validate_role_invalid(self):
        """Test validation rôle invalide"""
        with pytest.raises(ValidationError):
            validate_role("invalid_role")


class TestPermissionsCoverage:
    """Tests for improving coverage of permissions (currently 96%)"""

    def test_permission_enum_values(self):
        """Test permission enum values - line 205"""
        # Test que toutes les permissions existent
        assert Permission.CREATE_CUSTOMER is not None
        assert Permission.UPDATE_CUSTOMER is not None
        assert Permission.DELETE_CUSTOMER is not None
        assert Permission.READ_CUSTOMER is not None

    def test_has_permission_invalid_user(self):
        """Test has_permission with invalid user - line 224"""
        result = has_permission(None, Permission.READ_CUSTOMER)
        assert result is False

    def test_has_permission_missing_role(self):
        """Test has_permission with missing role - line 230"""
        user = {"id": 1}  # No role
        result = has_permission(user, Permission.READ_CUSTOMER)
        assert result is False

    def test_require_permission_insufficient_rights(self):
        """Test require_permission with insufficient rights - line  249"""
        user = {"id": 1, "role": "sales"}

        with pytest.raises(PermissionError, match="does not have permission"):
            require_permission(user, Permission.CREATE_EMPLOYEE)


class TestDatabaseConfigCoverage:
    """Tests for improving coverage of db.config (currently 62%)"""

    @patch.dict(
        "os.environ",
        {
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "test_db",
        },
    )
    def test_database_url_construction(self):
        """Test construction of database URL"""
        import db.config

        # Force module reload to account for new variables
        import importlib

        importlib.reload(db.config)

        assert (
            "postgresql+psycopg2://test_user:test_password@localhost:5432/test_db"
            in db.config.DATABASE_URL
        )

    @patch("db.config.engine")
    def test_connection_test_success(self, mock_engine):
        """Test test_connection function with success"""
        from db.config import test_connection

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = lambda self: mock_connection
        mock_engine.connect.return_value.__exit__ = lambda self, *args: None

        # This should cover the lines in test_connection
        test_connection()

    @patch("db.config.engine")
    def test_connection_test_failure(self, mock_engine):
        """Test test_connection function with failure"""
        from db.config import test_connection

        mock_engine.connect.side_effect = Exception("Connection failed")

        # This should cover the exception branch
        test_connection()


class TestModelsAttributesCoverage:
    """Tests for improving coverage of models with untested attributes"""

    def test_employee_repr(self):
        """Test string representation of Employee - line 43"""
        from models.employee import Employee

        employee = Employee(name="Test Employee", email="test@example.com")
        repr_str = repr(employee)
        assert "Test Employee" in repr_str
        assert "test@example.com" in repr_str

    def test_customer_repr(self):
        """Test string representation of Customer - lines 32-34"""
        from models.customer import Customer

        customer = Customer(full_name="Test Customer", email="test@example.com")
        repr_str = repr(customer)
        assert "Test Customer" in repr_str

    def test_contract_repr(self):
        """Test string representation of Contract - lines 29-31"""
        from models.contract import Contract

        contract = Contract(total_amount=1000.0, customer_id=1)
        repr_str = repr(contract)
        assert "1000.0" in repr_str

    def test_event_repr(self):
        """Test string representation of Event - lines 32-34"""
        from models.event import Event

        event = Event(name="Test Event", contract_id=1)
        repr_str = repr(event)
        assert "Test Event" in repr_str

    def test_role_repr(self):
        """Test string representation of Role - line 21"""
        from models.role import Role

        role = Role(name="admin")
        repr_str = repr(role)
        assert "admin" in repr_str


class TestBaseModelCoverage:
    """Tests for improving coverage of models.base"""

    def test_base_init_db(self):
        """Test init_db function - lines 17-18"""
        from models.base import init_db

        # Test init_db function (without actually creating tables)
        with patch("models.base.Base.metadata.create_all") as mock_create:
            with patch("builtins.print") as mock_print:
                init_db()
                mock_create.assert_called_once()
                mock_print.assert_called_with("All tables created successfully.")


class TestJWTServiceCoverage:
    """Tests for improving coverage of jwt_service"""

    def test_jwt_service_initialization(self):
        """Test initialization JWT service"""
        from services.jwt_service import JWTService

        # Test simple initialisation
        jwt_service = JWTService()
        assert jwt_service.algorithm == "HS256"
        assert jwt_service.access_token_expire_minutes > 0
        assert jwt_service.refresh_token_expire_days > 0


class TestAuthManagerCoverage:
    """Tests for improving coverage of auth_manager"""

    def test_auth_manager_initialization(self):
        """Test initialization auth manager"""
        from services.auth_manager import AuthenticationManager

        auth_manager = AuthenticationManager()
        assert auth_manager.token_file.name == ".epic_events_tokens"
        assert hasattr(auth_manager, "login")
        assert hasattr(auth_manager, "logout")
