"""
JWT Service for Epic Events CRM
Handles JWT token creation, validation, and management
"""

import jwt
import os
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from pathlib import Path

from models import Employee


class JWTService:
    """Service for JWT token management"""

    def __init__(self):
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def _get_secret_key(self) -> str:
        """
        Get JWT secret key from environment or generate one

        Returns:
            Secret key for JWT signing
        """
        # Try to get from environment first
        secret = os.getenv("EPIC_EVENTS_JWT_SECRET")

        if not secret:
            # Generate a new secret and save it to .env file
            import secrets

            secret = secrets.token_urlsafe(32)

            # Create/update .env file
            env_file = Path(".env")
            env_content = ""

            if env_file.exists():
                env_content = env_file.read_text()

            # Add or update the secret
            if "EPIC_EVENTS_JWT_SECRET=" in env_content:
                lines = env_content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("EPIC_EVENTS_JWT_SECRET="):
                        lines[i] = f"EPIC_EVENTS_JWT_SECRET={secret}"
                        break
                env_content = "\n".join(lines)
            else:
                if env_content and not env_content.endswith("\n"):
                    env_content += "\n"
                env_content += f"EPIC_EVENTS_JWT_SECRET={secret}\n"

            env_file.write_text(env_content)
            print("New JWT secret generated and saved to .env file")

        return secret

    def create_access_token(self, employee_data: dict) -> str:
        """
        Create an access token for the authenticated employee

        Args:
            employee_data: Dict with employee information

        Returns:
            JWT access token string
        """
        expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(employee_data["id"]),  # Subject (user ID)
            "employee_number": employee_data["employee_number"],
            "name": employee_data["name"],
            "email": employee_data["email"],
            "role": employee_data["role"],
            "role_id": employee_data["role_id"],
            "exp": expire,
            "iat": datetime.now(UTC),  # Issued at
            "type": "access",
        }

        secret = self._get_secret_key()
        return jwt.encode(payload, secret, algorithm=self.algorithm)

    def create_refresh_token(self, employee_data: dict) -> str:
        """
        Create a refresh token for token renewal

        Args:
            employee_data: Dict with employee information

        Returns:
            JWT refresh token string
        """
        expire = datetime.now(UTC) + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": str(employee_data["id"]),
            "employee_number": employee_data["employee_number"],
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",
        }

        secret = self._get_secret_key()
        return jwt.encode(payload, secret, algorithm=self.algorithm)

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            secret = self._get_secret_key()
            payload = jwt.decode(token, secret, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("type") != token_type:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            print("🚨 Token expired")
            return None
        except jwt.InvalidTokenError:
            print("🚨 Invalid token")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create a new access token from a valid refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token or None if refresh token is invalid
        """
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        # Get employee from database to create new access token
        from models import Session

        session = Session()
        try:
            employee = (
                session.query(Employee)
                .filter_by(employee_number=payload["employee_number"])
                .first()
            )

            if employee:
                # Extract data within session
                employee_data = {
                    "id": employee.id,
                    "employee_number": employee.employee_number,
                    "name": employee.name,
                    "email": employee.email,
                    "role": employee.role,  # employee.role is already the role name
                    "role_id": employee.role_id,
                }
                return self.create_access_token(employee_data)
            return None

        finally:
            session.close()
