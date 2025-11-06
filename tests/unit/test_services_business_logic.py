"""
Complete tests for Customer and Contract business services
Covers CRUD methods and error handling
"""

import pytest
import unittest.mock
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from services.customer import CustomerService
from services.contract import ContractService
from utils.validators import ValidationError


class TestCustomerServiceComplete:
    """Complete tests for CustomerService - CRUD and validation"""

    def setup_method(self):
        self.mock_repo = Mock()
        self.service = CustomerService(self.mock_repo)

        self.sales_user = {
            "id": 1,
            "role": "sales",
            "employee_number": "EMP001"
        }

        self.management_user = {
            "id": 2,
            "role": "management",
            "employee_number": "EMP002"
        }

    def test_get_customer_delegates_to_repository(self):
        """Test that get_customer properly delegates to repository"""
        # Given
        customer_id = 1
        expected_customer = {"id": 1, "full_name": "John Doe"}
        self.mock_repo.get_by_id.return_value = expected_customer

        # When
        result = self.service.get_customer(customer_id)

        # Then
        assert result == expected_customer
        self.mock_repo.get_by_id.assert_called_once_with(customer_id)

    @patch('services.customer.require_permission')
    def test_create_customer_basic_flow(self, mock_require_permission):
        """Test customer creation - basic flow"""
        # Given
        customer_data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+33123456789",
            "company_name": "ACME Corp"
        }
        expected_customer = {"id": 1, "full_name": "John Doe", "sales_contact_id": 1}
        self.mock_repo.create.return_value = expected_customer

        # When
        result = self.service.create_customer(customer_data, self.sales_user)

        # Then
        mock_require_permission.assert_called_once()
        self.mock_repo.create.assert_called_once()
        assert result == expected_customer

    @patch('services.customer.require_permission')
    def test_create_customer_management_custom_sales_contact(
                                                            self,
                                                            mock_require_permission
                                                            ):
        """Test that management can assign custom sales_contact"""
        # Given
        customer_data = {
            "full_name": "Jane Smith",
            "email": "jane@example.com",
            "sales_contact_id": "5"
        }
        expected_customer = {"id": 2, "full_name": "Jane Smith", "sales_contact_id": 5}
        self.mock_repo.create.return_value = expected_customer

        # When
        result = self.service.create_customer(customer_data, self.management_user)

        # Then
        self.mock_repo.create.assert_called_once()
        call_args = self.mock_repo.create.call_args[0][0]
        assert call_args["sales_contact_id"] == 5

    @patch('services.customer.require_permission')
    def test_create_customer_validation_empty_name_raises_error(
                                                                self,
                                                                mock_require_permission
                                                                ):
        """Test validation: empty name raises error"""
        # Given
        customer_data = {
            "full_name": "",
            "email": "test@example.com"
        }

        # When/Then
        with pytest.raises(ValidationError, match="full_name"):
            self.service.create_customer(customer_data, self.sales_user)

    @patch('services.customer.require_permission')
    def test_create_customer_validation_invalid_email_raises_error(
                                                                self,
                                                                mock_require_permission
                                                                ):
        """Test validation: invalid email raises error"""
        # Given
        customer_data = {
            "full_name": "John Doe",
            "email": "invalid-email"
        }

        # When/Then
        with pytest.raises(ValidationError):
            self.service.create_customer(customer_data, self.sales_user)

    @patch('services.customer.require_permission')
    def test_create_customer_invalid_sales_contact_raises_error(
                                                                self,
                                                                mock_require_permission
                                                                ):
        """Test validation: invalid sales_contact_id raises error"""
        # Given
        customer_data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "sales_contact_id": "not_a_number"
        }

        # When/Then
        with pytest.raises(ValidationError, match="valid integer"):
            self.service.create_customer(customer_data, self.management_user)

    @patch('services.customer.require_permission')
    def test_create_duplicate_email_raises_validation_error(
                                                            self,
                                                            mock_require_permission
                                                            ):
        """Test integrity error handling: duplicate email"""
        # Given
        customer_data = {
            "full_name": "John Doe",
            "email": "existing@example.com"
        }
        self.mock_repo.create.side_effect = IntegrityError("",
                                                           "",
                                                           "customers_email_key")

        # When/Then
        with pytest.raises(ValidationError, match="already used"):
            self.service.create_customer(customer_data, self.sales_user)

    @patch('services.customer.require_permission')
    def test_create_customer_other_error_raises_validation_error(
                                                                self,
                                                                mock_require_permission
                                                                ):
        """Test integrity error handling: other constraint"""
        # Given
        customer_data = {
            "full_name": "John Doe",
            "email": "john@example.com"
        }
        self.mock_repo.create.side_effect = IntegrityError("", "", "other_constraint")

        # When/Then
        with pytest.raises(ValidationError, match="Data conflict"):
            self.service.create_customer(customer_data, self.sales_user)

    @patch('services.customer.require_permission')
    def test_update_customer_basic_flow(self, mock_require_permission):
        """Test customer update - basic flow"""
        # Given
        customer_id = 1
        customer_data = {
            "full_name": "John Updated",
            "email": "john.updated@example.com"
        }
        expected_customer = {"id": 1, "full_name": "John Updated"}
        self.mock_repo.update.return_value = expected_customer

        # When
        result = self.service.update_customer(
            customer_id, customer_data, self.sales_user
            )

        # Then
        mock_require_permission.assert_called_once()
        self.mock_repo.update.assert_called_once_with(customer_id, unittest.mock.ANY)
        assert result == expected_customer

    @patch('services.customer.require_permission')
    def test_delete_customer_delegates_to_repository(self, mock_require_permission):
        """Test customer deletion delegates to repository"""
        # Given
        customer_id = 1
        self.mock_repo.delete.return_value = True

        # When
        result = self.service.delete_customer(customer_id, self.management_user)

        # Then
        mock_require_permission.assert_called_once()
        self.mock_repo.delete.assert_called_once_with(customer_id)
        assert result is True

    @patch('services.customer.require_permission')
    def test_list_customers_delegates_to_repository(self, mock_require_permission):
        """Test customer listing delegates to repository"""
        # Given
        expected_customers = [
            {"id": 1, "full_name": "John Doe"},
            {"id": 2, "full_name": "Jane Smith"}
        ]
        self.mock_repo.get_all.return_value = expected_customers

        # When
        result = self.service.list_customers(self.sales_user)

        # Then
        mock_require_permission.assert_called_once()
        self.mock_repo.get_all.assert_called_once()
        assert result == expected_customers


