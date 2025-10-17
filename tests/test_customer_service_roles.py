"""
Tests for CustomerService with role-based access control
Tests the list_customers functionality with different user roles
"""

import pytest
from unittest.mock import MagicMock, patch
from services.customer import CustomerService
from utils.permissions import Permission, PermissionError


class TestCustomerServiceRoleBasedAccess:
    """Test suite for CustomerService role-based access control"""

    @pytest.fixture
    def mock_repository(self):
        """Mock customer repository"""
        return MagicMock()

    @pytest.fixture
    def customer_service(self, mock_repository):
        """Create CustomerService with mocked repository"""
        return CustomerService(mock_repository)

    @pytest.fixture
    def admin_user(self):
        """Admin user fixture"""
        return {
            'id': 1,
            'name': 'Admin User',
            'role': 'admin',
            'role_id': 4
        }

    @pytest.fixture
    def management_user(self):
        """Management user fixture"""
        return {
            'id': 2,
            'name': 'Manager User',
            'role': 'management',
            'role_id': 3
        }

    @pytest.fixture
    def sales_user(self):
        """Sales user fixture"""
        return {
            'id': 3,
            'name': 'Sales User',
            'role': 'sales',
            'role_id': 1
        }

    @pytest.fixture
    def support_user(self):
        """Support user fixture"""
        return {
            'id': 4,
            'name': 'Support User',
            'role': 'support',
            'role_id': 2
        }

    @patch('services.customer.require_permission')
    def test_list_customers_admin_sees_all(self,
                                           mock_require_permission,
                                           customer_service,
                                           mock_repository,
                                           admin_user):
        """Test that admin users see all customers"""
        # Setup
        mock_customers = [MagicMock(), MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_customers

        # Execute
        result = customer_service.list_customers(admin_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            admin_user, Permission.READ_CUSTOMER)
        mock_repository.get_all.assert_called_once()
        assert result == mock_customers

    @patch('services.customer.require_permission')
    def test_list_customers_management_sees_all(self, mock_require_permission,
                                                customer_service, mock_repository,
                                                management_user):
        """Test that management users see all customers"""
        # Setup
        mock_customers = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_customers

        # Execute
        result = customer_service.list_customers(management_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            management_user, Permission.READ_CUSTOMER)
        mock_repository.get_all.assert_called_once()
        assert result == mock_customers

    @patch('services.customer.require_permission')
    def test_list_customers_support_sees_all(self,
                                             mock_require_permission,
                                             customer_service,
                                             mock_repository,
                                             support_user):
        """Test that support users see all customers"""
        # Setup
        mock_customers = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_customers

        # Execute
        result = customer_service.list_customers(support_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            support_user, Permission.READ_CUSTOMER)
        mock_repository.get_all.assert_called_once()
        assert result == mock_customers

    @patch('services.customer.require_permission')
    def test_list_customers_sales_sees_only_assigned(self,
                                                     mock_require_permission,
                                                     customer_service,
                                                     mock_repository,
                                                     sales_user):
        """Test that sales users see only their assigned customers"""
        # Setup
        mock_customers = [MagicMock(), MagicMock()]
        mock_repository.find_by_sales_contact.return_value = mock_customers

        # Execute
        result = customer_service.list_customers(sales_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            sales_user, Permission.READ_CUSTOMER)
        mock_repository.find_by_sales_contact.assert_called_once_with(
            sales_user['id'])
        mock_repository.get_all.assert_not_called()
        assert result == mock_customers

    @patch('services.customer.require_permission')
    def test_list_customers_unknown_role_returns_empty(self,
                                                       mock_require_permission,
                                                       customer_service,
                                                       mock_repository):
        """Test that unknown roles get empty list"""
        # Setup
        unknown_user = {'id': 5, 'name': 'Unknown', 'role': 'unknown'}

        # Execute
        result = customer_service.list_customers(unknown_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            unknown_user, Permission.READ_CUSTOMER)
        mock_repository.get_all.assert_not_called()
        mock_repository.find_by_sales_contact.assert_not_called()
        assert result == []

    @patch('services.customer.require_permission')
    def test_list_customers_permission_denied_raises_error(self,
                                                           mock_require_permission,
                                                           customer_service,
                                                           mock_repository,
                                                           sales_user):
        """Test that permission denial raises PermissionError"""
        # Setup
        mock_require_permission.side_effect = PermissionError("Access denied")

        # Execute & Verify
        with pytest.raises(PermissionError):
            customer_service.list_customers(sales_user)

        mock_repository.get_all.assert_not_called()
        mock_repository.find_by_sales_contact.assert_not_called()
