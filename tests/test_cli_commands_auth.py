"""
Tests for CLI commands with authentication and role-based access
Tests the list commands functionality with different user roles
"""

import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
import sys

from cli.commands import (
    list_customers_command,
    list_contracts_command,
    list_events_command,
    list_employees_command
)


class TestCLICommandsWithAuth:
    """Test suite for CLI commands with authentication"""

    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager"""
        with patch('cli.commands.auth_manager') as mock:
            yield mock

    @pytest.fixture
    def mock_session_class(self):
        """Mock database session class"""
        with patch('cli.commands.Session') as mock:
            yield mock

    @pytest.fixture
    def mock_auth_decorator(self):
        """Mock the auth decorator to bypass authentication"""
        with patch('utils.auth_decorators.auth_manager') as mock:
            yield mock

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

    def test_list_customers_command_success_admin(self,
                                                  mock_auth_manager,
                                                  mock_session_class,
                                                  mock_auth_decorator,
                                                  admin_user):
        """Test list customers command with admin user"""
        # Setup - Mock the decorator's auth_manager
        mock_auth_decorator.get_current_user.return_value = admin_user

        # Setup - Mock the command's auth_manager
        mock_auth_manager.get_current_user.return_value = admin_user

        # Setup - Mock database session
        mock_db_session = MagicMock()
        mock_session_class.return_value = mock_db_session

        # Setup - Mock customers with required attributes
        sales_contact = MagicMock(name="Sales Person")
        mock_customers = [
            MagicMock(id=1, full_name="John Doe", email="john@example.com",
                      company_name="Acme Corp", sales_contact=sales_contact),
            MagicMock(id=2, full_name="Jane Smith", email="jane@example.com",
                      company_name="Tech Inc", sales_contact=None)
        ]

        # Mock the repository and service
        with patch('cli.commands.CustomerRepository') as mock_repo_class, \
             patch('cli.commands.CustomerService') as mock_service_class:

            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.list_customers.return_value = mock_customers

            # Capture output
            captured_output = StringIO()
            sys.stdout = captured_output

            # Execute
            list_customers_command()

            # Restore stdout
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

            # Verify
            mock_service.list_customers.assert_called_once_with(admin_user)
            assert "Customers List" in output
            assert "John Doe" in output
            assert "Jane Smith" in output

    def test_list_customers_command_not_authenticated(self):
        """Test list customers command without authentication"""
        # Setup - Mock auth_manager to return False for require_authentication
        # This simulates a user who is not logged in
        with patch('utils.auth_decorators.auth_manager') as mock_auth_manager:
            mock_auth_manager.require_authentication.return_value = False

            # Capture output
            captured_output = StringIO()
            sys.stdout = captured_output

            # Execute
            list_customers_command()

            # Restore stdout
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

            # Verify - Should call require_authentication and not show list
            # When require_authentication returns False, decorator prevents execution
            mock_auth_manager.require_authentication.assert_called_once()
            # Since authentication failed, no customer list should be shown
            assert "Customers List" not in output

    def test_list_contracts_command_success_sales(self, mock_session_class,
                                                  sales_user):
        """Test list contracts command with sales user"""
        # Mock both auth_managers - one in decorator and one in command
        with patch('utils.auth_decorators.auth_manager') as mock_decorator_auth, \
             patch('cli.commands.auth_manager') as mock_command_auth:

            # Setup authentication mocks
            mock_decorator_auth.require_authentication.return_value = True
            mock_command_auth.get_current_user.return_value = sales_user

            mock_db_session = MagicMock()
            mock_session_class.return_value = mock_db_session

            # Create proper mock contracts with all required attributes
            mock_contract1 = MagicMock()
            mock_contract1.id = 1
            mock_contract1.total_amount = 5000.0
            mock_contract1.remaining_amount = 1000.0
            mock_contract1.signed = True
            mock_contract1.customer.full_name = "John Doe"
            mock_contract1.sales_contact.name = "Sales Person"

            mock_contract2 = MagicMock()
            mock_contract2.id = 2
            mock_contract2.total_amount = 3000.0
            mock_contract2.remaining_amount = 3000.0
            mock_contract2.signed = False
            mock_contract2.customer.full_name = "Jane Smith"
            mock_contract2.sales_contact = None

            mock_contracts = [mock_contract1, mock_contract2]

            # Mock the service call
            with patch('cli.commands.ContractService') as mock_service_class:
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.list_contracts.return_value = mock_contracts

                # Capture output
                captured_output = StringIO()
                sys.stdout = captured_output

                # Execute
                list_contracts_command()

                # Restore stdout
                sys.stdout = sys.__stdout__
                output = captured_output.getvalue()

                # Verify
                mock_decorator_auth.require_authentication.assert_called_once()
                mock_service.list_contracts.assert_called_once_with(sales_user)
                assert "Contracts List" in output
                assert "John Doe" in output
                assert "Jane Smith" in output
                assert "€5,000.00" in output
                assert "€3,000.00" in output
                assert "Signed" in output
                assert "Unsigned" in output

    def test_list_events_command_success_support(self,
                                                 mock_session_class,
                                                 support_user):
        """Test list events command with support user"""
        # Mock both auth_managers - one in decorator and one in command
        with patch('utils.auth_decorators.auth_manager') as mock_decorator_auth, \
             patch('cli.commands.auth_manager') as mock_command_auth:
            # Setup authentication mocks
            mock_decorator_auth.require_authentication.return_value = True
            mock_command_auth.get_current_user.return_value = support_user

            mock_db_session = MagicMock()
            mock_session_class.return_value = mock_db_session

            # Create proper mock events with all required attributes
            mock_event1 = MagicMock()
            mock_event1.id = 1
            mock_event1.name = "Conference 2025"
            mock_event1.location = "Paris"
            mock_event1.attendees = 100
            mock_event1.customer.full_name = "John Doe"
            mock_event1.support_contact.name = "Support Person"

            mock_event2 = MagicMock()
            mock_event2.id = 2
            mock_event2.name = "Workshop"
            mock_event2.location = "Lyon"
            mock_event2.attendees = 50
            mock_event2.customer.full_name = "Jane Smith"
            mock_event2.support_contact = None

            mock_events = [mock_event1, mock_event2]

            # Mock the service call
            with patch('cli.commands.EventService') as mock_service_class:
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.list_events.return_value = mock_events

                # Capture output
                captured_output = StringIO()
                sys.stdout = captured_output

                # Execute
                list_events_command()

                # Restore stdout
                sys.stdout = sys.__stdout__
                output = captured_output.getvalue()

                # Verify
                mock_decorator_auth.require_authentication.assert_called_once()
                mock_service.list_events.assert_called_once_with(support_user)
                assert "🎪 Events List" in output
                assert "Conference 2025" in output
            assert "Workshop" in output

    def test_list_employees_command_success_admin(self, mock_session_class, admin_user):
        """Test list employees command with admin user"""
        # Mock both auth_managers - one in decorator and one in command
        with patch('utils.auth_decorators.auth_manager') as mock_decorator_auth, \
             patch('cli.commands.auth_manager') as mock_command_auth:

            # Setup authentication mocks
            mock_decorator_auth.require_authentication.return_value = True
            mock_command_auth.get_current_user.return_value = admin_user

            mock_db_session = MagicMock()
            mock_session_class.return_value = mock_db_session

            # Create proper mock employees with all required attributes
            mock_employee1 = MagicMock()
            mock_employee1.id = 1
            mock_employee1.name = "Admin User"
            mock_employee1.email = "admin@example.com"
            mock_employee1.employee_number = "EMP001"
            mock_employee1.employee_role.name = "admin"

            mock_employee2 = MagicMock()
            mock_employee2.id = 2
            mock_employee2.name = "Sales User"
            mock_employee2.email = "sales@example.com"
            mock_employee2.employee_number = "EMP002"
            mock_employee2.employee_role.name = "sales"

            mock_employees = [mock_employee1, mock_employee2]

            # Mock the service call
            with patch('cli.commands.EmployeeService') as mock_service_class:
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.list_employees.return_value = mock_employees

                # Capture output
                captured_output = StringIO()
                sys.stdout = captured_output

                # Execute
                list_employees_command()

                # Restore stdout
                sys.stdout = sys.__stdout__
                output = captured_output.getvalue()

                # Verify
                mock_decorator_auth.require_authentication.assert_called_once()
                mock_service.list_employees.assert_called_once_with(admin_user)
                assert "Employees List" in output
                assert "Admin User" in output
                assert "Sales User" in output

    def test_commands_handle_permission_errors_gracefully(self,
                                                          mock_session_class,
                                                          sales_user):
        """Test that commands handle permission errors gracefully"""
        # Mock both auth_managers - one in decorator and one in command
        with patch('utils.auth_decorators.auth_manager') as mock_decorator_auth, \
             patch('cli.commands.auth_manager') as mock_command_auth:

            # Setup authentication mocks
            mock_decorator_auth.require_authentication.return_value = True
            mock_command_auth.get_current_user.return_value = sales_user

            mock_db_session = MagicMock()
            mock_session_class.return_value = mock_db_session

            # Mock the service to raise PermissionError
            with patch('cli.commands.CustomerService') as mock_service_class:
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.list_customers.side_effect = Exception("Permission denied")

                # Capture output
                captured_output = StringIO()
                sys.stdout = captured_output

                # Execute
                list_customers_command()

                # Restore stdout
                sys.stdout = sys.__stdout__
                output = captured_output.getvalue()

                # Verify error handling
                assert "❌ Erreur" in output or "Permission denied" in output