class TestContractServiceComplete:
    """Complete tests for ContractService - CRUD and validation"""

    def setup_method(self):
        self.mock_repo = Mock()
        self.service = ContractService(self.mock_repo)

        self.sales_user = {
            "id": 1,
            "role": "sales",
            "employee_number": "EMP001"
        }

        self.management_user = {
            "id": 2,
            "role": "management",
            "employee_number": "EMP002"
        }

    def test_get_contract_delegates_to_repository(self):
        """Test que get_contract délègue bien au repository"""
        # Given
        contract_id = 1
        expected_contract = {"id": 1, "customer_id": 1, "total_amount": 10000}
        self.mock_repo.get_by_id.return_value = expected_contract

        # When
        result = self.service.get_contract(contract_id)

        # Then
        assert result == expected_contract
        self.mock_repo.get_by_id.assert_called_once_with(contract_id)

    @patch('services.contract.require_permission')
    def test_create_contract_basic_flow(self, mock_require_permission):
        """Test contract creation - basic flow"""
        # Given
        contract_data = {
            "customer_id": "1",
            "total_amount": 10000.0,
            "remaining_amount": 5000.0,
            "signed": True
        }
        expected_contract = {"id": 1, "customer_id": 1, "total_amount": 10000.0}
        self.mock_repo.create.return_value = expected_contract

        # When
        result = self.service.create_contract(contract_data, self.sales_user)

        # Then
        mock_require_permission.assert_called_once()
        self.mock_repo.create.assert_called_once()
        assert result == expected_contract

    @patch('services.contract.require_permission')
    def test_create_contract_empty_customer_id_raises_error(
                                                            self,
                                                            mock_require_permission
                                                            ):
        """Test validation: empty customer_id raises error"""
        # Given
        contract_data = {
            "customer_id": "",
            "total_amount": 10000.0
        }

        # When/Then
        with pytest.raises(ValidationError, match="customer_id"):
            self.service.create_contract(contract_data, self.sales_user)

    @patch('services.contract.require_permission')
    def test_create_contract_validation_negative_raises_error(
                                                            self,
                                                            mock_require_permission
                                                ):
        """Test validation: negative amount raises error"""
        # Given
        contract_data = {
            "customer_id": "1",
            "total_amount": -1000.0
        }

        # When/Then
        with pytest.raises(ValidationError):
            self.service.create_contract(contract_data, self.sales_user)

    @patch('services.contract.require_permission')
    def test_create_contract_remaining_greater_than_total_raises_error(
                                                        self,
                                                        mock_require_permission
                                                        ):
        """Test validation: remaining amount > total raises error"""
        # Given
        contract_data = {
            "customer_id": "1",
            "total_amount": 5000.0,
            "remaining_amount": 10000.0
        }

        # When/Then
        with pytest.raises(ValidationError, match="Remaining amount cannot be greater"):
            self.service.create_contract(contract_data, self.sales_user)

    @patch('services.contract.require_permission')
    def test_create_contract_invalid_customer_id_raises_error(
                                                            self,
                                                            mock_require_permission
                                                            ):
        """Test validation: invalid customer_id raises error"""
        # Given
        contract_data = {
            "customer_id": "not_a_number",
            "total_amount": 10000.0
        }

        # When/Then
        with pytest.raises(ValidationError, match="valid integers"):
            self.service.create_contract(contract_data, self.sales_user)

    @patch('services.contract.require_permission')
    def test_delete_contract_delegates_to_repository(self, mock_require_permission):
        """Test contract deletion delegates to repository"""
        # Given
        contract_id = 1
        self.mock_repo.delete.return_value = True

        # When
        result = self.service.delete_contract(contract_id, self.management_user)

        # Then
        mock_require_permission.assert_called_once()
        self.mock_repo.delete.assert_called_once_with(contract_id)
        assert result is True

    @patch('services.contract.require_permission')
    def test_list_contracts_delegates_to_repository(self, mock_require_permission):
        """Test contract listing delegates to repository"""
        # Given
        expected_contracts = [
            {"id": 1, "customer_id": 1, "total_amount": 10000},
            {"id": 2, "customer_id": 2, "total_amount": 15000}
        ]
        self.mock_repo.get_all.return_value = expected_contracts

        # When
        result = self.service.list_contracts(self.sales_user)

        # Then
        mock_require_permission.assert_called_once()
        self.mock_repo.get_all.assert_called_once()
        assert result == expected_contracts
