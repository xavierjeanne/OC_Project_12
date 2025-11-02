"""
Tests pour les opérations de création et modification
Valide les fonctionnalités selon les exigences prérequis
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from services.employee import EmployeeService
from services.customer import CustomerService
from services.contract import ContractService
from services.event import EventService
from utils.validators import ValidationError


class TestEmployeeOperations:
    """Tests pour les opérations Employee"""

    @pytest.fixture
    def employee_service(self):
        """Mock repository et service"""
        mock_repo = MagicMock()
        return EmployeeService(mock_repo)

    @pytest.fixture
    def management_user(self):
        """Utilisateur management"""
        return {
            'id': 1,
            'name': 'Manager',
            'role': 'management',
            'role_id': 3
        }

    @pytest.fixture
    def sales_user(self):
        """Utilisateur sales"""
        return {
            'id': 2,
            'name': 'Sales Person',
            'role': 'sales',
            'role_id': 1
        }

    @patch('services.employee.require_permission')
    def test_create_employee_success(self,
                                     mock_permission,
                                     employee_service,
                                     management_user):
        """Test création d'employé avec validation complète (inclut mot de passe)"""
        employee_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'employee_number': 'EMP001',
            'role_id': 1,
            'password': 'SecurePass123!'
        }

        # Mock return value for successful creation
        mock_employee = MagicMock()
        mock_employee.id = 1
        employee_service.repository.create.return_value = mock_employee

        # Call the actual method
        _result = employee_service.create_employee(employee_data, management_user)

        # Vérifications
        mock_permission.assert_called_once()
        employee_service.repository.create.assert_called_once()

        # Vérifier que les données sont correctement validées
        created_employee_data = employee_service.repository.create.call_args[0][0]
        assert created_employee_data['name'] == 'John Doe'
        assert created_employee_data['email'] == 'john.doe@example.com'
        assert created_employee_data['employee_number'] == 'EMP001'
        assert created_employee_data['role_id'] == 1

    @patch('services.employee.require_permission')
    def test_create_employee_invalid_email(self,
                                           mock_permission,
                                           employee_service,
                                           management_user):
        """Test création d'employé avec email invalide"""
        employee_data = {
            'name': 'John Doe',
            'email': 'invalid-email',
            'employee_number': 'EMP001',
            'role_id': 1
        }

        with pytest.raises(ValidationError, match="Email"):
            employee_service.create_employee(
                employee_data, management_user
                )

    @patch('services.employee.require_permission')
    def test_update_employee_role_change(self,
                                         mock_permission,
                                         employee_service,
                                         management_user):
        """Test modification du rôle d'un employé"""
        employee_id = 1
        update_data = {
            'role_id': 2,
            'name': 'John Doe Updated',
            'email': 'john.doe.updated@example.com',
            'employee_number': 'EMP001'
        }

        # Mock existing employee
        mock_existing = MagicMock()
        mock_existing.id = employee_id
        mock_existing.role_id = 1
        employee_service.repository.get_by_id.return_value = mock_existing

        # Mock updated employee return
        mock_updated = MagicMock()
        mock_updated.role_id = 2
        employee_service.repository.update.return_value = mock_updated

        # Call the actual method
        _result = employee_service.update_employee(
            employee_id, update_data, management_user
        )

        # Vérifications
        mock_permission.assert_called_once()
        employee_service.repository.update.assert_called_once()

        # Vérifier que le rôle a été changé - second argument est les données
        updated_employee_data = employee_service.repository.update.call_args[0][1]
        assert updated_employee_data['role_id'] == 2


