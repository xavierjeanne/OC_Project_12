from models import Employee
from repositories.employee import EmployeeRepository
from utils.permissions import Permission, require_permission
from utils.validators import (validate_string_not_empty, validate_email,
                              ValidationError)


class EmployeeService:
    def __init__(self, employee_repository: EmployeeRepository):
        self.repository = employee_repository

    def get_employee(self, employee_id):
        return self.repository.find_by_id(employee_id)

    def create_employee(self, employee_data, current_user):
        require_permission(current_user, Permission.CREATE_EMPLOYEE)

        # Validation data
        name = validate_string_not_empty(employee_data["name"], "name")
        email = validate_email(employee_data["email"])
        employee_number = validate_string_not_empty(
            employee_data["employee_number"], "employee_number"
        )
        role_id = employee_data.get("role_id")
        if not role_id:
            raise ValidationError("role_id is required")

        # check that role_id is valid
        try:
            role_id = int(role_id)
        except (ValueError, TypeError):
            raise ValidationError("role_id must be a valid integer")

        employee = Employee(
            name=name,
            email=email,
            employee_number=employee_number,
            role_id=role_id
        )

        return self.repository.create(employee)

    def update_employee(self, employee_id, employee_data, current_user):
        require_permission(current_user, Permission.UPDATE_EMPLOYEE)
        # Validation data
        name = validate_string_not_empty(employee_data["name"], "name")
        email = validate_email(employee_data["email"])
        employee_number = validate_string_not_empty(
            employee_data["employee_number"], "employee_number"
        )
        role_id = employee_data.get("role_id")
        if not role_id:
            raise ValidationError("role_id is required")

        # check that role_id is valid
        try:
            role_id = int(role_id)
        except (ValueError, TypeError):
            raise ValidationError("role_id must be a valid integer")

        employee = Employee(
            id=employee_id,
            name=name,
            email=email,
            employee_number=employee_number,
            role_id=role_id
        )

        return self.repository.update(employee)

    def delete_employee(self, employee_id, current_user):
        require_permission(current_user, Permission.DELETE_EMPLOYEE)
        return self.repository.delete(employee_id)

    def list_employees(self, current_user):
        """ list of all employees by role and permission"""
        require_permission(current_user, Permission.READ_EMPLOYEE)

        if current_user['role'] in ['management', 'admin']:
            # Management et Admin see all employes
            return self.repository.get_all()
        elif current_user['role'] == 'sales':
            # Sales see only sales + management
            sales_team = self.repository.find_by_role('sales')
            management_team = self.repository.find_by_role('management')
            return sales_team + management_team
        elif current_user['role'] == 'support':
            # Support see only support + management
            support_team = self.repository.find_by_role('support')
            management_team = self.repository.find_by_role('management')
            return support_team + management_team
        else:
            return []
