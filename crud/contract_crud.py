from typing import Optional

from sqlalchemy.orm import sessionmaker

from config import engine
from models import Contract, Employee
from permissions import (Permission, PermissionError,
                         can_update_own_assigned_contract, require_permission)
from validators import (ValidationError, validate_non_negative_amount,
                        validate_positive_amount, validate_remaining_amount)

Session = sessionmaker(bind=engine)


def create_contract(
    customer_id,
    sales_contact_id,
    total_amount,
    remaining_amount,
    date_created,
    signed=False,
    current_user: Optional[Employee] = None,
):
    """
    Creates a new contract

    Args:
        customer_id: Customer's ID
        sales_contact_id: Sales contact's ID
        total_amount: Total amount
        remaining_amount: Remaining amount
        date_created: Creation date
        signed: Signed or not (default: False)
        current_user: The employee performing the action (for permission checking)

    Returns:
        The created contract

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    # Check permissions
    if current_user:
        require_permission(current_user, Permission.CREATE_CONTRACT)

    # Validate amounts
    total_amount = validate_positive_amount(total_amount, "total amount")
    remaining_amount = validate_non_negative_amount(
        remaining_amount, "remaining amount"
    )
    validate_remaining_amount(total_amount, remaining_amount)

    session = Session()
    try:
        contract = Contract(
            customer_id=customer_id,
            sales_contact_id=sales_contact_id,
            total_amount=total_amount,
            remaining_amount=remaining_amount,
            date_created=date_created,
            signed=signed,
        )
        session.add(contract)
        session.commit()
        print(f"Contract created with id {contract.id}.")
        return contract
    except Exception as e:
        session.rollback()
        print(f"Error creating contract: {e}")
        raise
    finally:
        session.close()


def get_all_contracts(current_user: Optional[Employee] = None):
    """
    Retrieves all contracts

    Args:
        current_user: The employee performing the action (for permission checking)

    Returns:
        List of contracts

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions
    if current_user:
        require_permission(current_user, Permission.READ_CONTRACT)

    session = Session()
    try:
        contracts = session.query(Contract).all()
        for c in contracts:
            print(c.id, c.customer_id, c.sales_contact_id, c.total_amount, c.signed)
        return contracts
    finally:
        session.close()


def update_contract(contract_id, current_user: Optional[Employee] = None, **kwargs):
    """
    Updates a contract

    Args:
        contract_id: ID of the contract to update
        current_user: The employee performing the action (for permission checking)
        **kwargs: Fields to update

    Returns:
        The updated contract

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    session = Session()
    try:
        contract = session.get(Contract, contract_id)
        if contract:
            # Check permissions
            if current_user:
                # Management or assigned sales can update
                if not (
                    can_update_own_assigned_contract(current_user, contract)
                    or current_user.role == "management"
                ):
                    require_permission(current_user, Permission.UPDATE_CONTRACT)

            # Validate data before update
            if "total_amount" in kwargs:
                kwargs["total_amount"] = validate_positive_amount(
                    kwargs["total_amount"], "total amount"
                )
            if "remaining_amount" in kwargs:
                kwargs["remaining_amount"] = validate_non_negative_amount(
                    kwargs["remaining_amount"], "remaining amount"
                )

            # If updating amounts, check consistency
            new_total = kwargs.get("total_amount", contract.total_amount)
            new_remaining = kwargs.get("remaining_amount", contract.remaining_amount)
            validate_remaining_amount(new_total, new_remaining)

            for key, value in kwargs.items():
                setattr(contract, key, value)
            session.commit()
            print(f"Contract {contract_id} updated.")
            return contract
        else:
            print(f"Contract {contract_id} not found.")
            return None
    except (PermissionError, ValidationError):
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating contract: {e}")
        raise
    finally:
        session.close()


def delete_contract(contract_id, current_user: Optional[Employee] = None):
    """
    Deletes a contract

    Args:
        contract_id: ID of the contract to delete
        current_user: The employee performing the action (for permission checking)

    Returns:
        True if deletion successful, False otherwise

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions (only management can delete)
    if current_user:
        require_permission(current_user, Permission.DELETE_CONTRACT)

    session = Session()
    try:
        contract = session.get(Contract, contract_id)
        if contract:
            session.delete(contract)
            session.commit()
            print(f"Contract {contract_id} deleted.")
            return True
        else:
            print(f"Contract {contract_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting contract: {e}")
        raise
    finally:
        session.close()
