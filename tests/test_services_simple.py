"""
Simple service tests focusing on basic functionality
"""

from unittest.mock import MagicMock, Mock

import pytest

from models import Employee
from security.permissions import PermissionError as PermError
from services.contract import ContractService
from services.employee import EmployeeService
from services.event import EventService

# === FIXTURES ===


@pytest.fixture
def mock_sales_user():
    user = Mock(spec=Employee)
    user.id = 1
    user.role = "sales"
    return user


@pytest.fixture
def mock_management_user():
    user = Mock(spec=Employee)
    user.id = 2
    user.role = "management"
    return user


@pytest.fixture
def mock_support_user():
    user = Mock(spec=Employee)
    user.id = 3
    user.role = "support"
    return user


# === EMPLOYEE SERVICE TESTS ===


class TestEmployeeService:
    """Tests for EmployeeService"""

    def test_create_employee_as_management(self, mock_management_user):
        """Management can create employees"""
        mock_repo = MagicMock()
        service = EmployeeService(mock_repo)

        employee_data = {
            "name": "John Doe",
            "email": "john@test.com",
            "role_id": 1
        }

        service.create_employee(employee_data, mock_management_user)

        assert mock_repo.create.called
        created_employee = mock_repo.create.call_args[0][0]
        assert created_employee.name == "John Doe"
        assert created_employee.email == "john@test.com"
        assert created_employee.role_id == 1

    def test_create_employee_as_sales_denied(self, mock_sales_user):
        """Sales cannot create employees"""
        mock_repo = MagicMock()
        service = EmployeeService(mock_repo)

        employee_data = {
            "name": "John Doe",
            "email": "john@test.com",
            "role_id": 1
        }

        with pytest.raises(PermError):
            service.create_employee(employee_data, mock_sales_user)

    def test_list_employees(self):
        """Test listing all employees"""
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = [Mock(spec=Employee), Mock(spec=Employee)]
        service = EmployeeService(mock_repo)

        result = service.list_employees()

        assert len(result) == 2
        mock_repo.list_all.assert_called_once()


# === CONTRACT SERVICE TESTS ===


class TestContractService:
    """Tests for ContractService"""

    def test_create_contract_as_sales(self, mock_sales_user):
        """Sales can create contracts"""
        mock_repo = MagicMock()
        service = ContractService(mock_repo)

        contract_data = {
            "customer_id": "100",
            "total_amount": "5000.0",
            "remaining_amount": "5000.0"
        }

        service.create_contract(contract_data, mock_sales_user)

        assert mock_repo.create.called
        created_contract = mock_repo.create.call_args[0][0]
        assert created_contract.customer_id == 100
        assert created_contract.total_amount == 5000.0
        assert created_contract.sales_contact_id == mock_sales_user.id

    def test_create_contract_as_support_denied(self, mock_support_user):
        """Support cannot create contracts"""
        mock_repo = MagicMock()
        service = ContractService(mock_repo)

        contract_data = {
            "customer_id": "100",
            "total_amount": "5000.0"
        }

        with pytest.raises(PermError):
            service.create_contract(contract_data, mock_support_user)

    def test_delete_contract_as_management(self, mock_management_user):
        """Management can delete contracts"""
        mock_repo = MagicMock()
        mock_repo.delete.return_value = True
        service = ContractService(mock_repo)

        result = service.delete_contract(1, mock_management_user)

        assert result is True
        mock_repo.delete.assert_called_once_with(1)

    def test_delete_contract_as_sales_denied(self, mock_sales_user):
        """Sales cannot delete contracts"""
        mock_repo = MagicMock()
        service = ContractService(mock_repo)
        with pytest.raises(PermError):
            service.delete_contract(1, mock_sales_user)


# === EVENT SERVICE TESTS ===


class TestEventService:
    """Tests for EventService"""

    def test_create_event_as_sales(self, mock_sales_user):
        """Sales can create events"""
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        event_data = {
            "name": "Conference 2025",
            "customer_id": "200",
            "contract_id": "50",
            "location": "Paris",
            "attendees": "100"
        }
        service.create_event(event_data, mock_sales_user)
        assert mock_repo.create.called
        created_event = mock_repo.create.call_args[0][0]
        assert created_event.name == "Conference 2025"
        assert created_event.customer_id == 200
        assert created_event.location == "Paris"
        assert created_event.attendees == 100

    def test_create_event_as_support_denied(self, mock_support_user):
        """Support cannot create events"""
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        event_data = {
            "name": "Conference 2025",
            "customer_id": "200"
        }
        with pytest.raises(PermError):
            service.create_event(event_data, mock_support_user)

    def test_update_event_as_support(self, mock_support_user):
        """Support can update events"""
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        event_data = {
            "name": "Conference 2025 Updated",
            "customer_id": "200"
        }
        service.update_event(1, event_data, mock_support_user)
        assert mock_repo.update.called
        updated_event = mock_repo.update.call_args[0][0]
        assert updated_event.id == 1
        assert updated_event.name == "Conference 2025 Updated"

    def test_update_event_as_sales_denied(self, mock_sales_user):
        """Sales cannot update events"""
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        event_data = {
            "name": "Conference 2025",
            "customer_id": "200"
        }
        with pytest.raises(PermError):
            service.update_event(1, event_data, mock_sales_user)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
