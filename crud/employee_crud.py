from typing import Optional

from sqlalchemy.orm import sessionmaker

from config import engine
from models import Employee
from permissions import Permission, PermissionError, require_permission
from validators import (ValidationError, validate_email, validate_role,
                        validate_string_not_empty)

Session = sessionmaker(bind=engine)


def create_employee(name, email, role, current_user: Optional[Employee] = None):
    """
    Creates a new employee

    Args:
        name: Employee's name
        email: Employee's email
        role: Role (sales, support, management)
        current_user: The employee performing the action (for permission checking)

    Returns:
        The created employee

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    # Check permissions (only management can create employees)
    if current_user:
        require_permission(current_user, Permission.CREATE_EMPLOYEE)

    # Validate data
    name = validate_string_not_empty(name, "name")
    email = validate_email(email)
    role = validate_role(role)

    session = Session()
    try:
        employee = Employee(name=name, email=email, role=role)
        session.add(employee)
        session.commit()
        print(f"Employee '{name}' created with id {employee.id}.")
        return employee
    except Exception as e:
        session.rollback()
        print(f"Error creating employee: {e}")
        raise
    finally:
        session.close()


def get_all_employees(current_user: Optional[Employee] = None):
    """
    Retrieves all employees

    Args:
        current_user: The employee performing the action (for permission checking)

    Returns:
        List of employees

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions
    if current_user:
        require_permission(current_user, Permission.READ_EMPLOYEE)

    session = Session()
    try:
        employees = session.query(Employee).all()
        for e in employees:
            print(e.id, e.name, e.email, e.role)
        return employees
    finally:
        session.close()


def update_employee(employee_id, current_user: Optional[Employee] = None, **kwargs):
    """
    Updates an employee

    Args:
        employee_id: ID of the employee to update
        current_user: The employee performing the action (for permission checking)
        **kwargs: Fields to update

    Returns:
        The updated employee

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    # Check permissions (only management can update employees)
    if current_user:
        require_permission(current_user, Permission.UPDATE_EMPLOYEE)

    session = Session()
    try:
        employee = session.get(Employee, employee_id)
        if employee:
            # Validate data before update
            if "name" in kwargs:
                kwargs["name"] = validate_string_not_empty(kwargs["name"], "name")
            if "email" in kwargs:
                kwargs["email"] = validate_email(kwargs["email"])
            if "role" in kwargs:
                kwargs["role"] = validate_role(kwargs["role"])

            for key, value in kwargs.items():
                setattr(employee, key, value)
            session.commit()
            print(f"Employee {employee_id} updated.")
            return employee
        else:
            print(f"Employee {employee_id} not found.")
            return None
    except (PermissionError, ValidationError):
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating employee: {e}")
        raise
    finally:
        session.close()


def delete_employee(employee_id, current_user: Optional[Employee] = None):
    """
    Deletes an employee

    Args:
        employee_id: ID of the employee to delete
        current_user: The employee performing the action (for permission checking)

    Returns:
        True if deletion successful, False otherwise

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions (only management can delete employees)
    if current_user:
        require_permission(current_user, Permission.DELETE_EMPLOYEE)

    session = Session()
    try:
        employee = session.get(Employee, employee_id)
        if employee:
            session.delete(employee)
            session.commit()
            print(f"Employee {employee_id} deleted.")
            return True
        else:
            print(f"Employee {employee_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting employee: {e}")
        raise
    finally:
        session.close()
