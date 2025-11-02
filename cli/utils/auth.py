"""
CLI Authentication Module
Handles user authentication for CLI commands
"""

import click
from services.auth_manager import auth_manager
from utils.permissions import Permission, PermissionError


def cli_auth_required(func):
    """
    Decorator to ensure user is authenticated before accessing CLI commands
    """
    def wrapper(*args, **kwargs):
        if not auth_manager.require_authentication():
            click.echo(click.style('Authentication required. Please login first.', fg='red'))
            click.echo(click.style('Use: python -m cli.main login', fg='yellow'))
            raise click.Abort()
        return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def get_current_user():
    """
    Get currently authenticated user
    
    Returns:
        User dict or None if not authenticated
    """
    return auth_manager.get_current_user()


def require_permission(permission: Permission):
    """
    Decorator to check user permissions for CLI commands
    
    Args:
        permission: Required permission
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not auth_manager.require_permission(permission):
                click.echo(click.style(f'Permission denied. Required permission: {permission.value}', fg='red'))
                raise click.Abort()
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def check_authentication():
    """
    Check if user is currently authenticated
    
    Returns:
        True if authenticated, False otherwise
    """
    return auth_manager.get_current_user() is not None