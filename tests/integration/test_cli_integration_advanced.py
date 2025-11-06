"""
Integration tests for CLI with full system mocking
Bypasses authentication issues by mocking at system level
"""

from click.testing import CliRunner
from unittest.mock import patch, Mock
from datetime import datetime
from decimal import Decimal


class TestCLIIntegrationWithMocking:
    """integration tests for CLI with system-level mocking"""

    def setup_method(self):
        """Setup for each test"""
        self.runner = CliRunner()

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.contract.get_contract_service")
    def test_contract_list_integration_success(
        self, mock_get_service, mock_auth_manager
    ):
        """integration test: successful contract listing"""
        # Setup auth manager to bypass authentication
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "management"
        mock_employee.id = 1
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service mock
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)

        # Mock contracts data
        mock_contract = Mock()
        mock_contract.id = 1
        mock_contract.customer_id = 10
        mock_contract.total_amount = Decimal("1000.00")
        mock_contract.remaining_amount = Decimal("500.00")
        mock_contract.signed = True
        mock_contract.creation_date = datetime(2024, 1, 15)

        mock_service.list_contracts.return_value = [mock_contract]

        # Import and test after setting up mocks
        from cli.commands.contract import contract_group

        # Test the command
        result = self.runner.invoke(contract_group, ["list"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        # VVerifications
        assert result.exit_code == 0
        assert "Contract List" in result.output
        mock_service.list_contracts.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.contract.get_contract_service")
    def test_contract_list_with_filters(self, mock_get_service, mock_auth_manager):
        """integration test: contract listing with filters"""
        # Setup auth
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "sales"
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service avec repository
        mock_service = Mock()
        mock_session = Mock()
        mock_repository = Mock()
        mock_service.repository = mock_repository
        mock_get_service.return_value = (mock_service, mock_session)

        # Mock contracts avec balance
        mock_contract = Mock()
        mock_contract.id = 1
        mock_contract.customer_id = 10
        mock_contract.total_amount = Decimal("1500.00")
        mock_contract.remaining_amount = Decimal("750.00")
        mock_contract.signed = True
        mock_contract.creation_date = datetime(2024, 2, 1)

        mock_repository.find_with_balance.return_value = [mock_contract]

        from cli.commands.contract import contract_group

        # Test avec filtre --unpaid
        result = self.runner.invoke(contract_group, ["list", "--unpaid"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 0
        mock_repository.find_with_balance.assert_called_once()

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.customer.get_customer_service")
    def test_customer_list_integration(self, mock_get_service, mock_auth_manager):
        """integration test: customer listing"""
        # Setup auth
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "sales"
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)

        # Mock customer data - return an empty list to simplify
        mock_service.list_customers.return_value = []

        from cli.commands.customer import customer_group

        result = self.runner.invoke(customer_group, ["list"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 0
        assert "Customer List" in result.output
        mock_service.list_customers.assert_called_once()

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.employee.get_employee_service")
    def test_employee_list_management_access(self, mock_get_service, mock_auth_manager):
        """integration test: employee listing with management access"""
        # Setup auth pour management
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "management"
        mock_employee.id = 1
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)

        # Mock employee data
        mock_emp = Mock()
        mock_emp.id = 2
        mock_emp.name = "John Doe"
        mock_emp.email = "john@example.com"
        mock_emp.employee_number = "EMP002"
        mock_emp.role = "sales"

        mock_service.list_employees.return_value = [mock_emp]

        from cli.commands.employee import employee_group

        result = self.runner.invoke(employee_group, ["list"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 0
        assert "Employee List" in result.output
        mock_service.list_employees.assert_called_once()

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.event.get_event_service")
    def test_event_list_support_access(self, mock_get_service, mock_auth_manager):
        """Integration test: event listing with support access"""
        # Setup auth pour support
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "support"
        mock_employee.id = 3
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)

        # Mock event data
        mock_event = Mock()
        mock_event.id = 1
        mock_event.name = "Conference 2024"
        mock_event.contract_id = 5
        mock_event.support_contact_id = 3
        mock_event.start_date = datetime(2024, 6, 15)
        mock_event.end_date = datetime(2024, 6, 16)
        mock_event.location = "Paris"
        mock_event.attendees = 150
        mock_event.notes = "Annual conference"

        mock_service.list_events.return_value = [mock_event]

        from cli.commands.event import event_group

        result = self.runner.invoke(event_group, ["list"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 0
        assert "Event List" in result.output
        mock_service.list_events.assert_called_once()


class TestCLIErrorHandlingIntegration:
    """Integration tests for CLI error handling"""

    def setup_method(self):
        self.runner = CliRunner()

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.contract.get_contract_service")
    def test_validation_error_handling(self, mock_get_service, mock_auth_manager):
        """Test validation error handling"""
        # Setup auth
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "sales"
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service with validation error
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)

        from utils.validators import ValidationError

        mock_service.create_contract.side_effect = ValidationError(
            "Invalid customer ID"
        )

        from cli.commands.contract import contract_group

        result = self.runner.invoke(
            contract_group,
            ["create", "--customer-id", "999", "--total-amount", "1000.00"],
        )

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 1
        assert "Invalid customer ID" in result.output

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.customer.get_customer_service")
    def test_permission_error_handling(self, mock_get_service, mock_auth_manager):
        """Test permission error handling"""
        # Setup auth with user lacking permissions
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "support"  # Support cannot create customers
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service with permission error
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)

        from utils.permissions import PermissionError

        mock_service.create_customer.side_effect = PermissionError(
            "Insufficient permissions"
        )

        from cli.commands.customer import customer_group

        result = self.runner.invoke(
            customer_group,
            [
                "create",
                "--contact-name",
                "Test Customer",
                "--email",
                "test@example.com",
                "--phone",
                "0123456789",
            ],
        )

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 1
        assert "Aborted" in result.output

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.contract.get_contract_service")
    def test_database_error_handling(self, mock_get_service, mock_auth_manager):
        """Test database error handling"""
        # Setup auth
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "management"
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service with DB error
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)
        mock_service.list_contracts.side_effect = Exception(
            "Database connection failed"
        )

        from cli.commands.contract import contract_group

        result = self.runner.invoke(contract_group, ["list"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        # The exit code can be 0 even with a handled error
        assert (
            "Database connection failed" in result.output
            or "error" in result.output.lower()
        )


class TestCLIAuthenticationFlow:
    """Integration tests for CLI authentication flow"""

    def setup_method(self):
        self.runner = CliRunner()

    @patch("cli.utils.auth.auth_manager")
    def test_authentication_required_message(self, mock_auth_manager):
        """Test authentication required message"""
        # Setup auth to deny access
        mock_auth_manager.require_authentication.return_value = False

        from cli.commands.contract import contract_group

        result = self.runner.invoke(contract_group, ["list"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 1
        assert (
            "Authentication required" in result.output
            or "login" in result.output.lower()
        )

    @patch("cli.utils.auth.auth_manager")
    @patch("cli.commands.contract.get_contract_service")
    def test_successful_authentication_flow(self, mock_get_service, mock_auth_manager):
        """Test successful authentication flow"""
        # Setup auth réussie
        mock_auth_manager.require_authentication.return_value = True
        mock_employee = Mock()
        mock_employee.role = "management"
        mock_employee.id = 1
        mock_employee.name = "Admin User"
        mock_auth_manager.get_current_user.return_value = mock_employee

        # Setup service
        mock_service = Mock()
        mock_session = Mock()
        mock_get_service.return_value = (mock_service, mock_session)
        mock_service.list_contracts.return_value = []

        from cli.commands.contract import contract_group

        result = self.runner.invoke(contract_group, ["list"])

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert result.exit_code == 0
        # Check that authentication was called
        mock_auth_manager.require_authentication.assert_called_once()
        mock_auth_manager.get_current_user.assert_called()
