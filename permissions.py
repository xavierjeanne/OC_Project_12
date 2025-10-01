"""
Role-based permission management module
Defines permissions for each role (sales, support, management)
"""

from enum import Enum
from typing import Optional

from models import Employee


class Permission(Enum):
    """Enumeration of available permissions"""

    # Customer permissions
    CREATE_CUSTOMER = "create_customer"
    READ_CUSTOMER = "read_customer"
    UPDATE_CUSTOMER = "update_customer"
    DELETE_CUSTOMER = "delete_customer"

    # Employee permissions
    CREATE_EMPLOYEE = "create_employee"
    READ_EMPLOYEE = "read_employee"
    UPDATE_EMPLOYEE = "update_employee"
    DELETE_EMPLOYEE = "delete_employee"

    # Contract permissions
    CREATE_CONTRACT = "create_contract"
    READ_CONTRACT = "read_contract"
    UPDATE_CONTRACT = "update_contract"
    DELETE_CONTRACT = "delete_contract"
    SIGN_CONTRACT = "sign_contract"

    # Event permissions
    CREATE_EVENT = "create_event"
    READ_EVENT = "read_event"
    UPDATE_EVENT = "update_event"
    DELETE_EVENT = "delete_event"
    ASSIGN_SUPPORT = "assign_support"


class PermissionError(Exception):
    """Exception raised when access is unauthorized"""

    pass


# Permission definitions by role
ROLE_PERMISSIONS = {
    "sales": [
        # Customers: full CRUD
        Permission.CREATE_CUSTOMER,
        Permission.READ_CUSTOMER,
        Permission.UPDATE_CUSTOMER,
        # No DELETE_CUSTOMER for sales
        # Employees: read only
        Permission.READ_EMPLOYEE,
        # Contracts: full CRUD + signing
        Permission.CREATE_CONTRACT,
        Permission.READ_CONTRACT,
        Permission.UPDATE_CONTRACT,
        Permission.SIGN_CONTRACT,
        # No DELETE_CONTRACT
        # Events: read and create
        Permission.CREATE_EVENT,
        Permission.READ_EVENT,
        # No UPDATE/DELETE for sales
    ],
    "support": [
        # Customers: read only
        Permission.READ_CUSTOMER,
        # Employees: read only
        Permission.READ_EMPLOYEE,
        # Contracts: read only
        Permission.READ_CONTRACT,
        # Events: read and update (for assigned events)
        Permission.READ_EVENT,
        Permission.UPDATE_EVENT,
        # No CREATE/DELETE for support
    ],
    "management": [
        # Management has ALL permissions
        Permission.CREATE_CUSTOMER,
        Permission.READ_CUSTOMER,
        Permission.UPDATE_CUSTOMER,
        Permission.DELETE_CUSTOMER,
        Permission.CREATE_EMPLOYEE,
        Permission.READ_EMPLOYEE,
        Permission.UPDATE_EMPLOYEE,
        Permission.DELETE_EMPLOYEE,
        Permission.CREATE_CONTRACT,
        Permission.READ_CONTRACT,
        Permission.UPDATE_CONTRACT,
        Permission.DELETE_CONTRACT,
        Permission.SIGN_CONTRACT,
        Permission.CREATE_EVENT,
        Permission.READ_EVENT,
        Permission.UPDATE_EVENT,
        Permission.DELETE_EVENT,
        Permission.ASSIGN_SUPPORT,
    ],
}


def has_permission(employee: Optional[Employee], permission: Permission) -> bool:
    """
    Checks if an employee has a given permission

    Args:
        employee: The employee to check (can be None)
        permission: The permission to check

    Returns:
        True if the employee has the permission, False otherwise
    """
    if employee is None:
        return False

    role = employee.role.lower() if employee.role else None

    if role not in ROLE_PERMISSIONS:
        return False

    return permission in ROLE_PERMISSIONS[role]


def require_permission(employee: Optional[Employee], permission: Permission) -> None:
    """
    Checks that an employee has a permission, otherwise raises an exception

    Args:
        employee: The employee to check
        permission: The required permission

    Raises:
        PermissionError: If the employee doesn't have the permission
    """
    if employee is None:
        raise PermissionError("Authentication required")

    if not has_permission(employee, permission):
        raise PermissionError(
            f"Employee {employee.name} (role: {employee.role}) "
            f"does not have permission '{permission.value}'"
        )


def can_update_own_assigned_customer(employee: Optional[Employee], customer) -> bool:
    """
    Checks if a sales employee can update THEIR assigned customer

    Args:
        employee: The employee to check
        customer: The customer to update

    Returns:
        True if the employee can update this customer
    """
    if employee is None or customer is None:
        return False

    # Management can do everything
    if employee.role == "management":
        return True

    # Sales can update their own customers
    if employee.role == "sales":
        return customer.sales_contact_id == employee.id

    return False


def can_update_own_assigned_contract(employee: Optional[Employee], contract) -> bool:
    """
    Checks if a sales employee can update THEIR assigned contract

    Args:
        employee: The employee to check
        contract: The contract to update

    Returns:
        True if the employee can update this contract
    """
    if employee is None or contract is None:
        return False

    # Management can do everything
    if employee.role == "management":
        return True

    # Sales can update their own contracts
    if employee.role == "sales":
        return contract.sales_contact_id == employee.id

    return False


def can_update_own_assigned_event(employee: Optional[Employee], event) -> bool:
    """
    Checks if a support employee can update THEIR assigned event

    Args:
        employee: The employee to check
        event: The event to update

    Returns:
        True if the employee can update this event
    """
    if employee is None or event is None:
        return False

    # Management can do everything
    if employee.role == "management":
        return True

    # Support can update their own events
    if employee.role == "support":
        return event.support_contact_id == employee.id

    return False


def get_role_permissions(role: str) -> list:
    """
    Returns the list of permissions for a given role

    Args:
        role: The role

    Returns:
        List of permissions
    """
    role = role.lower() if role else None
    return ROLE_PERMISSIONS.get(role, [])


def describe_permissions(role: str) -> str:
    """
    Returns a human-readable description of a role's permissions

    Args:
        role: The role

    Returns:
        Formatted description of permissions
    """
    perms = get_role_permissions(role)

    if not perms:
        return f"No permissions for role '{role}'"

    description = f"Permissions for role '{role.upper()}':\n"

    # Group by entity
    entities = {"Customer": [], "Employee": [], "Contract": [], "Event": []}

    for perm in perms:
        perm_str = perm.value
        for entity in entities.keys():
            if entity.lower() in perm_str:
                entities[entity].append(perm_str)
                break

    for entity, entity_perms in entities.items():
        if entity_perms:
            description += f"\n  {entity}:\n"
            for perm in entity_perms:
                action = (
                    perm.replace(f"_{entity.lower()}", "").replace("_", " ").title()
                )
                description += f"    - {action}\n"

    return description
