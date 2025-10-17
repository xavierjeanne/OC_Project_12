"""
Tests for JWT Service
Tests the JWT token creation, validation, and management functionality
"""

import pytest
import jwt
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from services.jwt_service import JWTService


class TestJWTService:
    """Test suite for JWT Service"""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service instance"""
        return JWTService()

    @pytest.fixture
    def sample_employee_data(self):
        """Sample employee data for testing"""
        return {
            "id": 1,
            "employee_number": "EMP001",
            "name": "Test User",
            "email": "test@example.com",
            "role": "admin",
            "role_id": 4
        }

    @pytest.fixture
    def mock_env_secret(self):
        """Mock environment secret"""
        with patch.dict(os.environ, {'EPIC_EVENTS_JWT_SECRET': 'test_secret_key'}):
            yield

    def test_get_secret_key_from_env(self, jwt_service, mock_env_secret):
        """Test getting secret key from environment"""
        secret = jwt_service._get_secret_key()
        assert secret == 'test_secret_key'

    def test_get_secret_key_generate_new(self, jwt_service):
        """Test generating new secret key when not in env"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('pathlib.Path.exists', return_value=False):
                with patch('pathlib.Path.write_text') as mock_write:
                    secret = jwt_service._get_secret_key()
                    assert len(secret) > 20  # Generated secret should be long
                    mock_write.assert_called_once()

    def test_create_access_token(self, jwt_service, sample_employee_data,
                                 mock_env_secret):
        """Test creating access token"""
        token = jwt_service.create_access_token(sample_employee_data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode to verify content
        secret = jwt_service._get_secret_key()
        payload = jwt.decode(token, secret, algorithms=[jwt_service.algorithm])

        assert payload["sub"] == "1"
        assert payload["employee_number"] == "EMP001"
        assert payload["name"] == "Test User"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"
        assert payload["role_id"] == 4
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token(self, jwt_service, sample_employee_data,
                                  mock_env_secret):
        """Test creating refresh token"""
        token = jwt_service.create_refresh_token(sample_employee_data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode to verify content
        secret = jwt_service._get_secret_key()
        payload = jwt.decode(token, secret, algorithms=[jwt_service.algorithm])

        assert payload["sub"] == "1"
        assert payload["employee_number"] == "EMP001"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        # Refresh token should not contain sensitive data
        assert "name" not in payload
        assert "email" not in payload
        assert "role" not in payload

    def test_verify_valid_access_token(self, jwt_service, sample_employee_data,
                                       mock_env_secret):
        """Test verifying valid access token"""
        token = jwt_service.create_access_token(sample_employee_data)
        payload = jwt_service.verify_token(token, "access")

        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["type"] == "access"

    def test_verify_valid_refresh_token(self, jwt_service, sample_employee_data,
                                        mock_env_secret):
        """Test verifying valid refresh token"""
        token = jwt_service.create_refresh_token(sample_employee_data)
        payload = jwt_service.verify_token(token, "refresh")

        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    def test_verify_invalid_token(self, jwt_service, mock_env_secret):
        """Test verifying invalid token"""
        payload = jwt_service.verify_token("invalid_token", "access")
        assert payload is None

    def test_verify_wrong_token_type(self, jwt_service, sample_employee_data,
                                     mock_env_secret):
        """Test verifying token with wrong type"""
        access_token = jwt_service.create_access_token(sample_employee_data)

        # Try to verify access token as refresh token
        payload = jwt_service.verify_token(access_token, "refresh")
        assert payload is None

    def test_verify_expired_token(self, jwt_service, sample_employee_data,
                                  mock_env_secret):
        """Test verifying expired token"""
        # Create token with very short expiry
        jwt_service.access_token_expire_minutes = -1  # Already expired
        token = jwt_service.create_access_token(sample_employee_data)

        payload = jwt_service.verify_token(token, "access")
        assert payload is None

    @patch('models.Session')
    def test_refresh_access_token_success(self,
                                          mock_session_class,
                                          jwt_service,
                                          sample_employee_data,
                                          mock_env_secret):
        """Test successful access token refresh"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_employee = MagicMock()
        mock_employee.id = 1
        mock_employee.employee_number = "EMP001"
        mock_employee.name = "Test User"
        mock_employee.email = "test@example.com"
        mock_employee.role = "admin"  # This is the role name
        mock_employee.role_id = 4

        query_result = mock_session.query.return_value.filter_by.return_value
        query_result.first.return_value = mock_employee

        # Create refresh token
        refresh_token = jwt_service.create_refresh_token(sample_employee_data)

        # Test refresh
        new_access_token = jwt_service.refresh_access_token(refresh_token)

        assert new_access_token is not None
        assert isinstance(new_access_token, str)

        # Verify new token is valid
        payload = jwt_service.verify_token(new_access_token, "access")
        assert payload is not None
        assert payload["sub"] == "1"

    def test_refresh_access_token_invalid_refresh(self,
                                                  jwt_service,
                                                  mock_env_secret):
        """Test refresh with invalid refresh token"""
        new_access_token = jwt_service.refresh_access_token("invalid_token")
        assert new_access_token is None

    @patch('models.Session')
    def test_refresh_access_token_user_not_found(self,
                                                 mock_session_class,
                                                 jwt_service,
                                                 sample_employee_data,
                                                 mock_env_secret):
        """Test refresh when user no longer exists"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Create refresh token
        refresh_token = jwt_service.create_refresh_token(sample_employee_data)

        # Test refresh
        new_access_token = jwt_service.refresh_access_token(refresh_token)
        assert new_access_token is None

    def test_token_expiry_times(self, jwt_service, sample_employee_data,
                                mock_env_secret):
        """Test that token expiry times are reasonable"""
        access_token = jwt_service.create_access_token(sample_employee_data)
        refresh_token = jwt_service.create_refresh_token(sample_employee_data)

        secret = jwt_service._get_secret_key()

        access_payload = jwt.decode(access_token, secret,
                                    algorithms=[jwt_service.algorithm])
        refresh_payload = jwt.decode(refresh_token, secret,
                                     algorithms=[jwt_service.algorithm])

        access_exp = datetime.fromtimestamp(access_payload["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
        now = datetime.utcnow()

        # Access token should expire in reasonable time (allow more flexibility)
        access_delta = access_exp - now
        assert 10 <= access_delta.total_seconds() / 60 <= 200

        # Refresh token should expire in reasonable days
        refresh_delta = refresh_exp - now
        assert 5 <= refresh_delta.days <= 10  # Between 5 and 10 days

    def test_algorithm_setting(self, jwt_service):
        """Test that correct algorithm is used"""
        assert jwt_service.algorithm == "HS256"

    def test_token_structure(self, jwt_service, sample_employee_data,
                             mock_env_secret):
        """Test token structure and required fields"""
        access_token = jwt_service.create_access_token(sample_employee_data)

        # JWT should have 3 parts separated by dots
        parts = access_token.split('.')
        assert len(parts) == 3

        secret = jwt_service._get_secret_key()
        payload = jwt.decode(access_token, secret,
                             algorithms=[jwt_service.algorithm])

        # Required fields
        required_fields = ["sub", "employee_number", "name", "email", "role",
                           "role_id", "exp", "iat", "type"]
        for field in required_fields:
            assert field in payload
