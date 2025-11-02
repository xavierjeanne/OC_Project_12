"""
Tests basiques pour améliorer le coverage des repositories
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from repositories.event import EventRepository
from repositories.contract import ContractRepository
from repositories.employee import EmployeeRepository
from repositories.customer import CustomerRepository


class TestRepositoryBasics:
    """Tests simples pour coverage des repositories"""

    def test_event_repository_find_without_support(self):
        """Test EventRepository.find_without_support"""
        mock_session = Mock()
        mock_query_result = [Mock(), Mock()]
        mock_session.query().filter().all.return_value = mock_query_result
        
        # Mock the logger to avoid len() issue
        with patch('repositories.event.logger'):
            repo = EventRepository(mock_session)
            result = repo.find_without_support()
            
            assert result == mock_query_result
            mock_session.query.assert_called()

    def test_contract_repository_find_with_balance(self):
        """Test ContractRepository.find_with_balance"""
        mock_session = Mock()
        
        # Mock the entire query chain
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        with patch('repositories.contract.logger'):
            repo = ContractRepository(mock_session)
            result = repo.find_with_balance()
            
            assert isinstance(result, list)
            mock_session.query.assert_called()

    @patch('repositories.base.logger')
    def test_employee_repository_find_by_email_none(self, mock_logger):
        """Test EmployeeRepository.find_by_email when not found"""
        mock_session = Mock()
        mock_session.query().filter_by().first.return_value = None
        
        repo = EmployeeRepository(mock_session)
        result = repo.find_by_email("notfound@test.com")
        
        assert result is None
        mock_session.query.assert_called()

    @patch('repositories.base.logger')
    def test_customer_repository_find_by_email_found(self, mock_logger):
        """Test CustomerRepository.find_by_email when found"""
        mock_session = Mock()
        mock_customer = Mock()
        mock_customer.email = "found@test.com"
        mock_session.query().filter_by().first.return_value = mock_customer
        
        repo = CustomerRepository(mock_session)
        result = repo.find_by_email("found@test.com")
        
        assert result == mock_customer
        assert result.email == "found@test.com"

    @patch('repositories.base.logger')
    def test_event_repo_create_success(self, mock_logger):
        """Test EventRepository create method"""
        mock_session = Mock()
        mock_event = Mock()
        mock_event.id = 1
        
        # Mock the Event model creation
        with patch('repositories.event.Event') as mock_event_class:
            mock_event_class.return_value = mock_event
            mock_event_class.__name__ = 'Event'  # Fix the __name__ attribute
            
            repo = EventRepository(mock_session)
            data = {'name': 'Test Event', 'contract_id': 1}
            result = repo.create(data)
            
            mock_event_class.assert_called_once_with(**data)
            mock_session.add.assert_called_once_with(mock_event)
            mock_session.commit.assert_called_once()
            assert result == mock_event

    @patch('repositories.base.logger')  
    def test_contract_repo_update_success(self, mock_logger):
        """Test ContractRepository update method"""
        mock_session = Mock()
        mock_contract = Mock()
        mock_contract.id = 1
        mock_contract.total_amount = Decimal('1000.00')
        
        mock_session.query().filter().first.return_value = mock_contract
        
        repo = ContractRepository(mock_session)
        update_data = {'total_amount': Decimal('1500.00')}
        result = repo.update(1, update_data)
        
        assert mock_contract.total_amount == Decimal('1500.00')
        mock_session.commit.assert_called_once()
        assert result == mock_contract

    @patch('repositories.base.logger')
    def test_employee_repo_get_by_id_found(self, mock_logger):
        """Test EmployeeRepository get_by_id when found"""
        mock_session = Mock()
        mock_employee = Mock()
        mock_employee.id = 1
        mock_session.query().filter().first.return_value = mock_employee
        
        repo = EmployeeRepository(mock_session)
        result = repo.get_by_id(1)
        
        assert result == mock_employee
        assert result.id == 1

    @patch('repositories.base.logger')
    def test_customer_repo_delete_success(self, mock_logger):
        """Test CustomerRepository delete method"""
        mock_session = Mock()
        mock_customer = Mock()
        mock_customer.id = 1
        mock_session.query().filter().first.return_value = mock_customer
        
        repo = CustomerRepository(mock_session)
        result = repo.delete(1)
        
        mock_session.delete.assert_called_once_with(mock_customer)
        mock_session.commit.assert_called_once()
        assert result is True

    @patch('repositories.base.logger')
    def test_repository_error_handling(self, mock_logger):
        """Test error handling in repository"""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")
        
        repo = EventRepository(mock_session)
        
        # The method should raise the exception, not return empty list
        with pytest.raises(Exception, match="Database error"):
            result = repo.get_all()

    def test_repository_get_all_basic(self):
        """Test basic get_all functionality"""
        mock_session = Mock()
        mock_items = [Mock() for _ in range(3)]
        mock_session.query().all.return_value = mock_items
        
        with patch('repositories.base.logger'):
            repo = EventRepository(mock_session)
            result = repo.get_all()
            
            mock_session.query.assert_called()
            assert len(result) == 3