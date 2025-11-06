"""
Tests for ContractService with role-based access control
Tests the list_contracts functionality with different user roles
"""

import pytest
from unittest.mock import MagicMock, patch
from services.contract import ContractService
from utils.permissions import Permission


class TestContractServiceRoleBasedAccess:
    """Test suite for ContractService role-based access control"""

    @pytest.fixture
    def mock_repository(self):
        """Mock contract repository"""
        return MagicMock()

    @pytest.fixture
    def contract_service(self, mock_repository):
        """Create ContractService with mocked repository"""
        return ContractService(mock_repository)

    @pytest.fixture
    def admin_user(self):
        """Admin user fixture"""
        return {"id": 1, "name": "Admin User", "role": "admin", "role_id": 4}

    @pytest.fixture
    def management_user(self):
        """Management user fixture"""
        return {"id": 2, "name": "Manager User", "role": "management", "role_id": 3}

    @pytest.fixture
    def sales_user(self):
        """Sales user fixture"""
        return {"id": 3, "name": "Sales User", "role": "sales", "role_id": 1}

    @pytest.fixture
    def support_user(self):
        """Support user fixture"""
        return {"id": 4, "name": "Support User", "role": "support", "role_id": 2}

    @patch("services.contract.require_permission")
    def test_list_contracts_admin_sees_all(
        self, mock_require_permission, contract_service, mock_repository, admin_user
    ):
        """Test that admin users see all contracts"""
        # Setup
        mock_contracts = [MagicMock(), MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_contracts

        # Execute
        result = contract_service.list_contracts(admin_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            admin_user, Permission.READ_CONTRACT
        )
        mock_repository.get_all.assert_called_once()
        assert result == mock_contracts

    @patch("services.contract.require_permission")
    def test_list_contracts_management_sees_all(
        self,
        mock_require_permission,
        contract_service,
        mock_repository,
        management_user,
    ):
        """Test that management users see all contracts"""
        # Setup
        mock_contracts = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_contracts

        # Execute
        result = contract_service.list_contracts(management_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            management_user, Permission.READ_CONTRACT
        )
        mock_repository.get_all.assert_called_once()
        assert result == mock_contracts

    @patch("services.contract.require_permission")
    def test_list_contracts_support_sees_all(
        self, mock_require_permission, contract_service, mock_repository, support_user
    ):
        """Test that support users see all contracts"""
        # Setup
        mock_contracts = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_contracts

        # Execute
        result = contract_service.list_contracts(support_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            support_user, Permission.READ_CONTRACT
        )
        mock_repository.get_all.assert_called_once()
        assert result == mock_contracts

    @patch("services.contract.require_permission")
    def test_list_contracts_sales_sees_all_contracts(
        self, mock_require_permission, contract_service, mock_repository, sales_user
    ):
        """Test that sales users now see ALL contracts (conformité)"""
        # Setup
        mock_contracts = [MagicMock(), MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_contracts

        # Execute
        result = contract_service.list_contracts(sales_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            sales_user, Permission.READ_CONTRACT
        )
        mock_repository.get_all.assert_called_once()
        mock_repository.find_by_sales_contact.assert_not_called()
        assert result == mock_contracts

    @patch("services.contract.require_permission")
    def test_list_contracts_unknown_role_sees_all_contracts(
        self, mock_require_permission, contract_service, mock_repository
    ):
        """Test that even unknown roles now see ALL contracts (conformité)"""
        # Setup
        unknown_user = {"id": 5, "name": "Unknown", "role": "unknown"}
        mock_contracts = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_contracts

        # Execute
        result = contract_service.list_contracts(unknown_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            unknown_user, Permission.READ_CONTRACT
        )
        mock_repository.get_all.assert_called_once()
        mock_repository.find_by_sales_contact.assert_not_called()
        assert result == mock_contracts
