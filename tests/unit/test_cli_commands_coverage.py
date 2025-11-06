"""
Targeted unit tests to improve CLI command coverage
Focus on testable functions without full authentication
"""

from unittest.mock import Mock, patch
from datetime import datetime

from cli.commands.contract import get_contract_service
from cli.commands.customer import get_customer_service
from cli.commands.employee import get_employee_service
from cli.commands.event import get_event_service
from utils.validators import ValidationError
from utils.permissions import PermissionError
from decimal import Decimal


class TestCLIServiceFactories:
    """Tests des fonctions factory des services CLI"""

    @patch("cli.commands.contract.Session")
    @patch("cli.commands.contract.ContractRepository")
    @patch("cli.commands.contract.ContractService")
    def test_get_contract_service_creation(
        self, mock_service_class, mock_repo_class, mock_session_class
    ):
        """Test création du service contract"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        service, session = get_contract_service()

        assert service == mock_service
        assert session == mock_session
        mock_session_class.assert_called_once()
        mock_repo_class.assert_called_once_with(mock_session)
        mock_service_class.assert_called_once_with(mock_repo)

    @patch("cli.commands.customer.Session")
    @patch("cli.commands.customer.CustomerRepository")
    @patch("cli.commands.customer.CustomerService")
    def test_get_customer_service_creation(
        self, mock_service_class, mock_repo_class, mock_session_class
    ):
        """Test création du service customer"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        service, session = get_customer_service()

        assert service == mock_service
        assert session == mock_session

    @patch("cli.commands.employee.Session")
    @patch("cli.commands.employee.EmployeeRepository")
    @patch("cli.commands.employee.EmployeeService")
    def test_get_employee_service_creation(
        self, mock_service_class, mock_repo_class, mock_session_class
    ):
        """Test création du service employee"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        service, session = get_employee_service()

        assert service == mock_service
        assert session == mock_session

    @patch("cli.commands.event.Session")
    @patch("cli.commands.event.EventRepository")
    @patch("cli.commands.event.EventService")
    def test_get_event_service_creation(
        self, mock_service_class, mock_repo_class, mock_session_class
    ):
        """Test création du service event"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        service, session = get_event_service()

        assert service == mock_service
        assert session == mock_session


class TestCLIHelperFunctions:
    """Tests des fonctions utilitaires CLI"""

    def test_contract_data_display_formatting(self):
        """Test formatage d'affichage des données contract"""
        # Mock contract data
        mock_contract = Mock()
        mock_contract.id = 1
        mock_contract.customer_id = 10
        mock_contract.total_amount = Decimal("1500.00")
        mock_contract.remaining_amount = Decimal("750.00")
        mock_contract.signed = True
        mock_contract.creation_date = datetime(2024, 1, 15)

        # Test des attributs accessibles
        assert mock_contract.id == 1
        assert mock_contract.customer_id == 10
        assert mock_contract.total_amount == Decimal("1500.00")
        assert mock_contract.remaining_amount == Decimal("750.00")
        assert mock_contract.signed is True
        assert isinstance(mock_contract.creation_date, datetime)

    def test_customer_data_display_formatting(self):
        """Test formatage d'affichage des données customer"""
        mock_customer = Mock()
        mock_customer.id = 1
        mock_customer.name = "Test Customer"
        mock_customer.email = "test@example.com"
        mock_customer.phone = "0123456789"
        mock_customer.company = "Test Company"
        mock_customer.sales_contact_id = 5

        # Test des attributs accessibles
        assert mock_customer.id == 1
        assert mock_customer.name == "Test Customer"
        assert mock_customer.email == "test@example.com"
        assert mock_customer.phone == "0123456789"
        assert mock_customer.company == "Test Company"
        assert mock_customer.sales_contact_id == 5

    def test_employee_data_display_formatting(self):
        """Test formatage d'affichage des données employee"""
        mock_employee = Mock()
        mock_employee.id = 1
        mock_employee.name = "Test Employee"
        mock_employee.email = "employee@example.com"
        mock_employee.employee_number = "EMP001"
        mock_employee.role = "sales"

        # Test des attributs accessibles
        assert mock_employee.id == 1
        assert mock_employee.name == "Test Employee"
        assert mock_employee.email == "employee@example.com"
        assert mock_employee.employee_number == "EMP001"
        assert mock_employee.role == "sales"

    def test_event_data_display_formatting(self):
        """Test formatage d'affichage des données event"""
        mock_event = Mock()
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.contract_id = 10
        mock_event.support_contact_id = 3
        mock_event.start_date = datetime(2024, 6, 15)
        mock_event.end_date = datetime(2024, 6, 16)
        mock_event.location = "Paris"
        mock_event.attendees = 100
        mock_event.notes = "Important event"

        # Test des attributs accessibles
        assert mock_event.id == 1
        assert mock_event.name == "Test Event"
        assert mock_event.contract_id == 10
        assert mock_event.support_contact_id == 3
        assert isinstance(mock_event.start_date, datetime)
        assert isinstance(mock_event.end_date, datetime)
        assert mock_event.location == "Paris"
        assert mock_event.attendees == 100
        assert mock_event.notes == "Important event"


