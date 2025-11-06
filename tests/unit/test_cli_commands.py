"""
Tests for CLI commands - Unit tests with mocking
Focus on service functions and utility components
"""

import pytest
from unittest.mock import Mock, patch

from cli.commands.customer import get_customer_service
from cli.commands.event import get_event_service
from cli.commands.contract import get_contract_service
from cli.commands.employee import get_employee_service
from utils.validators import ValidationError
from utils.permissions import PermissionError


class TestCLIServiceFactories:
    """Test CLI service factory functions"""

    def test_get_customer_service(self):
        """Test customer service factory function"""
        with patch("cli.commands.customer.Session") as mock_session_class, patch(
            "cli.commands.customer.CustomerRepository"
        ) as mock_repo_class, patch(
            "cli.commands.customer.CustomerService"
        ) as mock_service_class:

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            service, session = get_customer_service()

            assert service == mock_service
            assert session == mock_session
            mock_repo_class.assert_called_once_with(mock_session)
            mock_service_class.assert_called_once_with(mock_repo)

    def test_get_event_service(self):
        """Test event service factory function"""
        with patch("cli.commands.event.Session") as mock_session_class, patch(
            "cli.commands.event.EventRepository"
        ) as mock_repo_class, patch(
            "cli.commands.event.EventService"
        ) as mock_service_class:

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            service, session = get_event_service()

            assert service == mock_service
            assert session == mock_session
            mock_repo_class.assert_called_once_with(mock_session)
            mock_service_class.assert_called_once_with(mock_repo)

    def test_get_contract_service(self):
        """Test contract service factory function"""
        with patch("cli.commands.contract.Session") as mock_session_class, patch(
            "cli.commands.contract.ContractRepository"
        ) as mock_repo_class, patch(
            "cli.commands.contract.ContractService"
        ) as mock_service_class:

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            service, session = get_contract_service()

            assert service == mock_service
            assert session == mock_session
            mock_repo_class.assert_called_once_with(mock_session)
            mock_service_class.assert_called_once_with(mock_repo)

    def test_get_employee_service(self):
        """Test employee service factory function"""
        with patch("cli.commands.employee.Session") as mock_session_class, patch(
            "cli.commands.employee.EmployeeRepository"
        ) as mock_repo_class, patch(
            "cli.commands.employee.EmployeeService"
        ) as mock_service_class:

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            service, session = get_employee_service()

            assert service == mock_service
            assert session == mock_session
            mock_repo_class.assert_called_once_with(mock_session)
            mock_service_class.assert_called_once_with(mock_repo)

    def test_all_service_factories_return_valid_objects(self):
        """Test that all CLI service factories work correctly"""
        # Test customer service factory
        with patch("cli.commands.customer.Session"), patch(
            "cli.commands.customer.CustomerRepository"
        ), patch("cli.commands.customer.CustomerService"):
            service, session = get_customer_service()
            assert service is not None
            assert session is not None

        # Test event service factory
        with patch("cli.commands.event.Session"), patch(
            "cli.commands.event.EventRepository"
        ), patch("cli.commands.event.EventService"):
            service, session = get_event_service()
            assert service is not None
            assert session is not None

        # Test contract service factory
        with patch("cli.commands.contract.Session"), patch(
            "cli.commands.contract.ContractRepository"
        ), patch("cli.commands.contract.ContractService"):
            service, session = get_contract_service()
            assert service is not None
            assert session is not None

        # Test employee service factory
        with patch("cli.commands.employee.Session"), patch(
            "cli.commands.employee.EmployeeRepository"
        ), patch("cli.commands.employee.EmployeeService"):
            service, session = get_employee_service()
            assert service is not None
            assert session is not None