class TestContractOperations:
    """Tests pour les opérations Contract"""

    @pytest.fixture
    def contract_service(self):
        """Mock repository et service"""
        mock_repo = MagicMock()
        return ContractService(mock_repo)

    @pytest.fixture
    def sales_user(self):
        """Utilisateur sales"""
        return {
            'id': 2,
            'name': 'Sales Person',
            'role': 'sales',
            'role_id': 1
        }

    @patch('services.contract.require_permission')
    def test_create_contract_with_validation(self,
                                             mock_permission,
                                             contract_service,
                                             sales_user):

        """Test création de contrat avec validation des montants"""
        contract_data = {
            'customer_id': '1',
            'total_amount': 5000.0,
            'remaining_amount': 3000.0,
            'signed': False
        }

        # Mock successful creation
        mock_contract = MagicMock()
        mock_contract.id = 1
        contract_service.repository.create.return_value = mock_contract

        # Call the actual method
        _result = contract_service.create_contract(contract_data, sales_user)

        # Vérifications
        mock_permission.assert_called_once()
        contract_service.repository.create.assert_called_once()

        # Vérifier que les données sont correctement validées
        created_contract_data = contract_service.repository.create.call_args[0][0]
        assert created_contract_data['customer_id'] == 1
        assert created_contract_data['total_amount'] == 5000.0
        assert created_contract_data['remaining_amount'] == 3000.0
        assert created_contract_data['sales_contact_id'] == 2

    @patch('services.contract.require_permission')
    def test_create_contract_invalid_amounts(self,
                                             mock_permission,
                                             contract_service,
                                             sales_user):
        """Test création de contrat avec montant restant > total"""
        contract_data = {
            'customer_id': '1',
            'total_amount': 3000.0,
            'remaining_amount': 5000.0,  # Invalide
            'signed': False
        }

        with pytest.raises(ValidationError, match="cannot be greater than"):
            contract_service.create_contract(contract_data, sales_user)

    @patch('services.contract.require_permission')
    def test_update_contract_all_fields(self,
                                        mock_permission,
                                        contract_service,
                                        sales_user):
        """Test modification de tous les champs d'un contrat"""
        contract_id = 1
        update_data = {
            'customer_id': '2',  # String required
            'total_amount': 8000.0,
            'remaining_amount': 4000.0,
            'signed': True
        }

        # Mock existing contract
        mock_existing = MagicMock()
        mock_existing.id = contract_id
        mock_existing.sales_contact_id = 2
        contract_service.repository.get_by_id.return_value = mock_existing

        # Mock updated contract
        mock_updated = MagicMock()
        mock_updated.customer_id = 2
        mock_updated.signed = True
        contract_service.repository.update.return_value = mock_updated

        # Call the actual method
        _result = contract_service.update_contract(contract_id, update_data, sales_user)

        # Vérifications
        mock_permission.assert_called_once()
        contract_service.repository.update.assert_called_once()

        # Vérifier que les relations sont mises à jour - second argument est les données
        updated_contract_data = contract_service.repository.update.call_args[0][1]
        assert updated_contract_data['customer_id'] == 2
        assert updated_contract_data['signed'] is True


class TestEventOperations:
    """Tests pour les opérations Event"""

    @pytest.fixture
    def event_service(self):
        """Mock repository et service"""
        mock_repo = MagicMock()
        return EventService(mock_repo)

    @pytest.fixture
    def support_user(self):
        """Utilisateur support"""
        return {
            'id': 3,
            'name': 'Support Person',
            'role': 'support',
            'role_id': 2
        }

    @patch('services.event.require_permission')
    def test_create_event_with_dates(self,
                                     mock_permission,
                                     event_service,
                                     support_user):
        """Test création d'événement avec validation des dates"""
        event_data = {
            'name': 'Conference 2024',
            'customer_id': '1',
            'date_start': '2024-06-01',
            'date_end': '2024-06-03',
            'attendees': 100,
            'location': 'Conference Center'
        }

        # Mock successful creation
        mock_event = MagicMock()
        mock_event.id = 1
        event_service.repository.create.return_value = mock_event

        # Call the actual method
        _result = event_service.create_event(event_data, support_user)

        # Vérifications
        mock_permission.assert_called_once()
        event_service.repository.create.assert_called_once()

        # Vérifier que les données sont correctement validées
        created_event_data = event_service.repository.create.call_args[0][0]
        assert created_event_data['name'] == 'Conference 2024'
        assert created_event_data['attendees'] == 100
        assert created_event_data['support_contact_id'] == 3

    @patch('services.event.require_permission')
    def test_create_event_invalid_dates(self,
                                        mock_permission,
                                        event_service,
                                        support_user):
        """Test création d'événement avec dates invalides"""
        event_data = {
            'name': 'Conference 2024',
            'customer_id': '1',
            'date_start': '2024-06-03',
            'date_end': '2024-06-01',  # Fin avant début
        }

        with pytest.raises(ValidationError, match="cannot be before"):
            event_service.create_event(event_data, support_user)

    @patch('services.event.require_permission')
    def test_update_event_relations(self,
                                    mock_permission,
                                    event_service,
                                    support_user):
        """Test modification des relations d'un événement"""
        event_id = 1
        update_data = {
            'customer_id': '2',  # String required
            'contract_id': '3',  # String required
            'name': 'Updated Event',
            'attendees': 150
        }

        # Mock existing event
        mock_existing = MagicMock()
        mock_existing.id = event_id
        mock_existing.support_contact_id = 3
        event_service.repository.get_by_id.return_value = mock_existing

        # Mock updated event
        mock_updated = MagicMock()
        mock_updated.customer_id = 2
        mock_updated.contract_id = 3
        event_service.repository.update.return_value = mock_updated

        # Call the actual method
        _result = event_service.update_event(event_id, update_data, support_user)

        # Vérifications
        mock_permission.assert_called_once()
        event_service.repository.update.assert_called_once()

        # Vérifier que les relations sont mises à jour - second argument est les données
        updated_event_data = event_service.repository.update.call_args[0][1]
        assert updated_event_data['customer_id'] == 2
        assert updated_event_data['contract_id'] == 3


