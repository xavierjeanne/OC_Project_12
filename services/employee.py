from repositories.employee import EmployeeRepository
from utils.permissions import Permission, require_permission
from utils.validators import validate_string_not_empty, validate_email, ValidationError
from services.auth import AuthService
from utils.sentry_config import (
    log_employee_creation,
    log_employee_update,
    capture_exceptions,
)


class EmployeeService:

    def __init__(self, employee_repository: EmployeeRepository):
        self.repository = employee_repository

    def get_employee(self, employee_id):
        return self.repository.get_by_id(employee_id)

    def create_employee(self, employee_data, current_user):
        require_permission(current_user, Permission.CREATE_EMPLOYEE)

        # Validate input data
        name = validate_string_not_empty(employee_data["name"], "name")
        email = validate_email(employee_data["email"])
        employee_number = validate_string_not_empty(
            employee_data["employee_number"], "employee_number"
        )
        role_id = employee_data.get("role_id")
        if not role_id:
            raise ValidationError("role_id is required")

        # Ensure role_id is an integer
        try:
            role_id = int(role_id)
        except (ValueError, TypeError):
            raise ValidationError("role_id must be a valid integer")

        # Validate and hash password
        password = employee_data.get("password")
        if not password:
            raise ValidationError("password is required")

        password = validate_string_not_empty(password, "password")

        # Hash the password
        auth_service = AuthService()
        password_hash = auth_service.hash_password(password)

        employee_data_dict = {
            "name": name,
            "email": email,
            "employee_number": employee_number,
            "role_id": role_id,
            "password_hash": password_hash,
        }

        # Create the employee
        new_employee = self.repository.create(employee_data_dict)

        # Log creation to Sentry
        current_user_email = getattr(current_user, "email", "system")
        log_employee_creation(
            employee_id=new_employee.id,
            employee_name=new_employee.name,
            created_by=current_user_email,
        )

        return new_employee

    @capture_exceptions
    def update_employee(self, employee_id, employee_data, current_user):
        require_permission(current_user, Permission.UPDATE_EMPLOYEE)

        # Validate input data
        name = validate_string_not_empty(employee_data["name"], "name")
        email = validate_email(employee_data["email"])
        employee_number = validate_string_not_empty(
            employee_data["employee_number"], "employee_number"
        )
        role_id = employee_data.get("role_id")
        if not role_id:
            raise ValidationError("role_id is required")

        # Ensure role_id is an integer
        try:
            role_id = int(role_id)
        except (ValueError, TypeError):
            raise ValidationError("role_id must be a valid integer")

        # Retrieve the existing employee to compute changes
        existing_employee = self.repository.get_by_id(employee_id)
        if not existing_employee:
            raise ValidationError(f"Employee with ID {employee_id} not found")

        # Determine changed fields
        changes = {}
        if existing_employee.name != name:
            changes["name"] = {"old": existing_employee.name, "new": name}
        if existing_employee.email != email:
            changes["email"] = {"old": existing_employee.email, "new": email}
        if existing_employee.employee_number != employee_number:
            changes["employee_number"] = {
                "old": existing_employee.employee_number,
                "new": employee_number,
            }
        if existing_employee.role_id != role_id:
            changes["role_id"] = {"old": existing_employee.role_id, "new": role_id}

        employee_data_dict = {
            "name": name,
            "email": email,
            "employee_number": employee_number,
            "role_id": role_id,
        }

        # Update the employee
        updated_employee = self.repository.update(employee_id, employee_data_dict)

        # Log the update to Sentry (only if there are changes)
        if changes:
            current_user_email = getattr(current_user, "email", "system")
            log_employee_update(
                employee_id=employee_id,
                employee_name=updated_employee.name,
                updated_by=current_user_email,
                changes=changes,
            )

        return updated_employee

    def delete_employee(self, employee_id, current_user):
        require_permission(current_user, Permission.DELETE_EMPLOYEE)
        return self.repository.delete(employee_id)

    def list_employees(self, current_user):
        """Return a list of employees based on role and permissions."""
        require_permission(current_user, Permission.READ_EMPLOYEE)

        if current_user["role"] in ["management", "admin"]:
            # Management and admin see all employees
            return self.repository.get_all()
        elif current_user["role"] == "sales":
            # Sales see only sales + management
            sales_team = self.repository.find_by_role("sales")
            management_team = self.repository.find_by_role("management")
            return sales_team + management_team
        elif current_user["role"] == "support":
            # Support see only support + management
            support_team = self.repository.find_by_role("support")
            management_team = self.repository.find_by_role("management")
            return support_team + management_team
        else:
            return []
