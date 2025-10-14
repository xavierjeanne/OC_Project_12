

from models import Contract
from repositories.contract import ContractRepository
from security.permissions import Permission, require_permission
from utils.validators import validate_string_not_empty


class ContractService:
    def __init__(self, contract_repository: ContractRepository):
        self.repository = contract_repository

    def get_contract(self, contract_id):
        return self.repository.find_by_id(contract_id)

    def create_contract(self, contract_data, current_user):
        require_permission(current_user, Permission.CREATE_CONTRACT)

        customer_id = validate_string_not_empty(contract_data["customer_id"],
                                                "customer_id")
        total_amount = contract_data.get("total_amount", 0.0)
        remaining_amount = contract_data.get("remaining_amount", total_amount)

        contract = Contract(
            customer_id=int(customer_id),
            sales_contact_id=current_user.id,
            total_amount=float(total_amount),
            remaining_amount=float(remaining_amount),
            signed=False
        )

        return self.repository.create(contract)

    def update_contract(self, contract_id, contract_data, current_user):
        require_permission(current_user, Permission.UPDATE_CONTRACT)

        customer_id = validate_string_not_empty(contract_data["customer_id"],
                                                "customer_id")
        total_amount = contract_data.get("total_amount", 0.0)
        remaining_amount = contract_data.get("remaining_amount",
                                             total_amount)
        signed = contract_data.get("signed", False)

        contract = Contract(
            id=contract_id,
            customer_id=int(customer_id),
            sales_contact_id=current_user.id,
            total_amount=float(total_amount),
            remaining_amount=float(remaining_amount),
            signed=bool(signed)
        )

        return self.repository.update(contract)

    def delete_contract(self, contract_id, current_user):
        require_permission(current_user, Permission.DELETE_CONTRACT)
        return self.repository.delete(contract_id)

    def list_contracts(self):
        return self.repository.list_all()
