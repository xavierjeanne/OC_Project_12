"""
Authentication Manager for Epic Events CRM
Handles persistent authentication, token storage, and session management
"""

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any

from sqlalchemy.orm import joinedload
from models import Employee, Session
from services.auth import AuthService
from services.jwt_service import JWTService
from utils.permissions import Permission, has_permission


class AuthenticationManager:
    """Manages authentication state and token persistence"""

    def __init__(self):
        self.auth_service = AuthService()
        self.jwt_service = JWTService()
        self.token_file = Path.home() / '.epic_events_tokens'
        self.current_user = None

    def login(self, employee_number: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and create persistent session

        Args:
            employee_number: Employee number
            password: Plain text password

        Returns:
            Dict with success status and user info
        """
        # Authenticate with existing AuthService
        success, employee_data, message = self.auth_service.authenticate_user(
            employee_number, password
        )

        if not success:
            return {
                "success": False,
                "message": message,
                "user": None,
                "tokens": None
            }

        # Create JWT tokens (employee_data is already a dict)
        access_token = self.jwt_service.create_access_token(employee_data)
        refresh_token = self.jwt_service.create_refresh_token(employee_data)

        # Store tokens securely
        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "created_at": datetime.now(UTC).isoformat()
        }

        self._save_tokens(tokens)

        # Set current user session
        self.current_user = employee_data

        return {
            "success": True,
            "message": f"Welcome {employee_data['name']}! You are now logged in.",
            "user": self.current_user,
            "tokens": tokens
        }

    def logout(self) -> Dict[str, str]:
        """
        Logout current user and clean tokens

        Returns:
            Dict with logout status
        """
        # Clear tokens file
        if self.token_file.exists():
            self.token_file.unlink()

        # Clear current session
        user_name = (self.current_user.get("name", "User")
                     if self.current_user else "User")
        self.current_user = None

        return {
            "success": True,
            "message": f"Goodbye {user_name}! You have been logged out."
        }

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get currently authenticated user from stored tokens

        Returns:
            Current user info or None if not authenticated
        """
        if self.current_user:
            return self.current_user

        # Try to restore session from stored tokens
        tokens = self._load_tokens()
        if not tokens:
            return None

        # Verify access token
        payload = self.jwt_service.verify_token(tokens["access_token"])
        if payload:
            # Token is valid, restore user session
            self.current_user = {
                "id": int(payload["sub"]),
                "employee_number": payload["employee_number"],
                "name": payload["name"],
                "email": payload["email"],
                "role": payload["role"],
                "role_id": payload["role_id"]
            }
            return self.current_user

        # Access token expired, try refresh
        new_access_token = self.jwt_service.refresh_access_token(
            tokens["refresh_token"])
        if new_access_token:
            # Update stored tokens
            tokens["access_token"] = new_access_token
            tokens["created_at"] = datetime.now(UTC).isoformat()
            self._save_tokens(tokens)

            # Verify new token and restore session
            payload = self.jwt_service.verify_token(new_access_token)
            if payload:
                self.current_user = {
                    "id": int(payload["sub"]),
                    "employee_number": payload["employee_number"],
                    "name": payload["name"],
                    "email": payload["email"],
                    "role": payload["role"],
                    "role_id": payload["role_id"]
                }
                print("Token refreshed automatically")
                return self.current_user

        # All tokens expired, clean up
        self.logout()
        return None

    def require_authentication(self) -> bool:
        """
        Check if user is authenticated, print message if not

        Returns:
            True if authenticated, False otherwise
        """
        user = self.get_current_user()
        if not user:
            print("You must be logged in to perform this action.")
            print("   Use: python -m cli.main login")
            return False
        return True

    def require_permission(self, permission: Permission) -> bool:
        """
        Check if current user has required permission

        Args:
            permission: Required permission

        Returns:
            True if user has permission, False otherwise
        """
        if not self.require_authentication():
            return False

        # Get full employee object for permission check
        session = Session()
        try:
            employee = (session.query(Employee)
                        .filter(Employee.id == self.current_user["id"])
                        .first())
            if not employee:
                print("User session invalid")
                self.logout()
                return False

            if not has_permission(employee, permission):
                print(f"Access denied. You don't have permission: {permission.value}")
                print(f"Your role '{employee.role}' cannot perform this action.")
                return False

            return True

        finally:
            session.close()

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information

        Returns:
            Session details or None if not authenticated
        """
        user = self.get_current_user()
        if not user:
            return None

        tokens = self._load_tokens()
        if not tokens:
            return None

        # Decode token for expiry info
        payload = self.jwt_service.verify_token(tokens["access_token"])
        if not payload:
            return None

        expires_at = datetime.fromtimestamp(payload["exp"], UTC)
        time_until_expiry = expires_at - datetime.now(UTC)

        return {
            "user": user,
            "token_expires_at": expires_at.isoformat(),
            "time_until_expiry_minutes": max(0, time_until_expiry.total_seconds() / 60),
            "logged_in_at": tokens.get("created_at")
        }

    def _save_tokens(self, tokens: Dict[str, str]) -> None:
        """
        Save tokens to secure local file

        Args:
            tokens: Dict containing access and refresh tokens
        """
        try:
            # Create file with restricted permissions (owner only)
            self.token_file.touch(mode=0o600, exist_ok=True)

            with self.token_file.open('w') as f:
                json.dump(tokens, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save tokens: {e}")

    def _load_tokens(self) -> Optional[Dict[str, str]]:
        """
        Load tokens from local file

        Returns:
            Dict with tokens or None if not found
        """
        if not self.token_file.exists():
            return None

        try:
            with self.token_file.open('r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load tokens: {e}")
            return None


# Global instance for application-wide use
auth_manager = AuthenticationManager()
