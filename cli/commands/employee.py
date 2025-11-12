"""
Employee management commands
"""

import click
from models import Session, Employee
from repositories.employee import EmployeeRepository
from services.employee import EmployeeService
from utils.permissions import PermissionError, Permission
from cli.utils.auth import cli_auth_required, get_current_user, require_permission
from cli.utils.error_handling import handle_cli_errors, display_success_message


def get_employee_service():
    """Create employee service instance"""
    session = Session()
    repository = EmployeeRepository(session)
    return EmployeeService(repository), session


@click.group(name="employee")
def employee_group():
    """Employee management (create, update, view, delete)"""


@employee_group.command(name="list")
@click.option("--role", help="Filter by role (sales, support, management)")
@click.option("--limit", default=20, help="Maximum number of results")
@cli_auth_required
@handle_cli_errors
def list_employees(role, limit):
    """Display employee list"""
    click.echo(click.style("=== Employee List ===", fg="blue", bold=True))

    service, session = get_employee_service()

    try:
        current_user = get_current_user()
        employees = service.list_employees(current_user)

        # Apply role filter if specified
        if role:
            employees = [emp for emp in employees if emp.role == role]

        # Apply limit
        employees = employees[:limit] if limit else employees

        if not employees:
            click.echo(click.style("No employees found.", fg="yellow"))
            return

        # Display employees in table format
        click.echo(f"{'ID':<5} {'Name':<20} {'Email':<25} {'Role':<10} {'Emp#':<8} {'Created':<12} {'Last Login':<12}")
        click.echo("-" * 92)

        for emp in employees:
            # Format dates
            created_date = (
                emp.created_at.strftime("%Y-%m-%d") if emp.created_at else "N/A"
            )
            last_login_date = (
                emp.last_login.strftime("%Y-%m-%d") if emp.last_login else "Never"
            )
            
            click.echo(
                f"{emp.id:<5} {emp.name[:19]:<20} {emp.email[:24]:<25}"
                f"{emp.role or 'N/A':<10} {emp.employee_number:<8} {created_date:<12} {last_login_date:<12}"
            )

        click.echo(f"\nTotal: {len(employees)} employee(s)")

    except PermissionError as e:
        click.echo(click.style(f"Permission denied: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
    finally:
        session.close()


@employee_group.command(name="create")
@click.option("--name", prompt="Full name", help="Employee full name")
@click.option("--email", prompt="Email", help="Employee email address")
@click.option(
    "--role-id",
    prompt="Role ID (1=sales, 2=support, 3=management)",
    type=int,
    help="Employee role ID",
)
@click.option(
    "--password",
    prompt="Password",
    hide_input=True,
    confirmation_prompt=True,
    help="Employee password",
)
@cli_auth_required
@require_permission(Permission.CREATE_EMPLOYEE)
@handle_cli_errors
def create_employee(name, email, role_id, password):
    """Create a new employee"""
    click.echo(click.style("=== Create Employee ===", fg="blue", bold=True))

    service, session = get_employee_service()

    try:
        current_user = get_current_user()

        # Generate employee number
        employee_number = Employee.generate_employee_number(session)

        employee_data = {
            "name": name,
            "email": email,
            "employee_number": employee_number,
            "role_id": role_id,
            "password": password,
        }

        employee = service.create_employee(employee_data, current_user)

        display_success_message(
            "Employee created successfully!",
            {
                "ID": employee.id,
                "Name": employee.name,
                "Email": employee.email,
                "Employee Number": employee.employee_number,
                "Role ID": employee.role_id,
            },
        )

    finally:
        session.close()


@employee_group.command(name="update")
@click.argument("employee_id", type=int)
@click.option("--name", help="New full name")
@click.option("--email", help="New email address")
@click.option("--role-id", type=int, help="New role ID")
@cli_auth_required
@require_permission(Permission.UPDATE_EMPLOYEE)
@handle_cli_errors
def update_employee(employee_id, name, email, role_id):
    """Update an existing employee"""
    click.echo(
        click.style(f"=== Update Employee {employee_id} ===", fg="blue", bold=True)
    )

    service, session = get_employee_service()

    try:
        current_user = get_current_user()

        # Get existing employee
        existing_employee = service.get_employee(employee_id)
        if not existing_employee:
            click.echo(click.style(f"Employee {employee_id} not found.", fg="red"))
            return

        # Prepare update data with only provided fields
        update_data = {}

        if name:
            update_data["name"] = name
        else:
            update_data["name"] = existing_employee.name

        if email:
            update_data["email"] = email
        else:
            update_data["email"] = existing_employee.email

        if role_id:
            update_data["role_id"] = role_id
        else:
            update_data["role_id"] = existing_employee.role_id

        update_data["employee_number"] = existing_employee.employee_number

        # If no changes specified, prompt user
        if not any([name, email, role_id]):
            click.echo("No changes specified. What would you like to update?")
            new_name = click.prompt(
                "Name", default=existing_employee.name, show_default=True
            )
            new_email = click.prompt(
                "Email", default=existing_employee.email, show_default=True
            )
            new_role_id = click.prompt(
                "Role ID",
                default=existing_employee.role_id,
                type=int,
                show_default=True,
            )

            update_data.update(
                {"name": new_name, "email": new_email, "role_id": new_role_id}
            )

        updated_employee = service.update_employee(
            employee_id, update_data, current_user
        )

        display_success_message(
            "Employee updated successfully!",
            {
                "ID": updated_employee.id,
                "Name": updated_employee.name,
                "Email": updated_employee.email,
                "Role ID": updated_employee.role_id,
            },
        )
    finally:
        session.close()


@employee_group.command(name="delete")
@click.argument("employee_id", type=int)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@cli_auth_required
@require_permission(Permission.DELETE_EMPLOYEE)
@handle_cli_errors
def delete_employee(employee_id, force):
    """Delete an employee"""
    from cli.utils.error_handling import (
        validate_id,
        display_success_message,
        display_info_message,
        ResourceNotFoundError,
        confirm_destructive_action,
    )

    # ID validation
    employee_id = validate_id(employee_id, "Employee ID")

    service, session = get_employee_service()

    try:
        current_user = get_current_user()

        # Get existing employee to show details before deletion
        existing_employee = service.get_employee(employee_id)
        if not existing_employee:
            raise ResourceNotFoundError(
                f"Employee with ID {employee_id} does not exist."
            )

        # Show employee details
        click.echo(
            click.style(f"=== Delete Employee {employee_id} ===", fg="red", bold=True)
        )
        click.echo(f"Name: {existing_employee.full_name}")
        click.echo(f"Email: {existing_employee.email}")
        click.echo(f"Employee Number: {existing_employee.employee_number}")

        # Confirmation
        if not force:
            if not confirm_destructive_action(
                f"delete employee '{existing_employee.full_name}'"
            ):
                display_info_message("Operation cancelled.")
                return

        # Perform deletion
        service.delete_employee(employee_id, current_user)

        display_success_message(
            f"Employee '{existing_employee.full_name}' deleted successfully!"
        )

    finally:
        session.close()
