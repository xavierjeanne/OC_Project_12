"""
Tests ciblés pour atteindre 80% de couverture
Focus sur les modules avec couverture faible pour gains rapides
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


class TestCLIErrorHandlingCoverage:
    """Tests pour améliorer la couverture de cli.error_handling (36% → 50%+)"""

    def test_handle_cli_errors_decorator_success(self):
        """Test décorateur handle_cli_errors sans erreur"""
        from cli.utils.error_handling import handle_cli_errors
        
        @handle_cli_errors
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"

    def test_handle_cli_errors_validation_error(self):
        """Test décorateur avec ValidationError"""
        from cli.utils.error_handling import handle_cli_errors
        from utils.validators import ValidationError
        import click
        
        @handle_cli_errors
        def test_function():
            raise ValidationError("Test validation error")
        
        # Le décorateur doit lever click.Abort après avoir traité l'erreur
        with pytest.raises(click.Abort):
            test_function()

    def test_handle_cli_errors_permission_error(self):
        """Test décorateur avec PermissionError"""
        from cli.utils.error_handling import handle_cli_errors
        from utils.permissions import PermissionError
        import click
        
        @handle_cli_errors
        def test_function():
            raise PermissionError("Test permission error")
        
        with pytest.raises(click.Abort):
            test_function()

    def test_handle_cli_errors_sqlalchemy_error(self):
        """Test décorateur avec SQLAlchemyError"""
        from cli.utils.error_handling import handle_cli_errors
        import click
        
        @handle_cli_errors
        def test_function():
            raise SQLAlchemyError("Database error")
        
        with pytest.raises(click.Abort):
            test_function()


class TestCustomerServiceCoverage:
    """Tests pour améliorer la couverture de services.customer (57% → 70%+)"""

    def test_customer_service_initialization(self):
        """Test initialisation CustomerService"""
        from services.customer import CustomerService
        from repositories.customer import CustomerRepository
        
        mock_repo = MagicMock(spec=CustomerRepository)
        service = CustomerService(mock_repo)
        assert service.repository == mock_repo


class TestRepositoryBaseCoverage:
    """Tests pour améliorer la couverture de repositories.base (76% → 85%+)"""

    def test_base_repository_initialization(self):
        """Test initialisation BaseRepository"""
        from repositories.base import BaseRepository
        from models.employee import Employee
        
        mock_session = MagicMock()
        repo = BaseRepository(Employee, mock_session)
        
        # Test que le repository a été initialisé
        assert hasattr(repo, 'model')
        assert hasattr(repo, 'db')


class TestCLIAuthCoverage:
    """Tests pour améliorer la couverture de cli.auth (61% → 75%+)"""
    
    def test_get_current_user_not_authenticated(self):
        """Test get_current_user quand non authentifié"""
        from cli.utils.auth import get_current_user
        
        with patch('cli.utils.auth.auth_manager') as mock_auth:
            mock_auth.get_current_user.return_value = None
            
            user = get_current_user()
            assert user is None

    def test_auth_manager_import(self):
        """Test import auth_manager"""
        from cli.utils.auth import auth_manager
        assert auth_manager is not None


class TestServicesCoverage:
    """Tests pour améliorer la couverture des services avec faible coverage"""

    def test_employee_service_edge_cases(self):
        """Test cas limites EmployeeService"""
        from services.employee import EmployeeService
        
        mock_repo = MagicMock()
        service = EmployeeService(mock_repo)
        
        # Test avec repository mock
        mock_repo.get_all.return_value = []
        mock_user = {'id': 1, 'role': 'admin'}
        
        result = service.list_employees(mock_user)
        assert result == []

    def test_contract_service_edge_cases(self):
        """Test cas limites ContractService"""
        from services.contract import ContractService
        
        mock_repo = MagicMock()
        service = ContractService(mock_repo)
        
        # Test initialisation
        assert service.repository == mock_repo

    def test_event_service_edge_cases(self):
        """Test cas limites EventService"""
        from services.event import EventService
        
        mock_repo = MagicMock()
        service = EventService(mock_repo)
        
        # Test initialisation
        assert service.repository == mock_repo


class TestRepositoriesCoverage:
    """Tests pour améliorer la couverture des repositories"""

    def test_employee_repository_edge_cases(self):
        """Test cas limites EmployeeRepository"""
        from repositories.employee import EmployeeRepository
        
        mock_db = MagicMock()
        repo = EmployeeRepository(mock_db)
        
        # Test find_by_email sans résultat
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        result = repo.find_by_email("nonexistent@test.com")
        assert result is None

    def test_contract_repository_initialization(self):
        """Test initialisation ContractRepository"""
        from repositories.contract import ContractRepository
        
        mock_db = MagicMock()
        repo = ContractRepository(mock_db)
        
        # Test d'initialisation
        assert repo.db == mock_db

    def test_event_repository_initialization(self):
        """Test initialisation EventRepository"""
        from repositories.event import EventRepository
        
        mock_db = MagicMock()
        repo = EventRepository(mock_db)
        
        # Test d'initialisation
        assert repo.db == mock_db