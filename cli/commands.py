"""
CLI Commands for Epic Events CRM
Authentication and main application commands
"""

import sys
import getpass

from services.auth_manager import auth_manager
from utils.permissions import Permission
from utils.auth_decorators import (
    cli_auth_required,
    cli_permission_required,
    auto_refresh_token,
    cli_role_required,
    cli_admin_required,
    cli_management_or_admin_required,
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


# Example protected commands using new decorators
@cli_auth_required
def list_customers_command() -> None:
    """List customers (requires authentication)"""
    print("Customers List")
    print("=" * 20)
    current_user = auth_manager.get_current_user()
    print(f"Logged in as: {current_user['name']} ({current_user['role']})")
    print("Implementation here...")


@cli_permission_required(Permission.CREATE_CUSTOMER)
def create_customer_command() -> None:
    """Create new customer (requires CREATE_CUSTOMER permission)"""
    print("Create New Customer")
    print("=" * 25)
    print("Implementation here...")


@cli_permission_required(Permission.DELETE_CUSTOMER)
def delete_customer_command() -> None:
    """Delete customer (requires DELETE_CUSTOMER permission)"""
    print(" Delete Customer")
    print("=" * 20)
    print("Implementation here...")


@auto_refresh_token
@cli_auth_required
def long_operation_command() -> None:
    """Example of long operation with auto token refresh"""
    print("Long Operation (with auto token refresh)")
    print("=" * 45)
    import time
    for i in range(5):
        print(f"Step {i+1}/5...")
        time.sleep(1)
        # Token is automatically refreshed if needed
    print("Operation completed!")


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


@cli_admin_required
def admin_users_command() -> None:
    """Admin-only command to manage users"""
    print("Admin Users Management")
    print("=" * 25)
    print("This is an admin-only function.")
    print("Only users with 'admin' role can access this.")


@cli_management_or_admin_required
def reports_command() -> None:
    """Management or admin command for reports"""
    print("Management Reports")
    print("=" * 20)
    user = auth_manager.get_current_user()
    print(f"Accessing reports as: {user['role']}")
    print("This command requires management or admin role.")


@cli_role_required('sales', 'management', 'admin')
def sales_dashboard_command() -> None:
    """Sales dashboard - requires sales, management or admin role"""
    print("Sales Dashboard")
    print("=" * 18)
    user = auth_manager.get_current_user()
    print(f"Welcome to sales dashboard, {user['name']} ({user['role']})")
    print("Sales metrics and customer data here...")


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
    print("  list-customers    - List all customers")
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
        'create-customer': create_customer_command,
        'delete-customer': delete_customer_command,
        'admin-users': admin_users_command,
        'reports': reports_command,
        'sales-dashboard': sales_dashboard_command,
        'long-operation': long_operation_command,
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
