"""
Business data validation module
Validations for emails, amounts, dates, etc.
"""

import re
from datetime import datetime
from typing import Optional, Tuple


class ValidationError(Exception):
    """Exception raised during validation errors"""

    pass


def validate_email(email: str) -> str:
    """
    Validates that an email address is correct

    Args:
        email: The email address to validate

    Returns:
        The validated email (stripped and lowercase)

    Raises:
        ValidationError: If the email is invalid
    """
    if not email:
        raise ValidationError("Email is required")

    email = email.strip().lower()

    # Basic but robust regex for email
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError(f"Email '{email}' is not valid")

    return email


def validate_phone(phone: Optional[str]) -> Optional[str]:
    """
    Validates a phone number (optional)

    Args:
        phone: The phone number to validate

    Returns:
        The validated phone (cleaned of spaces)

    Raises:
        ValidationError: If the phone is invalid
    """
    if not phone:
        return None

    phone = phone.strip()

    # Accepts different formats: 0123456789, 01 23 45 67 89, +33123456789, etc.
    phone_clean = re.sub(r"[\s\-\.\(\)]", "", phone)

    if not re.match(r"^\+?[0-9]{10,15}$", phone_clean):
        raise ValidationError(f"Phone number '{phone}' is not valid")

    return phone


def validate_positive_amount(amount: float, field_name: str = "amount") -> float:
    """
    Validates that an amount is positive

    Args:
        amount: The amount to validate
        field_name: Field name for error message

    Returns:
        The validated amount

    Raises:
        ValidationError: If the amount is negative or zero
    """
    if amount is None:
        raise ValidationError(f"The {field_name} is required")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValidationError(f"The {field_name} must be a number")

    if amount <= 0:
        raise ValidationError(f"The {field_name} must be positive (received: {amount})")

    return amount


def validate_non_negative_amount(amount: float, field_name: str = "amount") -> float:
    """
    Validates that an amount is non-negative (can be 0)

    Args:
        amount: The amount to validate
        field_name: Field name for error message

    Returns:
        The validated amount

    Raises:
        ValidationError: If the amount is negative
    """
    if amount is None:
        raise ValidationError(f"The {field_name} is required")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValidationError(f"The {field_name} must be a number")

    if amount < 0:
        raise ValidationError(
            f"The {field_name} cannot be negative (received: {amount})"
        )

    return amount


def validate_remaining_amount(total: float, remaining: float) -> None:
    """
    Validates that the remaining amount is not greater than the total

    Args:
        total: The total amount
        remaining: The remaining amount

    Raises:
        ValidationError: If remaining > total
    """
    if remaining > total:
        raise ValidationError(
            f"The remaining amount ({remaining}) cannot be greater than "
            f"the total amount ({total})"
        )


def validate_date_order(
    start_date: datetime,
    end_date: datetime,
    start_field_name: str = "start date",
    end_field_name: str = "end date",
) -> None:
    """
    Validates that the start date is before the end date

    Args:
        start_date: Start date
        end_date: End date
        start_field_name: Start field name (for error messages)
        end_field_name: End field name (for error messages)

    Raises:
        ValidationError: If start_date >= end_date
    """
    if start_date >= end_date:
        raise ValidationError(
            f"The {start_field_name} ({start_date}) must be before "
            f"the {end_field_name} ({end_date})"
        )


def validate_positive_integer(value: int, field_name: str = "value") -> int:
    """
    Validates that a value is a positive integer

    Args:
        value: The value to validate
        field_name: Field name for error message

    Returns:
        The validated value

    Raises:
        ValidationError: If the value is not a positive integer
    """
    if value is None:
        raise ValidationError(f"The {field_name} field is required")

    try:
        value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"The {field_name} field must be an integer")

    if value <= 0:
        raise ValidationError(
            f"The {field_name} field must be positive (received: {value})"
        )

    return value


def validate_role(role: str) -> str:
    """
    Validates that a role is one of the authorized roles

    Args:
        role: The role to validate

    Returns:
        The validated role (lowercase)

    Raises:
        ValidationError: If the role is not valid
    """
    if not role:
        raise ValidationError("Role is required")

    role = role.strip().lower()
    valid_roles = ["sales", "support", "management"]

    if role not in valid_roles:
        raise ValidationError(
            f"Role '{role}' is not valid. " f"Accepted roles: {', '.join(valid_roles)}"
        )

    return role


def validate_string_not_empty(value: str, field_name: str = "field") -> str:
    """
    Validates that a string is not empty

    Args:
        value: The value to validate
        field_name: Field name for error message

    Returns:
        The validated value (stripped)

    Raises:
        ValidationError: If the value is empty
    """
    if not value or not value.strip():
        raise ValidationError(f"The {field_name} field is required and cannot be empty")

    return value.strip()


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements

    Args:
        password: Plain text password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"

    return True, "Password is valid"
