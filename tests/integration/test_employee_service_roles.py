"""
Tests for EmployeeService with role-based access control
Tests the list_employees functionality with different user roles
"""

import pytest
from unittest.mock import MagicMock, patch
from services.employee import EmployeeService
from utils.permissions import Permission


class TestEmployeeServiceRoleBasedAccess:
    """Test suite for EmployeeService role-based access control"""

    @pytest.fixture
    def mock_repository(self):
        """Mock employee repository"""
        return MagicMock()

    @pytest.fixture
    def employee_service(self, mock_repository):
        """Create EmployeeService with mocked repository"""
        return EmployeeService(mock_repository)

    @pytest.fixture
    def admin_user(self):
        """Admin user fixture"""
        return {"id": 1, "name": "Admin User", "role": "admin", "role_id": 4}

    @pytest.fixture
    def management_user(self):
        """Management user fixture"""
        return {"id": 2, "name": "Manager User", "role": "management", "role_id": 3}

    @pytest.fixture
    def sales_user(self):
        """Sales user fixture"""
        return {"id": 3, "name": "Sales User", "role": "sales", "role_id": 1}

    @pytest.fixture
    def support_user(self):
        """Support user fixture"""
        return {"id": 4, "name": "Support User", "role": "support", "role_id": 2}

    @patch("services.employee.require_permission")
    def test_list_employees_admin_sees_all(
        self, mock_require_permission, employee_service, mock_repository, admin_user
    ):
        """Test that admin users see all employees"""
        # Setup
        mock_employees = [MagicMock(), MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_employees

        # Execute
        result = employee_service.list_employees(admin_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            admin_user, Permission.READ_EMPLOYEE
        )
        mock_repository.get_all.assert_called_once()
        assert result == mock_employees

    @patch("services.employee.require_permission")
    def test_list_employees_management_sees_all(
        self,
        mock_require_permission,
        employee_service,
        mock_repository,
        management_user,
    ):
        """Test that management users see all employees"""
        # Setup
        mock_employees = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_employees

        # Execute
        result = employee_service.list_employees(management_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            management_user, Permission.READ_EMPLOYEE
        )
        mock_repository.get_all.assert_called_once()
        assert result == mock_employees

    @patch("services.employee.require_permission")
    def test_list_employees_sales_sees_sales_and_management(
        self, mock_require_permission, employee_service, mock_repository, sales_user
    ):
        """Test that sales users see only sales team + management"""
        # Setup
        mock_sales_team = [MagicMock(), MagicMock()]
        mock_management_team = [MagicMock()]
        mock_repository.find_by_role.side_effect = lambda role: {
            "sales": mock_sales_team,
            "management": mock_management_team,
        }[role]

        # Execute
        result = employee_service.list_employees(sales_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            sales_user, Permission.READ_EMPLOYEE
        )
        assert mock_repository.find_by_role.call_count == 2
        mock_repository.find_by_role.assert_any_call("sales")
        mock_repository.find_by_role.assert_any_call("management")
        mock_repository.get_all.assert_not_called()
        assert result == mock_sales_team + mock_management_team

    @patch("services.employee.require_permission")
    def test_list_employees_support_sees_support_and_management(
        self, mock_require_permission, employee_service, mock_repository, support_user
    ):
        """Test that support users see only support team + management"""
        # Setup
        mock_support_team = [MagicMock(), MagicMock()]
        mock_management_team = [MagicMock()]
        mock_repository.find_by_role.side_effect = lambda role: {
            "support": mock_support_team,
            "management": mock_management_team,
        }[role]

        # Execute
        result = employee_service.list_employees(support_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            support_user, Permission.READ_EMPLOYEE
        )
        assert mock_repository.find_by_role.call_count == 2
        mock_repository.find_by_role.assert_any_call("support")
        mock_repository.find_by_role.assert_any_call("management")
        mock_repository.get_all.assert_not_called()
        assert result == mock_support_team + mock_management_team

    @patch("services.employee.require_permission")
    def test_list_employees_unknown_role_returns_empty(
        self, mock_require_permission, employee_service, mock_repository
    ):
        """Test that unknown roles get empty list"""
        # Setup
        unknown_user = {"id": 5, "name": "Unknown", "role": "unknown"}

        # Execute
        result = employee_service.list_employees(unknown_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            unknown_user, Permission.READ_EMPLOYEE
        )
        mock_repository.get_all.assert_not_called()
        mock_repository.find_by_role.assert_not_called()
        assert result == []
