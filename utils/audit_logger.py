"""
Journalisattion system for Epic Events CRM
Centralized logging for critical actions and important traceability
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import sentry_sdk
from utils.sentry_config import capture_exceptions


class CRMLogger:
    """Centralized logger for all critical actions in the CRM"""
    
    def __init__(self):
        # Main logger configuration 
        self.logger = logging.getLogger('crm_audit')
        self.logger.setLevel(logging.INFO)
        
        pass
    
    def _format_log_data(self, action: str, user_info: Dict[str, Any], 
                        entity_type: str, entity_data: Dict[str, Any],
                        additional_info: Optional[Dict[str, Any]] = None) -> str:
        """Format log data in a structured way"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user": {
                "id": user_info.get("id"),
                "employee_number": user_info.get("employee_number"),
                "role": user_info.get("role"),
                "full_name": user_info.get("full_name")
            },
            "entity": {
                "type": entity_type,
                "data": entity_data
            }
        }
        
        if additional_info:
            log_data["additional_info"] = additional_info
            
        return json.dumps(log_data, ensure_ascii=False)
    
    def log_employee_creation(self, user_info: Dict[str, Any], 
                             employee_data: Dict[str, Any]) -> None:
        """Log employee creation - SENTRY ONLY"""
        
        # Send directly to Sentry with enriched context
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("action", "employee_creation")
            scope.set_tag("user_role", user_info.get("role"))
            scope.set_tag("employee_role", employee_data.get("role"))
            
            # Acting user context
            scope.set_context("acting_user", {
                "id": user_info.get("id"),
                "employee_number": user_info.get("employee_number"),
                "role": user_info.get("role"),
                "full_name": user_info.get("full_name")
            })
            
            # Created employee context
            scope.set_context("created_employee", {
                "full_name": employee_data.get("full_name"),
                "employee_number": employee_data.get("employee_number"),
                "email": employee_data.get("email"),
                "role": employee_data.get("role")
            })
            
            # Message principal avec fallback pour éviter "by None"
            creator_name = user_info.get('full_name') or user_info.get('employee_number') or f"User #{user_info.get('id', 'Unknown')}"
            message = f"Employee created: {employee_data.get('full_name')} ({employee_data.get('employee_number')}) by {creator_name}"
            sentry_sdk.capture_message(message, level="info")
    
    def log_employee_modification(self, user_info: Dict[str, Any], 
                                 employee_id: str, changes: Dict[str, Any]) -> None:
        """Log employee modification """
        
        # Send directly to Sentry with enriched context
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("action", "employee_modification")
            scope.set_tag("user_role", user_info.get("role"))
            scope.set_tag("employee_id", str(employee_id))
            
            # Acting user context
            scope.set_context("acting_user", {
                "id": user_info.get("id"),
                "employee_number": user_info.get("employee_number"),
                "role": user_info.get("role"),
                "full_name": user_info.get("full_name")
            })
            
            # Modification context
            scope.set_context("employee_changes", {
                "employee_id": employee_id,
                "changes": changes,
                "change_count": len(changes)
            })
            
            # Main message with details of changes et fallback
            changed_fields = list(changes.keys())
            modifier_name = user_info.get('full_name') or user_info.get('employee_number') or f"User #{user_info.get('id', 'Unknown')}"
            message = f"Employee {employee_id} modified by {modifier_name}: {', '.join(changed_fields)}"
            sentry_sdk.capture_message(message, level="info")
    
    def log_contract_signature(self, user_info: Dict[str, Any], 
                              contract_data: Dict[str, Any]) -> None:
        """Log contract signature - CRITICAL ACTION - SENTRY ONLY"""
        
        # Send directly to Sentry with WARNING level (business critical)
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("action", "contract_signature")
            scope.set_tag("business_impact", "CRITICAL")
            scope.set_tag("user_role", user_info.get("role"))
            scope.set_tag("contract_amount", str(contract_data.get("total_amount", 0)))
            
            # Signer context
            scope.set_context("signer", {
                "id": user_info.get("id"),
                "employee_number": user_info.get("employee_number"),
                "role": user_info.get("role"),
                "full_name": user_info.get("full_name")
            })
            
            # Signed contract context
            scope.set_context("signed_contract", {
                "contract_id": contract_data.get("id"),
                "customer_id": contract_data.get("customer_id"),
                "total_amount": contract_data.get("total_amount"),
                "sales_contact_id": contract_data.get("sales_contact_id"),
                "signature_timestamp": datetime.now().isoformat(),
                "previous_signed_status": contract_data.get("previous_signed_status", False)
            })
            
            # Critical message avec fallback
            amount = contract_data.get("total_amount", 0)
            signer_name = user_info.get('full_name') or user_info.get('employee_number') or f"User #{user_info.get('id', 'Unknown')}"
            message = f"Contract {contract_data.get('id')} signed for {amount}€ by {signer_name} ({user_info.get('role')})"
            sentry_sdk.capture_message(message, level="warning")
    
    def log_unexpected_exception(self, exception: Exception, context: Dict[str, Any]) -> None:
        """Log all unexpected exceptions - SENTRY ONLY"""
        
        # Send directly to Sentry with enriched context
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("exception_type", type(exception).__name__)
            scope.set_tag("service", context.get("service", "unknown"))
            scope.set_tag("operation", context.get("operation", "unknown"))
            
            # Complete error context
            scope.set_context("error_details", {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "timestamp": datetime.now().isoformat()
            })
            
            scope.set_context("execution_context", context)
            
            # Capture the exception with its full stack trace
            sentry_sdk.capture_exception(exception)


# Global logger instance
crm_logger = CRMLogger()


def log_critical_action(action_type: str):
    """
    DDecorator to automatically log critical actions
    
    Usage:
    @log_critical_action("employee_creation")
    def create_employee(self, data, user):
        ...
    
    @log_critical_action("contract_signature")
    def update_contract(self, contract_id, data, user):
        ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # If it's a service method, retrieve context info
                if hasattr(args[0], '__class__') and 'Service' in args[0].__class__.__name__:
                    # Try to retrieve user_info from arguments
                    current_user = None
                    for arg in args[1:]:
                        if isinstance(arg, dict) and 'role' in arg:
                            current_user = arg
                            break
                    
                    if current_user and action_type == "employee_creation":
                        crm_logger.log_employee_creation(current_user, kwargs)
                    elif current_user and action_type == "employee_modification":
                        crm_logger.log_employee_modification(current_user, args[1], kwargs)
                    elif current_user and action_type == "contract_signature":
                        crm_logger.log_contract_signature(current_user, kwargs)
                
                return result
                
            except Exception as e:
                # Log unexpected exception
                context = {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "action_type": action_type
                }
                crm_logger.log_unexpected_exception(e, context)
                raise  # Re-raise the exception
                
        return wrapper
    return decorator


def log_exception_with_context(**context_data):
    """
    DDecorator to capture all exceptions with context
    
    Usage:
    @log_exception_with_context(service="CustomerService", operation="create")
    def create_customer(self, data):
        ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Enrich context with function information
                full_context = {
                    "function": f"{func.__module__}.{func.__name__}",
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    **context_data
                }
                
                crm_logger.log_unexpected_exception(e, full_context)
                raise  # Re-raise the exception
                
        return wrapper
    return decorator