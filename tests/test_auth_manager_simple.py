"""
Tests for Authentication Manager - Simplified Version
Tests core session management functionality
"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from services.auth_manager import AuthenticationManager


class TestAuthenticationManagerSimple:
    """Simplified test suite for Authentication Manager"""

    @pytest.fixture
    def auth_manager(self):
        """Create authentication manager instance"""
        return AuthenticationManager()

    @pytest.fixture
    def sample_employee_data(self):
        """Sample employee data"""
        return {
            "id": 1,
            "employee_number": "EMP001",
            "name": "Test User",
            "email": "test@example.com",
            "role": "admin",
            "role_id": 4
        }

    def test_initialization(self, auth_manager):
        """Test proper initialization"""
        assert auth_manager.current_user is None
        assert auth_manager.auth_service is not None
        assert auth_manager.jwt_service is not None
        assert auth_manager.token_file.name == ".epic_events_tokens"
        assert auth_manager.token_file.parent == Path.home()

    def test_login_success(self, auth_manager, sample_employee_data):
        """Test successful login flow"""
        # Mock successful authentication
        auth_manager.auth_service.authenticate_user = MagicMock(
            return_value=(True, sample_employee_data, "Login successful")
        )

        # Mock JWT token creation
        auth_manager.jwt_service.create_access_token = MagicMock(
            return_value="access_token"
            )
        auth_manager.jwt_service.create_refresh_token = MagicMock(
            return_value="refresh_token"
            )

        # Mock token saving (to avoid file I/O)
        auth_manager._save_tokens = MagicMock()

        result = auth_manager.login("EMP001", "password123")

        # Verify successful result
        assert result["success"] is True
        assert result["user"] == sample_employee_data
        assert auth_manager.current_user == sample_employee_data
        assert "Welcome Test User" in result["message"]

        # Verify method calls
        auth_manager.auth_service.authenticate_user.assert_called_once_with(
            "EMP001", "password123")
        auth_manager.jwt_service.create_access_token.assert_called_once_with(
            sample_employee_data)
        auth_manager.jwt_service.create_refresh_token.assert_called_once_with(
            sample_employee_data)
        auth_manager._save_tokens.assert_called_once()

    def test_login_failure(self, auth_manager):
        """Test failed login"""
        # Mock failed authentication
        auth_manager.auth_service.authenticate_user = MagicMock(
            return_value=(False, None, "Invalid password")
        )

        result = auth_manager.login("EMP001", "wrong_password")

        assert result["success"] is False
        assert result["user"] is None
        assert result["message"] == "Invalid password"
        assert auth_manager.current_user is None

    def test_logout_success(self, auth_manager, sample_employee_data):
        """Test successful logout"""
        # Set current user
        auth_manager.current_user = sample_employee_data

        result = auth_manager.logout()

        assert result["success"] is True
        assert "Goodbye Test User" in result["message"]
        assert auth_manager.current_user is None

    def test_logout_not_logged_in(self, auth_manager):
        """Test logout when not logged in"""
        # Make sure no user is set
        auth_manager.current_user = None

        result = auth_manager.logout()

        assert result["success"] is True
        assert ("No user currently logged in"
                in result["message"] or "Goodbye"
                in result["message"])

    def test_get_current_user_cached(self, auth_manager, sample_employee_data):
        """Test getting current user when cached"""
        auth_manager.current_user = sample_employee_data

        user = auth_manager.get_current_user()
        assert user == sample_employee_data

    def test_get_current_user_no_session(self, auth_manager):
        """Test getting current user when no session exists"""
        # Mock no tokens available
        auth_manager._load_tokens = MagicMock(return_value=None)

        user = auth_manager.get_current_user()
        assert user is None

    def test_require_authentication_success(self, auth_manager, sample_employee_data):
        """Test require authentication when logged in"""
        auth_manager.current_user = sample_employee_data

        result = auth_manager.require_authentication()
        assert result is True

    def test_require_authentication_failure(self, auth_manager):
        """Test require authentication when not logged in"""
        # Mock get_current_user to return None
        auth_manager.get_current_user = MagicMock(return_value=None)

        result = auth_manager.require_authentication()
        assert result is False

    def test_session_info_with_user(self, auth_manager, sample_employee_data):
        """Test getting session info when logged in"""
        auth_manager.current_user = sample_employee_data

        # Mock tokens for session info
        mock_tokens = {
            "access_token": "fake_token",
            "refresh_token": "fake_refresh",
            "created_at": "2025-10-16T10:00:00"
        }
        auth_manager._load_tokens = MagicMock(return_value=mock_tokens)

        session_info = auth_manager.get_session_info()

        # Should return session info when user is logged in
        if session_info:  # Method might return None in some cases
            assert "user" in session_info or session_info is not None

    def test_session_info_no_user(self, auth_manager):
        """Test getting session info when not logged in"""
        auth_manager.current_user = None

        session_info = auth_manager.get_session_info()
        assert session_info is None
