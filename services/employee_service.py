from models.models import Employee
from repositories.employee_repository import EmployeeRepository
from security.permissions import Permission, require_permission
from validations.validators import validate_string_not_empty


class EmployeeService:
    def __init__(self, employee_repository: EmployeeRepository):
        self.repository = employee_repository

    def get_employee(self, employee_id):
        return self.repository.find_by_id(employee_id)

    def create_employee(self, employee_data, current_user):
        require_permission(current_user, Permission.CREATE_EMPLOYEE)

        name = validate_string_not_empty(employee_data["name"], "name")
        email = validate_string_not_empty(employee_data["email"], "email")
        role = validate_string_not_empty(employee_data["role"], "role")

        employee = Employee(
            name=name,
            email=email,
            role=role
        )

        return self.repository.create(employee)

    def update_employee(self, employee_id, employee_data, current_user):
        require_permission(current_user, Permission.UPDATE_EMPLOYEE)

        name = validate_string_not_empty(employee_data["name"], "name")
        email = validate_string_not_empty(employee_data["email"], "email")
        role = validate_string_not_empty(employee_data["role"], "role")

        employee = Employee(
            id=employee_id,
            name=name,
            email=email,
            role=role
        )

        return self.repository.update(employee)

    def delete_employee(self, employee_id, current_user):
        require_permission(current_user, Permission.DELETE_EMPLOYEE)
        return self.repository.delete(employee_id)

    def list_employees(self):
        return self.repository.list_all()
