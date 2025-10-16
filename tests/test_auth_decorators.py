"""
Tests for Authentication Decorators
Tests CLI authentication and authorization decorators
"""

import pytest
from unittest.mock import patch

from utils.auth_decorators import (
    cli_auth_required,
    cli_permission_required,
    cli_role_required,
    auto_refresh_token
)
from utils.permissions import Permission


class TestAuthDecorators:
    """Test suite for authentication decorators"""

    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager"""
        with patch('utils.auth_decorators.auth_manager') as mock:
            yield mock

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data"""
        return {
            "id": 1,
            "employee_number": "EMP001",
            "name": "Test User",
            "email": "test@example.com",
            "role": "admin",
            "role_id": 4
        }

    def test_cli_auth_required_success(self, mock_auth_manager, sample_user_data):
        """Test cli_auth_required decorator with authenticated user"""
        # Mock authentication success
        mock_auth_manager.require_authentication.return_value = True

        # Create test function
        @cli_auth_required
        def test_function():
            return "success"

        # Should execute successfully
        result = test_function()
        assert result == "success"

        # Verify auth check was called
        mock_auth_manager.require_authentication.assert_called_once()

    def test_cli_auth_required_failure(self, mock_auth_manager):
        """Test cli_auth_required decorator with no authentication"""
        # Mock authentication failure
        mock_auth_manager.require_authentication.return_value = False

        # Create test function
        @cli_auth_required
        def test_function():
            return "success"

        # Should return None and not execute function
        result = test_function()
        assert result is None

        mock_auth_manager.require_authentication.assert_called_once()

    def test_cli_permission_required_success(self, mock_auth_manager, sample_user_data):
        """Test cli_permission_required decorator with sufficient permissions"""
        # Mock permission success
        mock_auth_manager.require_permission.return_value = True

        # Create test function
        @cli_permission_required(Permission.CREATE_CUSTOMER)
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

        mock_auth_manager.require_permission.assert_called_once_with(
            Permission.CREATE_CUSTOMER)

    def test_cli_permission_required_failure(self, mock_auth_manager, sample_user_data):
        """Test cli_permission_required decorator without sufficient permissions"""
        # Mock authenticated user without permission
        mock_auth_manager.get_current_user.return_value = sample_user_data
        mock_auth_manager.require_permission.return_value = False

        # Create test function
        @cli_permission_required(Permission.DELETE_CUSTOMER)
        def test_function():
            return "success"

        result = test_function()
        assert result is None

        mock_auth_manager.require_permission.assert_called_once_with(
            Permission.DELETE_CUSTOMER)

    def test_cli_permission_required_not_authenticated(self, mock_auth_manager):
        """Test cli_permission_required decorator when not authenticated"""
        # Mock permission failure (due to no authentication)
        mock_auth_manager.require_permission.return_value = False

        # Create test function
        @cli_permission_required(Permission.CREATE_CUSTOMER)
        def test_function():
            return "success"

        result = test_function()
        assert result is None

        mock_auth_manager.require_permission.assert_called_once_with(
            Permission.CREATE_CUSTOMER)

    def test_cli_role_required_success(self, mock_auth_manager, sample_user_data):
        """Test cli_role_required decorator with correct role"""
        # Mock authenticated admin user
        mock_auth_manager.get_current_user.return_value = sample_user_data

        # Create test function requiring admin role
        @cli_role_required("admin")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

        mock_auth_manager.get_current_user.assert_called_once()

    def test_cli_role_required_failure(self, mock_auth_manager):
        """Test cli_role_required decorator with wrong role"""
        # Mock authenticated sales user
        sales_user = {
            "id": 2,
            "employee_number": "EMP002",
            "name": "Sales User",
            "email": "sales@example.com",
            "role": "sales",
            "role_id": 1
        }
        mock_auth_manager.get_current_user.return_value = sales_user

        # Create test function requiring admin role
        @cli_role_required("admin")
        def test_function():
            return "success"

        result = test_function()
        assert result is None

        mock_auth_manager.get_current_user.assert_called_once()

    def test_cli_role_required_not_authenticated(self, mock_auth_manager):
        """Test cli_role_required decorator when not authenticated"""
        # Mock no user
        mock_auth_manager.get_current_user.return_value = None

        # Create test function
        @cli_role_required("admin")
        def test_function():
            return "success"

        result = test_function()
        assert result is None

    def test_auto_refresh_token_with_user(self, mock_auth_manager, sample_user_data):
        """Test auto_refresh_token decorator with authenticated user"""
        # Mock authenticated user
        mock_auth_manager.get_current_user.return_value = sample_user_data

        # Create test function
        @auto_refresh_token
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

        # Should call get_current_user to check/refresh session
        mock_auth_manager.get_current_user.assert_called_once()

    def test_auto_refresh_token_no_user(self, mock_auth_manager):
        """Test auto_refresh_token decorator with no user"""
        # Mock no user
        mock_auth_manager.get_current_user.return_value = None

        # Create test function
        @auto_refresh_token
        def test_function():
            return "success"

        # Should return None when no user (prints message and returns)
        result = test_function()
        assert result is None

        mock_auth_manager.get_current_user.assert_called_once()

    def test_decorator_combination(self, mock_auth_manager, sample_user_data):
        """Test combining multiple decorators"""
        # Mock authenticated admin user with permission
        mock_auth_manager.get_current_user.return_value = sample_user_data
        mock_auth_manager.require_permission.return_value = True

        # Create test function with multiple decorators
        @cli_auth_required
        @cli_role_required("admin")
        @cli_permission_required(Permission.CREATE_CUSTOMER)
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_decorator_combination_failure(self, mock_auth_manager):
        """Test decorator combination with authentication failure"""
        # Mock no user
        mock_auth_manager.get_current_user.return_value = None

        # Create test function with multiple decorators
        @cli_auth_required
        @cli_role_required("admin")
        @cli_permission_required(Permission.CREATE_CUSTOMER)
        def test_function():
            return "success"

        result = test_function()
        assert result is None

    def test_function_with_args_and_kwargs(self, mock_auth_manager, sample_user_data):
        """Test decorators work with functions that have arguments"""
        # Mock authenticated user
        mock_auth_manager.get_current_user.return_value = sample_user_data

        @cli_auth_required
        def test_function(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        result = test_function("test1", "test2", kwarg1="test3")
        assert result == "test1-test2-test3"
