"""
CLI Commands for Epic Events CRM
Authentication and main application commands
"""

import sys
import getpass

from models import Session
from repositories.customer import CustomerRepository
from repositories.contract import ContractRepository
from repositories.event import EventRepository
from repositories.employee import EmployeeRepository
from services.customer import CustomerService
from services.contract import ContractService
from services.event import EventService
from services.employee import EmployeeService
from services.auth_manager import auth_manager
from utils.auth_decorators import (
    cli_auth_required,
    with_user_context
)


def login_command() -> None:
    """Handle user login via CLI"""
    print("Epic Events CRM - Login")
    print("=" * 30)

    # Check if already logged in
    current_user = auth_manager.get_current_user()
    if current_user:
        print(f"You are already logged in as {current_user['name']} "
              f"({current_user['role']})")

        response = input("Do you want to login as a different user? (y/N): ").lower()
        if response != 'y':
            return

        # Logout current user
        auth_manager.logout()
        print("Logged out successfully.")
        print()

    # Get credentials
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            employee_number = input("Employee Number: ").strip()
            if not employee_number:
                print("Employee number is required")
                continue

            password = getpass.getpass("Password: ")
            if not password:
                print("Password is required")
                continue

            # Attempt login
            result = auth_manager.login(employee_number, password)

            if result["success"]:
                print(f"\n{result['message']}")
                print(f"   Role: {result['user']['role']}")
                print(f"   Email: {result['user']['email']}")

                # Show session info
                session_info = auth_manager.get_session_info()
                if session_info:
                    expiry_minutes = session_info["time_until_expiry_minutes"]
                    print(f"   Session expires in: {expiry_minutes:.0f} minutes")

                return
            else:
                print(f"\n{result['message']}")
                attempts_left = max_attempts - attempt - 1
                if attempts_left > 0:
                    print(f"   {attempts_left} attempts remaining")
                    print()

        except KeyboardInterrupt:
            print("\n\nLogin cancelled.")
            return
        except Exception as e:
            print(f"Login error: {e}")

    print("\n Maximum login attempts exceeded. Please try again later.")


def logout_command() -> None:
    """Handle user logout via CLI"""
    current_user = auth_manager.get_current_user()
    if not current_user:
        print("ℹYou are not currently logged in.")
        return

    result = auth_manager.logout()
    print(f"{result['message']}")


def status_command() -> None:
    """Show current authentication status"""
    print(" Epic Events CRM - Status")
    print("=" * 30)

    session_info = auth_manager.get_session_info()
    if not session_info:
        print(" Not authenticated")
        print("   Use 'python epicevents.py login' to sign in")
        return

    user = session_info["user"]
    print(f"Authenticated as: {user['name']}")
    print(f"   Employee Number: {user['employee_number']}")
    print(f"   Email: {user['email']}")
    print(f"   Role: {user['role']}")
    print(f"   Logged in: {session_info['logged_in_at']}")

    expiry_minutes = session_info["time_until_expiry_minutes"]
    if expiry_minutes > 0:
        print(f"   Token expires in: {expiry_minutes:.0f} minutes")
    else:
        print(" Token expired (will auto-refresh on next action)")


# Business Logic Commands with Real Implementation
@cli_auth_required
def list_customers_command() -> None:
    """List customers based on user role and permissions"""
    print("Customers List")
    print("=" * 20)

    try:
        current_user = auth_manager.get_current_user()
        session = Session()

        # Initialize service
        customer_repo = CustomerRepository(session)
        customer_service = CustomerService(customer_repo)

        # Get customers based on role
        customers = customer_service.list_customers(current_user)

        if not customers:
            print("No customers found or no access to customers.")
            return

        print(f"Found {len(customers)} customer(s) for {current_user['role']} role:")
        print("-" * 60)

        for customer in customers:
            customer_line = (f"ID: {customer.id:3d} | {customer.full_name:<25} "
                             f"| {customer.email:<30}")
            print(customer_line)
            if customer.company_name:
                print(f"      Company: {customer.company_name}")
            if customer.sales_contact:
                print(f"      Sales Contact: {customer.sales_contact.name}")
            print("-" * 60)

    except Exception as e:
        print(f"Error listing customers: {e}")
    finally:
        if 'session' in locals():
            session.close()


