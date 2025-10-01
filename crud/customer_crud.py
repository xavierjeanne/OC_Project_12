from typing import Optional

from sqlalchemy.orm import sessionmaker

from config import engine
from models import Customer, Employee
from permissions import (Permission, PermissionError,
                         can_update_own_assigned_customer, require_permission)
from validators import (ValidationError, validate_email, validate_phone,
                        validate_string_not_empty)

Session = sessionmaker(bind=engine)


def create_customer(
    full_name,
    email,
    phone=None,
    company_name=None,
    current_user: Optional[Employee] = None,
):
    """
    Creates a new customer

    Args:
        full_name: Customer's full name
        email: Customer's email
        phone: Phone (optional)
        company_name: Company name (optional)
        current_user: The employee performing the action (for permission checking)

    Returns:
        The created customer

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    # Check permissions
    if current_user:
        require_permission(current_user, Permission.CREATE_CUSTOMER)

    # Validate data
    full_name = validate_string_not_empty(full_name, "full name")
    email = validate_email(email)
    phone = validate_phone(phone)

    session = Session()
    try:
        customer = Customer(
            full_name=full_name, email=email, phone=phone, company_name=company_name
        )
        session.add(customer)
        session.commit()
        print(f"Customer '{full_name}' created with id {customer.id}.")
        return customer
    except Exception as e:
        session.rollback()
        print(f"Error creating customer: {e}")
        raise
    finally:
        session.close()


def get_all_customers(current_user: Optional[Employee] = None):
    """
    Retrieves all customers

    Args:
        current_user: The employee performing the action (for permission checking)

    Returns:
        List of customers

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions
    if current_user:
        require_permission(current_user, Permission.READ_CUSTOMER)

    session = Session()
    try:
        customers = session.query(Customer).all()
        for c in customers:
            print(c.id, c.full_name, c.email)
        return customers
    finally:
        session.close()


def update_customer(customer_id, current_user: Optional[Employee] = None, **kwargs):
    """
    Updates a customer

    Args:
        customer_id: ID of the customer to update
        current_user: The employee performing the action (for permission checking)
        **kwargs: Fields to update

    Returns:
        The updated customer

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    session = Session()
    try:
        customer = session.get(Customer, customer_id)
        if customer:
            # Check permissions
            if current_user:
                # Management or assigned sales can update
                if not (
                    can_update_own_assigned_customer(current_user, customer)
                    or current_user.role == "management"
                ):
                    require_permission(current_user, Permission.UPDATE_CUSTOMER)

            # Validate data before update
            if "full_name" in kwargs:
                kwargs["full_name"] = validate_string_not_empty(
                    kwargs["full_name"], "full name"
                )
            if "email" in kwargs:
                kwargs["email"] = validate_email(kwargs["email"])
            if "phone" in kwargs:
                kwargs["phone"] = validate_phone(kwargs["phone"])

            for key, value in kwargs.items():
                setattr(customer, key, value)
            session.commit()
            print(f"Customer {customer_id} updated.")
            return customer
        else:
            print(f"Customer {customer_id} not found.")
            return None
    except (PermissionError, ValidationError):
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating customer: {e}")
        raise
    finally:
        session.close()


def delete_customer(customer_id, current_user: Optional[Employee] = None):
    """
    Deletes a customer

    Args:
        customer_id: ID of the customer to delete
        current_user: The employee performing the action (for permission checking)

    Returns:
        True if deletion successful, False otherwise

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions (only management can delete)
    if current_user:
        require_permission(current_user, Permission.DELETE_CUSTOMER)

    session = Session()
    try:
        customer = session.get(Customer, customer_id)
        if customer:
            session.delete(customer)
            session.commit()
            print(f"Customer {customer_id} deleted.")
            return True
        else:
            print(f"Customer {customer_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting customer: {e}")
        raise
    finally:
        session.close()
