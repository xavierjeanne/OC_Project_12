"""
Sentry configuration for Epic Events CRM
Centralized management of error monitoring and logs
"""

import os
import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from typing import Optional

# Configuration du logger
logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry for error and performance monitoring.

    Secure configuration:
    - DSN read from environment variables
    - No personal data (PII) sent by default
    - Integrations for logging and SQLAlchemy
    """

    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.warning(
            "SENTRY_DSN not found in environment variables. Sentry monitoring disabled."
        )
        return

    environment = os.getenv("ENVIRONMENT", "development")

    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            integrations=[
                sentry_logging,
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% des transactions pour éviter le spam
            send_default_pii=False,
            release=get_app_version(),
            before_send=filter_sensitive_data,
        )

        logger.info(f"Sentry initialized successfully for environment: {environment}")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def get_app_version() -> str:
    """
    Retrieve the application version.

    Returns:
        Application version or 'unknown'
    """
    return os.getenv("APP_VERSION", "1.0.0")


def filter_sensitive_data(event, hint):
    """
    Filter sensitive data before sending to Sentry.

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        Filtered event or None if it should be ignored
    """

    # Filter sensitive data in error messages
    if "message" in event:
        message = event["message"]
        if isinstance(message, str):
            import re

            # Mask potential passwords and secrets with precise regex
            sensitive_patterns = [
                r"password[:\s]*[\w\-\.\@]+",
                r"token[:\s]*[\w\-\.\@]+",
                r"secret[:\s]*[\w\-\.\@]+",
                r"key[:\s]*[\w\-\.\@]+",
            ]

            for pattern in sensitive_patterns:
                event["message"] = re.sub(
                    pattern, "***FILTERED***", message, flags=re.IGNORECASE
                )
                message = event["message"]  # Update for next iteration

    # Filter sensitive data in local variables
    if "exception" in event and "values" in event["exception"]:
        for exception in event["exception"]["values"]:
            if "stacktrace" in exception and "frames" in exception["stacktrace"]:
                for frame in exception["stacktrace"]["frames"]:
                    if "vars" in frame:
                        for var_name, var_value in frame["vars"].items():
                            if any(
                                sensitive in var_name.lower()
                                for sensitive in ["password", "token", "secret", "key"]
                            ):
                                frame["vars"][var_name] = "***FILTERED***"

    return event


# Helper functions for business-level logging


def log_employee_creation(
    employee_id: int, employee_name: str, created_by: str
) -> None:
    """
    Log employee creation

    Args:
        employee_id: ID of the created employee
        employee_name: Name of the employee
        created_by: Email of the creator
    """
    sentry_sdk.add_breadcrumb(
        message=f"Employee created: {employee_name}",
        category="employee.create",
        data={
            "employee_id": employee_id,
            "employee_name": employee_name,
            "created_by": created_by,
        },
        level="info",
    )

    logger.info(
        f"Employee created - ID: {employee_id},"
        f"Name: {employee_name}, Created by: {created_by}"
    )


def log_employee_update(
    employee_id: int, employee_name: str, updated_by: str, changes: dict
) -> None:
    """
    Log employee update

    Args:
        employee_id: ID of the updated employee
        employee_name: Name of the employee
        updated_by: Email of the updater
        changes: Dictionary of changes made
    """
    sentry_sdk.add_breadcrumb(
        message=f"Employee updated: {employee_name}",
        category="employee.update",
        data={
            "employee_id": employee_id,
            "employee_name": employee_name,
            "updated_by": updated_by,
            "changes": changes,
        },
        level="info",
    )

    logger.info(
        f"Employee updated - ID: {employee_id}, Name: {employee_name}, "
        f"Updated by: {updated_by}, Changes: {changes}"
    )


def log_contract_signature(
    contract_id: int, customer_name: str, signed_by: str, amount: float
) -> None:
    """
    Log contract signature

    Args:
        contract_id: ID of the signed contract
        customer_name: Customer name
        signed_by: Email of the signer
        amount: Contract amount
    """
    sentry_sdk.add_breadcrumb(
        message=f"Contract signed: #{contract_id} for {customer_name}",
        category="contract.signature",
        data={
            "contract_id": contract_id,
            "customer_name": customer_name,
            "signed_by": signed_by,
            "amount": amount,
        },
        level="info",
    )

    # Important log for business traceability
    logger.info(
        f"CONTRACT SIGNED - ID: {contract_id}, Customer: {customer_name}, "
        f"Amount: €{amount:,.2f}, Signed by: {signed_by}"
    )

    # Also create a Sentry event for high-value signatures
    if amount >= 10000:  # High-value contracts
        sentry_sdk.capture_message(
            f"High-value contract signed: €{amount:,.2f} for {customer_name}",
            level="info",
        )


def log_unexpected_error(error: Exception, context: Optional[dict] = None) -> None:
    """
    Log an unexpected error with context

    Args:
        error: Captured Exception
        context: Additional context (optional)
    """
    if context:
        sentry_sdk.set_context("error_context", context)

    # Capturer l'exception dans Sentry
    sentry_sdk.capture_exception(error)

    logger.error(f"Unexpected error occurred: {str(error)}", exc_info=True)


# Decorator to automatically capture exceptions


def capture_exceptions(func):
    """
    Decorator to automatically capture unexpected exceptions

    Usage:
        @capture_exceptions


        def my_function():
            # code that may raise an exception
            pass
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_unexpected_error(
                e,
                context={
                    "function": func.__name__,
                    "args": str(args)[:100],  # Limiter la taille
                    "kwargs": str(kwargs)[:100],
                },
            )
            raise  # Re-lever l'exception après logging

    return wrapper