@cli_auth_required
def list_contracts_command() -> None:
    """List contracts based on user role and permissions"""
    print("Contracts List")
    print("=" * 20)

    try:
        current_user = auth_manager.get_current_user()
        session = Session()

        # Initialize service
        contract_repo = ContractRepository(session)
        contract_service = ContractService(contract_repo)

        # Get contracts based on role
        contracts = contract_service.list_contracts(current_user)

        if not contracts:
            print("No contracts found or no access to contracts.")
            return

        role = current_user['role']
        print(f"Found {len(contracts)} contract(s) for {role} role:")
        print("-" * 80)

        for contract in contracts:
            status = "Signed" if contract.signed else "Unsigned"
            customer_name = contract.customer.full_name
            print(f"ID: {contract.id:3d} | Customer: {customer_name:<25} | {status}")
            amount_line = (f"      Amount: €{contract.total_amount:,.2f} | "
                           f"Remaining: €{contract.remaining_amount:,.2f}")
            print(amount_line)
            if contract.sales_contact:
                print(f"      Sales Contact: {contract.sales_contact.name}")
            print("-" * 80)

    except Exception as e:
        print(f"Error listing contracts: {e}")
    finally:
        if 'session' in locals():
            session.close()


@cli_auth_required
def list_events_command() -> None:
    """List events based on user role and permissions"""
    print("🎪 Events List")
    print("=" * 20)

    try:
        current_user = auth_manager.get_current_user()
        session = Session()

        # Initialize service
        event_repo = EventRepository(session)
        event_service = EventService(event_repo)

        # Get events based on role
        events = event_service.list_events(current_user)

        if not events:
            print("No events found or no access to events.")
            return

        print(f"Found {len(events)} event(s) for {current_user['role']} role:")
        print("-" * 80)

        for event in events:
            print(f"ID: {event.id:3d} | {event.name:<30}")
            print(f"      Customer: {event.customer.full_name}")
            if event.location:
                print(f"      Location: {event.location}")
            if event.attendees:
                print(f"      Attendees: {event.attendees}")
            if event.support_contact:
                print(f"      Support Contact: {event.support_contact.name}")
            print("-" * 80)

    except Exception as e:
        print(f"Error listing events: {e}")
    finally:
        if 'session' in locals():
            session.close()


@cli_auth_required
def list_employees_command() -> None:
    """List employees based on user role and permissions"""
    print("Employees List")
    print("=" * 20)

    try:
        current_user = auth_manager.get_current_user()
        session = Session()

        # Initialize service
        employee_repo = EmployeeRepository(session)
        employee_service = EmployeeService(employee_repo)

        # Get employees based on role
        employees = employee_service.list_employees(current_user)

        if not employees:
            print("No employees found or no access to employees.")
            return

        role = current_user['role']
        print(f"Found {len(employees)} employee(s) for {role} role:")
        print("-" * 70)

        for employee in employees:
            role_name = (employee.employee_role.name
                         if employee.employee_role else "Unknown")
            employee_line = (f"ID: {employee.id:3d} | {employee.name:<25} "
                             f"| Role: {role_name:<12}")
            print(employee_line)
            print(f"      Email: {employee.email}")
            print(f"      Employee #: {employee.employee_number}")
            print("-" * 70)

    except Exception as e:
        print(f"Error listing employees: {e}")
    finally:
        if 'session' in locals():
            session.close()


@with_user_context
def profile_command(user=None) -> None:
    """Show current user profile"""
    print("User Profile")
    print("=" * 15)
    if user:
        print(f"Name: {user['name']}")
        print(f"Employee Number: {user['employee_number']}")
        print(f"Email: {user['email']}")
        print(f"Role: {user['role']}")

        # Show session info
        session_info = auth_manager.get_session_info()
        if session_info:
            expiry_minutes = session_info["time_until_expiry_minutes"]
            print(f"Token expires in: {expiry_minutes:.0f} minutes")


def show_help() -> None:
    """Show available commands"""
    print("Epic Events CRM - Available Commands")
    print("=" * 45)
    print()
    print("Authentication:")
    print("  login             - Login to the system")
    print("  logout            - Logout from the system")
    print("  status            - Show current login status")
    print("  profile           - Show user profile")
    print()
    print("Customer Management:")
    print("  list-customers    - List all customers (role-based access)")
    print("  list-contracts    - List all contracts (role-based access)")
    print("  list-events       - List all events (role-based access)")
    print("  list-employees    - List all employees (role-based access)")
    print("  create-customer   - Create a new customer")
    print("  delete-customer   - Delete a customer")
    print()
    print("Role-based Commands:")
    print("  admin-users       - Manage users (Admin only)")
    print("  reports           - Access reports (Management/Admin)")
    print("  sales-dashboard   - Sales dashboard (Sales+)")
    print()
    print("Testing:")
    print("  long-operation    - Test long operation with auto token refresh")
    print()
    print("Usage:")
    print("  python epicevents.py <command>")
    print()


def main() -> None:
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    # Command mapping
    commands = {
        'login': login_command,
        'logout': logout_command,
        'status': status_command,
        'profile': profile_command,
        'list-customers': list_customers_command,
        'list-contracts': list_contracts_command,
        'list-events': list_events_command,
        'list-employees': list_employees_command,
        'help': show_help,
    }

    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Unknown command: {command}")
        print("Use 'python epicevents.py help' to see available commands")


if __name__ == "__main__":
    main()
