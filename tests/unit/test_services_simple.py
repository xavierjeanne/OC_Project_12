"""
Simple service tests focusing on basic functionality
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from models import Employee
from utils.permissions import PermissionError as PermError
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
            "employee_number": "EMP001",
            "role_id": 1,
            "password": "SecurePass123!",
        }

        # Convert mock_management_user to dict format
        management_user_dict = {
            "id": mock_management_user.id,
            "role": mock_management_user.role,
            "name": getattr(mock_management_user, "name", "Manager"),
        }

        service.create_employee(employee_data, management_user_dict)

        assert mock_repo.create.called
        created_employee_data = mock_repo.create.call_args[0][0]
        assert created_employee_data["name"] == "John Doe"
        assert created_employee_data["email"] == "john@test.com"
        assert created_employee_data["employee_number"] == "EMP001"
        assert created_employee_data["role_id"] == 1

    def test_create_employee_as_sales_denied(self, mock_sales_user):
        """Sales cannot create employees"""
        mock_repo = MagicMock()
        service = EmployeeService(mock_repo)

        employee_data = {
            "name": "John Doe",
            "email": "john@test.com",
            "employee_number": "EMP001",
            "role_id": 1,
        }

        # Convert mock_sales_user to dict format
        sales_user_dict = {
            "id": mock_sales_user.id,
            "role": mock_sales_user.role,
            "name": getattr(mock_sales_user, "name", "Sales"),
        }

        with pytest.raises(PermError):
            service.create_employee(employee_data, sales_user_dict)

    @patch("services.employee.require_permission")
    def test_list_employees(self, mock_require_permission):
        """Test listing all employees as management user"""
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [Mock(spec=Employee), Mock(spec=Employee)]
        service = EmployeeService(mock_repo)

        # Management user should see all employees
        management_user = {"id": 1, "role": "management", "name": "Manager"}
        result = service.list_employees(management_user)

        assert len(result) == 2
        mock_repo.get_all.assert_called_once()
        mock_require_permission.assert_called_once()


# === CONTRACT SERVICE TESTS ===


class TestContractService:
    """Tests for ContractService"""

    def test_create_contract_as_sales_denied(self, mock_sales_user):
        """Sales cannot create contracts (corrected permission)"""
        mock_repo = MagicMock()
        service = ContractService(mock_repo)

        contract_data = {
            "customer_id": "100",
            "total_amount": "5000.0",
            "remaining_amount": "5000.0",
        }

        # Convert Mock to dictionary
        sales_user = {"id": 2, "role": "sales", "name": "Sales Rep"}
        
        # Should raise PermissionError
        with pytest.raises(PermError):
            service.create_contract(contract_data, sales_user)

        # Repository should not be called
        assert not mock_repo.create.called

    def test_create_contract_as_support_denied(self, mock_support_user):
        """Support cannot create contracts"""
        mock_repo = MagicMock()
        service = ContractService(mock_repo)

        contract_data = {"customer_id": "100", "total_amount": "5000.0"}

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
        mock_contract_repo = MagicMock()
        
        # Mock signed contract
        mock_contract = MagicMock()
        mock_contract.signed = True
        mock_contract.customer_id = 200
        mock_contract_repo.get_by_id.return_value = mock_contract
        
        service = EventService(mock_repo, mock_contract_repo)
        event_data = {
            "name": "Conference 2025",
            "customer_id": "200",
            "contract_id": "50",
            "location": "Paris",
            "attendees": "100",
        }

        # Convert Mock to dictionary
        sales_user = {"id": 2, "role": "sales", "name": "Sales Rep"}
        service.create_event(event_data, sales_user)
        assert mock_repo.create.called
        created_event_data = mock_repo.create.call_args[0][0]
        assert created_event_data["name"] == "Conference 2025"
        assert created_event_data["customer_id"] == 200
        assert created_event_data["location"] == "Paris"
        assert created_event_data["attendees"] == 100

    def test_create_event_as_support_denied(self, mock_support_user):
        """Support cannot create events"""
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        event_data = {"name": "Conference 2025", "customer_id": "200"}
        with pytest.raises(PermError):
            service.create_event(event_data, mock_support_user)

    def test_update_event_as_support(self, mock_support_user):
        """Support can update events assigned to them"""
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        event_data = {"name": "Conference 2025 Updated", "customer_id": "200"}

        # Convert Mock to dictionary
        support_user = {"id": 3, "role": "support", "name": "Support Rep"}
        
        # Mock existing event assigned to this support user
        mock_existing_event = MagicMock()
        mock_existing_event.support_contact_id = support_user["id"]
        mock_repo.get_by_id.return_value = mock_existing_event
        
        service.update_event(1, event_data, support_user)
        assert mock_repo.update.called
        # Premier argument est l'event_id, second argument est les données
        event_id = mock_repo.update.call_args[0][0]
        updated_event_data = mock_repo.update.call_args[0][1]
        assert event_id == 1
        assert updated_event_data["name"] == "Conference 2025 Updated"

    def test_update_event_as_sales_denied(self, mock_sales_user):
        """Sales cannot update events"""
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        event_data = {"name": "Conference 2025", "customer_id": "200"}
        with pytest.raises(PermError):
            service.update_event(1, event_data, mock_sales_user)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