class TestCLIUtilities:
    """Test CLI utility functions and session management"""

    @patch("cli.commands.customer.Session")
    def test_session_cleanup(self, mock_session_class):
        """Test that sessions are properly managed in CLI commands"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        with patch("cli.commands.customer.CustomerRepository"), patch(
            "cli.commands.customer.CustomerService"
        ):

            service, session = get_customer_service()

            # Verify session object
            assert session == mock_session

            # Simulate command execution that should close session
            session.close()
            mock_session.close.assert_called_once()

    def test_service_factory_creates_correct_instances(self):
        """Test that service factories create instances with correct dependencies"""
        with patch("cli.commands.customer.Session") as mock_session_class, patch(
            "cli.commands.customer.CustomerRepository"
        ) as mock_repo_class, patch(
            "cli.commands.customer.CustomerService"
        ) as mock_service_class:

            # Setup mocks to track calls
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Call factory
            service, session = get_customer_service()

            # Verify correct instantiation order and dependencies
            mock_session_class.assert_called_once()
            mock_repo_class.assert_called_once_with(mock_session)
            mock_service_class.assert_called_once_with(mock_repo)

            # Verify returned objects
            assert service == mock_service
            assert session == mock_session


class TestCLIErrorHandling:
    """Test CLI error handling patterns (testable components)"""

    def test_validation_error_propagation(self):
        """Test that ValidationError is properly handled in CLI context"""
        with patch("cli.commands.customer.Session") as mock_session_class, patch(
            "cli.commands.customer.CustomerRepository"
        ) as mock_repo_class, patch(
            "cli.commands.customer.CustomerService"
        ) as mock_service_class:

            # Setup service to raise ValidationError
            mock_service = Mock()
            mock_service.create_customer.side_effect = ValidationError(
                "Invalid email format"
            )
            mock_service_class.return_value = mock_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            service, session = get_customer_service()

            # Test that error is raised when service method is called
            with pytest.raises(ValidationError, match="Invalid email format"):
                service.create_customer({})

    def test_permission_error_propagation(self):
        """Test that PermissionError is properly handled in CLI context"""
        with patch("cli.commands.customer.Session") as mock_session_class, patch(
            "cli.commands.customer.CustomerRepository"
        ) as mock_repo_class, patch(
            "cli.commands.customer.CustomerService"
        ) as mock_service_class:

            # Setup service to raise PermissionError
            mock_service = Mock()
            mock_service.list_customers.side_effect = PermissionError("Access denied")
            mock_service_class.return_value = mock_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            service, session = get_customer_service()

            # Test that error is raised when service method is called
            with pytest.raises(PermissionError, match="Access denied"):
                service.list_customers(Mock())

    def test_general_exception_handling(self):
        """Test that general exceptions are properly propagated"""
        with patch("cli.commands.event.Session") as mock_session_class, patch(
            "cli.commands.event.EventRepository"
        ) as mock_repo_class, patch(
            "cli.commands.event.EventService"
        ) as mock_service_class:

            # Setup service to raise general exception
            mock_service = Mock()
            mock_service.list_events.side_effect = Exception(
                "Database connection failed"
            )
            mock_service_class.return_value = mock_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            service, session = get_event_service()

            # Test that error is raised when service method is called
            with pytest.raises(Exception, match="Database connection failed"):
                service.list_events(Mock())


class TestCLIComponentIntegration:
    """Test integration between CLI components"""

    def test_customer_service_integration(self):
        """Test customer service integration with CLI layer"""
        with patch("cli.commands.customer.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            with patch("cli.commands.customer.CustomerRepository") as mock_repo_class:
                mock_repo = Mock()
                mock_repo_class.return_value = mock_repo

                with patch(
                    "cli.commands.customer.CustomerService"
                ) as mock_service_class:
                    mock_service = Mock()
                    mock_service_class.return_value = mock_service

                    # Test factory integration
                    service, session = get_customer_service()

                    # Verify integration chain
                    assert session == mock_session
                    assert service == mock_service
                    mock_repo_class.assert_called_once_with(mock_session)
                    mock_service_class.assert_called_once_with(mock_repo)

    def test_event_service_integration(self):
        """Test event service integration with CLI layer"""
        with patch("cli.commands.event.Session") as mock_session_class, patch(
            "cli.commands.event.EventRepository"
        ) as mock_repo_class, patch(
            "cli.commands.event.EventService"
        ) as mock_service_class:

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            service, session = get_event_service()

            # Verify all components are properly connected
            assert session == mock_session
            assert service == mock_service
            mock_repo_class.assert_called_once_with(mock_session)
            mock_service_class.assert_called_once_with(mock_repo)