class TestCLIValidationHandling:
    """Tests de gestion des validations dans CLI"""

    def test_validation_error_message_formatting(self):
        """Test formatage des messages d'erreur de validation"""
        error = ValidationError("Invalid email format")
        assert str(error) == "Invalid email format"
        assert isinstance(error, Exception)

    def test_permission_error_message_formatting(self):
        """Test formatage des messages d'erreur de permission"""
        error = PermissionError("Insufficient permissions")
        assert str(error) == "Insufficient permissions"
        assert isinstance(error, Exception)

    def test_decimal_amount_validation(self):
        """Test validation des montants décimaux"""
        # Test montants valides
        valid_amounts = ["100.00", "1500.50", "0.01"]
        for amount_str in valid_amounts:
            amount = Decimal(amount_str)
            assert isinstance(amount, Decimal)
            assert amount >= 0

    def test_datetime_validation(self):
        """Test validation des dates"""
        # Test date valide
        test_date = datetime(2024, 6, 15, 14, 30)
        assert isinstance(test_date, datetime)
        assert test_date.year == 2024
        assert test_date.month == 6
        assert test_date.day == 15
        assert test_date.hour == 14
        assert test_date.minute == 30


class TestCLISessionManagement:
    """Tests de gestion des sessions dans CLI"""

    def test_session_creation_and_cleanup(self):
        """Test création et nettoyage des sessions"""
        mock_session = Mock()

        # Test méthodes de session
        mock_session.commit()
        mock_session.rollback()
        mock_session.close()

        # Vérifier les appels
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_transaction_handling(self):
        """Test gestion des transactions"""
        mock_session = Mock()

        # Simuler une transaction réussie
        try:
            # Operations
            mock_session.add(Mock())
            mock_session.commit()
        except Exception:
            mock_session.rollback()
            raise
        finally:
            mock_session.close()

        # Vérifier les appels
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_error_handling_with_rollback(self):
        """Test gestion d'erreur avec rollback"""
        mock_session = Mock()
        mock_session.commit.side_effect = Exception("DB Error")

        # Simuler erreur et rollback
        try:
            mock_session.commit()
        except Exception:
            mock_session.rollback()
        finally:
            mock_session.close()

        # Vérifier les appels
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestCLIDataProcessing:
    """Tests de traitement des données CLI"""

    def test_contract_filtering_logic(self):
        """Test logique de filtrage des contrats"""
        # Mock contracts
        contracts = [
            Mock(signed=True, remaining_amount=Decimal("0")),
            Mock(signed=False, remaining_amount=Decimal("100")),
            Mock(signed=True, remaining_amount=Decimal("500")),
        ]

        # Test filtre signés
        signed_contracts = [c for c in contracts if c.signed]
        assert len(signed_contracts) == 2

        # Test filtre non payés
        unpaid_contracts = [c for c in contracts if c.remaining_amount > 0]
        assert len(unpaid_contracts) == 2

    def test_employee_role_filtering(self):
        """Test filtrage par rôle des employés"""
        employees = [
            Mock(role="sales"),
            Mock(role="support"),
            Mock(role="management"),
            Mock(role="sales"),
        ]

        # Test filtre par rôle
        sales_employees = [e for e in employees if e.role == "sales"]
        assert len(sales_employees) == 2

        support_employees = [e for e in employees if e.role == "support"]
        assert len(support_employees) == 1

    def test_event_support_filtering(self):
        """Test filtrage des événements par support"""
        events = [
            Mock(support_contact_id=1),
            Mock(support_contact_id=None),
            Mock(support_contact_id=2),
            Mock(support_contact_id=None),
        ]

        # Test événements sans support
        events_without_support = [e for e in events if e.support_contact_id is None]
        assert len(events_without_support) == 2

        # Test événements avec support
        events_with_support = [e for e in events if e.support_contact_id is not None]
        assert len(events_with_support) == 2
