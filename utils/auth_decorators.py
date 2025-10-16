"""
Authentication and Authorization Decorators for CLI
Decorators for JWT token verification and permission checking in CLI commands only
"""

import functools
from typing import Callable

from services.auth_manager import auth_manager
from utils.permissions import Permission


def cli_auth_required(f: Callable) -> Callable:
    """
    Decorator for CLI commands that require authentication

    Usage:
        @cli_auth_required
        def list_customers():
            print("Listing customers...")
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not auth_manager.require_authentication():
            return
        return f(*args, **kwargs)
    return wrapper


def cli_permission_required(permission: Permission):
    """
    Decorator for CLI commands that require specific permission

    Usage:
        @cli_permission_required(Permission.CREATE_CUSTOMER)
        def create_customer():
            print("Creating customer...")
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not auth_manager.require_permission(permission):
                return
            return f(*args, **kwargs)
        return wrapper
    return decorator


def auto_refresh_token(f: Callable) -> Callable:
    """
    Decorator that automatically refreshes expired tokens
    For CLI commands that need seamless token refresh

    Usage:
        @auto_refresh_token
        def long_running_operation():
            # Token will be refreshed if needed
            pass
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Force token check and refresh if needed
        current_user = auth_manager.get_current_user()
        if not current_user:
            print("Authentication required. Please login first.")
            return

        return f(*args, **kwargs)
    return wrapper


def cli_role_required(*required_roles: str):
    """
    Decorator for CLI commands that require specific role(s)

    Usage:
        @cli_role_required('management', 'admin')
        def admin_function():
            print("Admin function")
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Check authentication first
            current_user = auth_manager.get_current_user()
            if not current_user:
                print("Authentication required. Please login first.")
                return

            user_role = current_user.get('role')
            if user_role not in required_roles:
                print(f"Access denied. Required roles: {', '.join(required_roles)}")
                print(f"   Your role: {user_role}")
                return

            return f(*args, **kwargs)
        return wrapper
    return decorator


def with_user_context(f: Callable) -> Callable:
    """
    Decorator that provides current user context to CLI commands

    Usage:
        @with_user_context
        def my_command(user=None):
            print(f"Hello {user['name']}")
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        current_user = auth_manager.get_current_user()
        if not current_user:
            print("Authentication required. Please login first.")
            return

        # Add user to kwargs if the function accepts it
        if 'user' in f.__code__.co_varnames:
            kwargs['user'] = current_user

        return f(*args, **kwargs)
    return wrapper


# Convenience decorators for common role combinations
def cli_admin_required(f: Callable) -> Callable:
    """
    Shortcut decorator for admin-only CLI commands
    """
    @cli_role_required('admin')
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


def cli_management_or_admin_required(f: Callable) -> Callable:
    """
    Shortcut decorator for management+ level CLI commands
    """
    @cli_role_required('management', 'admin')
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


def cli_sales_or_management_required(f: Callable) -> Callable:
    """
    Decorator for sales or management level CLI commands
    """
    @cli_role_required('sales', 'management', 'admin')
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper
