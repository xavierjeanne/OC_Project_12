from models import Contract
from repositories.contract import ContractRepository
from utils.permissions import Permission, require_permission, PermissionError
from utils.validators import (validate_string_not_empty, validate_positive_amount,
                              validate_non_negative_amount, ValidationError)
from utils.sentry_config import capture_exceptions
from utils.audit_logger import crm_logger, log_exception_with_context, log_critical_action


class ContractService:

    def __init__(self, contract_repository: ContractRepository):
        self.repository = contract_repository

    def get_contract(self, contract_id):
        return self.repository.get_by_id(contract_id)

    @log_exception_with_context(service="ContractService", operation="create")
    def create_contract(self, contract_data, current_user):
        require_permission(current_user, Permission.CREATE_CONTRACT)

        # Validate required fields
        customer_id = validate_string_not_empty(contract_data["customer_id"],
                                                "customer_id")

        # Validate amounts
        total_amount = validate_positive_amount(
            contract_data.get("total_amount", 0.0), "total_amount"
        )
        remaining_amount = validate_non_negative_amount(
            contract_data.get("remaining_amount", total_amount), "remaining_amount"
        )

        # Ensure remaining_amount <= total_amount
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

        return self.repository.create(contract_data_dict)

    @log_exception_with_context(service="ContractService", operation="update")
    def update_contract(self, contract_id, contract_data, current_user):
        require_permission(current_user, Permission.UPDATE_CONTRACT)

        # Get existing contract to check ownership for sales
        existing_contract = self.repository.get_by_id(contract_id)
        if not existing_contract:
            raise ValidationError(f"Contract with ID {contract_id} not found")
        
        # Save original signed status before it gets modified
        original_signed_status = existing_contract.signed

        # Check if sales can update this contract (ownership validation)
        if current_user['role'] == 'sales':
            if existing_contract.sales_contact_id != current_user['id']:
                raise PermissionError(
                    f"Sales employee can only update their own assigned contracts"
                )

        # Validate required fields
        customer_id = validate_string_not_empty(contract_data["customer_id"],
                                                "customer_id")

        # Validate amounts
        total_amount = validate_positive_amount(
            contract_data.get("total_amount", 0.0), "total_amount"
        )
        remaining_amount = validate_non_negative_amount(
            contract_data.get("remaining_amount", total_amount), "remaining_amount"
        )

        # Ensure that remaining_amount <= total_amount
        if remaining_amount > total_amount:
            raise ValidationError(
                "Remaining amount cannot be greater than total amount"
            )

        # Optional fields
        date_created = contract_data.get("date_created")
        
        # CRITICAL: Only management/admin can modify the 'signed' status
        if 'signed' in contract_data:
            if current_user['role'] not in ['management', 'admin']:
                raise PermissionError(
                    "Only management can sign or modify signature status of contracts"
                )
            signed = bool(contract_data.get("signed", False))
        else:
            # Keep existing signature status if not provided
            signed = existing_contract.signed

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

        # Update the contract
        updated_contract = self.repository.update(contract_id, contract_data_dict)

        # CRITICAL: Log contract signing action for audit trail (Sentry uniquement)
        if signed and not original_signed_status:
            # Newly signed contract - CRITICAL LOG
            crm_logger.log_contract_signature(
                user_info=current_user,
                contract_data={
                    "id": contract_id,
                    "customer_id": customer_id,
                    "total_amount": total_amount,
                    "sales_contact_id": sales_contact_id,
                    "previous_signed_status": original_signed_status
                }
            )

        return updated_contract

    @capture_exceptions
    def sign_contract(self, contract_id: int, current_user) -> Contract:
        """
        Specific method to sign a contract.
        Includes special logging for business traceability.
        """
        require_permission(current_user, Permission.SIGN_CONTRACT)

        # Retrieve the current contract
        contract = self.repository.get_by_id(contract_id)
        if not contract:
            raise ValidationError(f"Contract with ID {contract_id} not found")

        if contract.signed:
            raise ValidationError(f"Contract {contract_id} is already signed")

        # Mark as signed
        contract_data = {'signed': True}
        updated_contract = self.repository.update(contract_id, contract_data)

        # Special log for the signature (Sentry uniquement)
        crm_logger.log_contract_signature(
            user_info=current_user,
            contract_data={
                "id": contract_id,
                "customer_id": updated_contract.customer_id,
                "total_amount": updated_contract.total_amount,
                "sales_contact_id": updated_contract.sales_contact_id,
                "previous_signed_status": False
            }
        )

        return updated_contract

    def delete_contract(self, contract_id, current_user):
        require_permission(current_user, Permission.DELETE_CONTRACT)
        return self.repository.delete(contract_id)

    def list_contracts(self, current_user):
        """List contracts - all users can see all contracts (read-only access)"""
        require_permission(current_user, Permission.READ_CONTRACT)
        # COMPLIANCE: All employees should be able to read all contracts
        return self.repository.get_all()