class TestCustomerOperations:
    """Tests pour les opérations Customer"""

    @pytest.fixture
    def customer_service(self):
        """Mock repository et service"""
        mock_repo = MagicMock()
        return CustomerService(mock_repo)

    @pytest.fixture
    def management_user(self):
        """Utilisateur management"""
        return {
            'id': 1,
            'name': 'Manager',
            'role': 'management',
            'role_id': 3
        }

    @patch('services.customer.require_permission')
    def test_create_customer_with_sales_assignment(self,
                                                   mock_permission,
                                                   customer_service,
                                                   management_user):
        """Test création de client avec assignation commerciale"""
        customer_data = {
            'full_name': 'John Smith',
            'email': 'john.smith@example.com',
            'phone': '+33123456789',
            'company_name': 'Smith Corp',
            'sales_contact_id': 5
        }

        # Mock successful creation
        mock_customer = MagicMock()
        mock_customer.id = 1
        customer_service.repository.create.return_value = mock_customer

        # Call the actual method
        _result = customer_service.create_customer(customer_data, management_user)

        # Vérifications
        mock_permission.assert_called_once()
        customer_service.repository.create.assert_called_once()

        # Vérifier que l'assignation est respectée
        created_customer_data = customer_service.repository.create.call_args[0][0]
        assert created_customer_data['full_name'] == 'John Smith'
        assert created_customer_data['sales_contact_id'] == 5  # Assigné par management

    @patch('services.customer.require_permission')
    def test_update_customer_email_validation(self,
                                              mock_permission,
                                              customer_service,
                                              management_user):
        """Test modification de client avec validation email"""
        customer_data = {
            'full_name': 'John Smith',
            'email': 'invalid.email',  # Email invalide
            'phone': '+33123456789',
            'company_name': 'ABC Corp'
        }

        with pytest.raises(ValidationError, match="Email"):
            customer_service.update_customer(1, customer_data, management_user)


class TestValidationIntegration:
    """Tests d'intégration pour la validation"""

    def test_positive_amount_validation(self):
        """Test validation des montants positifs"""
        from utils.validators import validate_positive_amount

        # Cas valides
        assert validate_positive_amount(100.0) == 100.0
        assert validate_positive_amount("50.5") == 50.5

        # Cas invalides
        with pytest.raises(ValidationError):
            validate_positive_amount(0)

        with pytest.raises(ValidationError):
            validate_positive_amount(-10)

    def test_date_validation(self):
        """Test validation des dates"""
        from utils.validators import validate_date

        # Cas valides
        result = validate_date("2024-06-01")
        assert isinstance(result, datetime)
        assert result.year == 2024

        # Format DD/MM/YYYY
        result = validate_date("15/06/2024")
        assert result.month == 6
        assert result.day == 15

        # Cas invalides
        with pytest.raises(ValidationError):
            validate_date("invalid-date")
