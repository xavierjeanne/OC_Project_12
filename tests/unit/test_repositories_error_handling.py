"""
Tests to improve repository coverage
Tests error cases and exceptions
"""

import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from repositories.contract import ContractRepository
from repositories.employee import EmployeeRepository
from repositories.event import EventRepository


class TestRepositoryErrorHandling:
    """Test error handling in repositories"""

    def test_contract_find_signed_error(self, mock_session):
        """Test error handling in find_signed"""
        repo = ContractRepository(mock_session)

        # Mock filter_by to raise an exception
        with patch.object(repo, "filter_by", side_effect=SQLAlchemyError("DB Error")):
            with pytest.raises(SQLAlchemyError):
                repo.find_signed()

    def test_contract_find_unsigned_error(self, mock_session):
        """Test error handling in find_unsigned"""
        repo = ContractRepository(mock_session)

        with patch.object(repo, "filter_by", side_effect=SQLAlchemyError("DB Error")):
            with pytest.raises(SQLAlchemyError):
                repo.find_unsigned()

    def test_contract_find_with_balance_error(self, mock_session):
        """Test error handling in find_with_balance"""
        repo = ContractRepository(mock_session)

        # Mock query to raise an exception
        with patch.object(
            mock_session, "query", side_effect=SQLAlchemyError("DB Error")
        ):
            with pytest.raises(SQLAlchemyError):
                repo.find_with_balance()

    def test_employee_find_by_role_error(self, mock_session):
        """Test error handling in find_by_role"""
        repo = EmployeeRepository(mock_session)

        with patch.object(mock_session, "query", side_effect=SQLAlchemyError("DB Error")):
            with pytest.raises(SQLAlchemyError):
                repo.find_by_role("sales")

    def test_event_find_by_support_contact_error(self, mock_session):
        """Test error handling in find_by_support_contact"""
        repo = EventRepository(mock_session)

        with patch.object(repo, "filter_by", side_effect=SQLAlchemyError("DB Error")):
            with pytest.raises(SQLAlchemyError):
                repo.find_by_support_contact(1)

    def test_event_find_without_support_error(self, mock_session):
        """Test error handling in find_without_support"""
        repo = EventRepository(mock_session)

        with patch.object(
            mock_session, "query", side_effect=SQLAlchemyError("DB Error")
        ):
            with pytest.raises(SQLAlchemyError):
                repo.find_without_support()


class TestRepositoryLogging:
    """Test that logs are emitted correctly"""

    @patch("repositories.contract.logger")
    def test_contract_find_signed_logging(self, mock_logger, mock_session):
        """Test that find_signed emits logs correctly"""
        repo = ContractRepository(mock_session)

        # Test successful logging
        result = repo.find_signed()
        mock_logger.debug.assert_called()

    @patch("repositories.contract.logger")
    def test_contract_find_signed_error_logging(self, mock_logger, mock_session):
        """Test that find_signed logs errors correctly"""
        repo = ContractRepository(mock_session)

        with patch.object(repo, "filter_by", side_effect=SQLAlchemyError("DB Error")):
            with pytest.raises(SQLAlchemyError):
                repo.find_signed()
            mock_logger.error.assert_called()

    @patch("repositories.employee.logger")
    def test_employee_find_by_role_logging(self, mock_logger, mock_session):
        """Test that find_by_role emits logs correctly"""
        repo = EmployeeRepository(mock_session)

        result = repo.find_by_role("sales")
        mock_logger.debug.assert_called()

    @patch("repositories.event.logger")
    def test_event_find_without_support_logging(self, mock_logger, mock_session):
        """Test that find_without_support emits logs correctly"""
        repo = EventRepository(mock_session)

        result = repo.find_without_support()
        mock_logger.debug.assert_called()


class TestRepositoryEdgeCases:
    """Test edge cases"""

    def test_contract_find_with_balance_empty_result(self, mock_session):
        """Test find_with_balance when no contract has a balance"""
        repo = ContractRepository(mock_session)

        # Mock to return an empty list
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = repo.find_with_balance()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_employee_find_by_role_invalid_role(self, mock_session):
        """Test find_by_role with a non-existent role"""
        repo = EmployeeRepository(mock_session)

        # Mock query chain to return empty list - need to mock .order_by as well
        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = repo.find_by_role("invalid_role")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_event_find_by_support_contact_nonexistent(self, mock_session):
        """Test find_by_support_contact with a non-existent ID"""
        repo = EventRepository(mock_session)

        # Mock filter_by to return an empty list
        with patch.object(repo, "filter_by", return_value=[]):
            result = repo.find_by_support_contact(99999)
            assert isinstance(result, list)
            assert len(result) == 0
