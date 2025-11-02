

from models import Contract
from repositories.contract import ContractRepository
from utils.permissions import Permission, require_permission
from utils.validators import (validate_string_not_empty, validate_positive_amount,
                              validate_non_negative_amount, ValidationError)


class ContractService:
    def __init__(self, contract_repository: ContractRepository):
        self.repository = contract_repository

    def get_contract(self, contract_id):
        return self.repository.get_by_id(contract_id)

    def create_contract(self, contract_data, current_user):
        require_permission(current_user, Permission.CREATE_CONTRACT)

        # Validation des champs obligatoires
        customer_id = validate_string_not_empty(contract_data["customer_id"],
                                                "customer_id")

        # Validation des montants
        total_amount = validate_positive_amount(
            contract_data.get("total_amount", 0.0), "total_amount"
        )
        remaining_amount = validate_non_negative_amount(
            contract_data.get("remaining_amount", total_amount), "remaining_amount"
        )

        # Validation que remaining_amount <= total_amount
        if remaining_amount > total_amount:
            raise ValidationError(
                "Remaining amount cannot be greater than total amount"
            )

        # Champs optionnels
        date_created = contract_data.get("date_created")
        signed = bool(contract_data.get("signed", False))

        # Relation avec le sales_contact (peut être modifié par management)
        if current_user['role'] in ['management', 'admin']:
            sales_contact_id = contract_data.get("sales_contact_id", current_user['id'])
        else:
            sales_contact_id = current_user['id']

        try:
            customer_id = int(customer_id)
            sales_contact_id = int(sales_contact_id)
        except (ValueError, TypeError):
            raise ValidationError(
                "Customer ID and Sales Contact ID must be valid integers"
                )

        contract_data_dict = {
            'customer_id': customer_id,
            'sales_contact_id': sales_contact_id,
            'total_amount': total_amount,
            'remaining_amount': remaining_amount,
            'date_created': date_created,
            'signed': signed
        }

        return self.repository.create(contract_data_dict)

    def update_contract(self, contract_id, contract_data, current_user):
        require_permission(current_user, Permission.UPDATE_CONTRACT)

        # Validation required fields
        customer_id = validate_string_not_empty(contract_data["customer_id"],
                                                "customer_id")

        # Validation amounts
        total_amount = validate_positive_amount(
            contract_data.get("total_amount", 0.0), "total_amount"
        )
        remaining_amount = validate_non_negative_amount(
            contract_data.get("remaining_amount", total_amount), "remaining_amount"
        )

        # Validation that remaining_amount <= total_amount
        if remaining_amount > total_amount:
            raise ValidationError(
                "Remaining amount cannot be greater than total amount"
            )

        # Optional fields
        date_created = contract_data.get("date_created")
        signed = bool(contract_data.get("signed", False))

        # Relation with the sales_contact (can be modified by management)
        if current_user['role'] in ['management', 'admin']:
            sales_contact_id = contract_data.get("sales_contact_id", current_user['id'])
        else:
            sales_contact_id = current_user['id']

        try:
            customer_id = int(customer_id)
            sales_contact_id = int(sales_contact_id)
        except (ValueError, TypeError):
            raise ValidationError(
                "Customer ID and Sales Contact ID must be valid integers"
                )

        contract_data_dict = {
            'customer_id': customer_id,
            'sales_contact_id': sales_contact_id,
            'total_amount': total_amount,
            'remaining_amount': remaining_amount,
            'date_created': date_created,
            'signed': signed
        }

        return self.repository.update(contract_id, contract_data_dict)

    def delete_contract(self, contract_id, current_user):
        require_permission(current_user, Permission.DELETE_CONTRACT)
        return self.repository.delete(contract_id)

    def list_contracts(self, current_user):
        """List contracts - all users can see all contracts (read-only access)"""
        require_permission(current_user, Permission.READ_CONTRACT)
        # CONFORMITÉ: Tous les collaborateurs doivent pouvoir accéder à tous les contrats en lecture seule
        return self.repository.get_all()
