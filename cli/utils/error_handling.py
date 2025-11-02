"""
Centralized error handling for Epic Events CLI application
"""

import click
from typing import Any, Callable, Optional
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DisconnectionError
from utils.validators import ValidationError
from utils.permissions import PermissionError
import logging

logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Base exception for CLI errors"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class DatabaseConnectionError(CLIError):
    """Database connection error"""
    pass


class ResourceNotFoundError(CLIError):
    """Resource not found error"""
    pass


class BusinessLogicError(CLIError):
    """Business logic error"""
    pass


def handle_cli_errors(func: Callable) -> Callable:
    """
    Decorator to handle CLI errors with user-friendly messages
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        
        except PermissionError as e:
            click.echo(click.style(
                f"❌ Access denied: {e}", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 Tip: Check that you have the necessary permissions for this action.",
                fg='yellow'
            ))
            logger.warning(f"Permission denied in {func.__name__}: {e}")
            raise click.Abort()
        
        except ValidationError as e:
            click.echo(click.style(
                f"⚠️  Invalid data: {e}", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 Tip: Check the format of your data (email, phone, amounts, etc.)",
                fg='yellow'
            ))
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise click.Abort()
        
        except IntegrityError as e:
            click.echo(click.style(
                "❌ Data conflict: This operation violates a database constraint.", 
                fg='red', bold=True
            ))
            if "email" in str(e).lower():
                click.echo(click.style(
                    "💡 This email address is already in use.",
                    fg='yellow'
                ))
            elif "employee_number" in str(e).lower():
                click.echo(click.style(
                    "💡 This employee number already exists.",
                    fg='yellow'
                ))
            else:
                click.echo(click.style(
                    "💡 Check that the data doesn't already exist.",
                    fg='yellow'
                ))
            logger.error(f"Integrity error in {func.__name__}: {e}")
            raise click.Abort()
        
        except DisconnectionError as e:
            click.echo(click.style(
                "❌ Connection error: Unable to connect to the database.", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 Check that the database is accessible and connection settings are correct.",
                fg='yellow'
            ))
            logger.error(f"Database connection error in {func.__name__}: {e}")
            raise click.Abort()
        
        except SQLAlchemyError as e:
            click.echo(click.style(
                "❌ Database error: An error occurred while accessing data.", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 This error has been logged. Contact the administrator if the problem persists.",
                fg='yellow'
            ))
            logger.error(f"SQLAlchemy error in {func.__name__}: {e}")
            raise click.Abort()
        
        except ResourceNotFoundError as e:
            click.echo(click.style(
                f"❌ Resource not found: {e.message}", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 Check the ID or use the 'list' command to see available resources.",
                fg='yellow'
            ))
            logger.warning(f"Resource not found in {func.__name__}: {e}")
            raise click.Abort()
        
        except BusinessLogicError as e:
            click.echo(click.style(
                f"❌ Business error: {e.message}", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 This action is not allowed in the current context.",
                fg='yellow'
            ))
            logger.warning(f"Business logic error in {func.__name__}: {e}")
            raise click.Abort()
        
        except DatabaseConnectionError as e:
            click.echo(click.style(
                f"❌ Database connection: {e.message}", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 Check connection settings in config.py",
                fg='yellow'
            ))
            logger.error(f"Database connection error in {func.__name__}: {e}")
            raise click.Abort()
        
        except KeyboardInterrupt:
            click.echo(click.style(
                "\n⚠️  Operation cancelled by user.", 
                fg='yellow', bold=True
            ))
            raise click.Abort()
        
        except Exception as e:
            click.echo(click.style(
                f"❌ Unexpected error: {str(e)}", 
                fg='red', bold=True
            ))
            click.echo(click.style(
                "💡 This error has been logged. Contact the administrator.",
                fg='yellow'
            ))
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise click.Abort()
    
    return wrapper


def validate_positive_number(value: Any, field_name: str) -> float:
    """Validate that a number is positive"""
    try:
        num = float(value)
        if num <= 0:
            raise ValidationError(f"{field_name} must be a positive number (received: {value})")
        return num
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number (received: {value})")


def validate_id(value: Any, resource_name: str = "ID") -> int:
    """Validate that an ID is a positive integer"""
    try:
        id_val = int(value)
        if id_val <= 0:
            raise ValidationError(f"{resource_name} must be a positive integer (received: {value})")
        return id_val
    except (ValueError, TypeError):
        raise ValidationError(f"{resource_name} must be a valid integer (received: {value})")


def validate_date_format(date_str: str, field_name: str = "Date") -> str:
    """Validate date format YYYY-MM-DD"""
    if not date_str:
        return date_str
    
    import re
    from datetime import datetime
    
    # Check YYYY-MM-DD format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format (received: {date_str})")
    
    # Check that the date is valid
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValidationError(f"{field_name} is not a valid date (received: {date_str})")
    
    return date_str


def confirm_destructive_action(action_description: str) -> bool:
    """
    Ask for confirmation for destructive actions
    """
    click.echo(click.style(
        f"⚠️  Destructive action: {action_description}", 
        fg='yellow', bold=True
    ))
    return click.confirm(
        click.style("Are you sure you want to continue?", fg='red'),
        default=False
    )


def display_success_message(message: str, details: Optional[dict] = None):
    """Display a formatted success message"""
    click.echo(click.style(f"✅ {message}", fg='green', bold=True))
    if details:
        for key, value in details.items():
            click.echo(f"   {key}: {value}")


def display_info_message(message: str):
    """Display a formatted information message"""
    click.echo(click.style(f"ℹ️  {message}", fg='blue'))


def display_warning_message(message: str):
    """Display a formatted warning message"""
    click.echo(click.style(f"⚠️  {message}", fg='yellow', bold=True))