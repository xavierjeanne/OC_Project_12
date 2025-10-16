"""
Authentication service for password hashing and user authentication
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
from datetime import datetime, timedelta
from typing import Optional, Tuple
from models import Employee, Session
import logging

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


class AuthService:
    """Service for user authentication and password management"""

    def __init__(self):
        # Configure Argon2 parameters
        self.ph = PasswordHasher(
            time_cost=3,        # Number of iterations
            memory_cost=65536,  # Memory used (64 MB)
            parallelism=1,      # Number of parallel threads
            hash_len=32,        # Length of the hash
            salt_len=16         # Length of the salt
        )
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2

        Args:
            password: Plain text password

        Returns:
            Hashed password string

        Raises:
            HashingError: If hashing fails
        """
        try:
            return self.ph.hash(password)
        except HashingError as e:
            logger.error(f"Password hashing failed: {e}")
            raise

    def verify_password(self, hashed_password: str, password: str) -> bool:
        """
        Verify a password against its hash

        Args:
            hashed_password: Stored hash
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        try:
            self.ph.verify(hashed_password, password)
            return True
        except VerifyMismatchError:
            return False

    def is_account_locked(self, employee: Employee) -> bool:
        """
        Check if employee account is locked

        Args:
            employee: Employee instance

        Returns:
            True if account is locked, False otherwise
        """
        if not employee.locked_until:
            return False

        return datetime.now() < employee.locked_until

    def increment_failed_attempts(self, employee: Employee, session: Session) -> None:
        """
        Increment failed login attempts and lock account if necessary

        Args:
            employee: Employee instance
            session: Database session
        """
        employee.failed_login_attempts += 1

        if employee.failed_login_attempts >= self.max_attempts:
            employee.locked_until = datetime.now() + self.lockout_duration
            logger.warning(f"Account locked for employee {employee.employee_number}")

        session.commit()

    def reset_failed_attempts(self, employee: Employee, session: Session) -> None:
        """
        Reset failed login attempts after successful login

        Args:
            employee: Employee instance
            session: Database session
        """
        employee.failed_login_attempts = 0
        employee.locked_until = None
        employee.last_login = datetime.now()
        session.commit()

    def authenticate_user(
                        self,
                        employee_number: str,
                        password: str
                        ) -> Tuple[bool, Optional[dict], str]:
        """
        Authenticate a user with employee number and password

        Args:
            employee_number: Employee number (EMP001, EMP002, etc.)
            password: Plain text password

        Returns:
            Tuple of (success, employee_data_dict, message)
        """
        session = Session()
        try:
            # Find employee by employee_number
            employee = session.query(
                Employee).filter_by(employee_number=employee_number).first()

            if not employee:
                logger.warning(f"Login attempt with invalid employee number:"
                               f"{employee_number}")
                return False, None, "Invalid employee number"

            # Check if account is locked
            if self.is_account_locked(employee):
                remaining_time = employee.locked_until - datetime.now()
                minutes = int(remaining_time.total_seconds() / 60)
                logger.warning(f"Login attempt on locked account: {employee_number}")
                return False, None, f"Account locked. Try again in {minutes} minutes"

            # Verify password
            if not self.verify_password(employee.password_hash, password):
                self.increment_failed_attempts(employee, session)
                attempts_left = self.max_attempts - employee.failed_login_attempts
                logger.warning(f"Failed login attempt for {employee_number}."
                               f"Attempts left: {attempts_left}")

                if attempts_left <= 0:
                    return False, None, "Account locked due to too many failed attempts"
                else:
                    message = f"Invalid password. {attempts_left} attempts remaining"
                    return False, None, message

            # Success - reset failed attempts
            self.reset_failed_attempts(employee, session)
            logger.info(f"Successful login for {employee_number}")

            # Extract employee data while in session to avoid detached instance issues
            employee_data = {
                "id": employee.id,
                "employee_number": employee.employee_number,
                "name": employee.name,
                "email": employee.email,
                "role": employee.role,  # employee.role is already the role name
                "role_id": employee.role_id
            }

            return True, employee_data, "Login successful"

        finally:
            session.close()

    def create_employee_with_password(self,
                                      name: str,
                                      email: str,
                                      role_id: int,
                                      password: str) -> dict:
        """
        Create a new employee with hashed password

        Args:
            name: Employee name
            email: Employee email
            role_id: Role ID (1=sales, 2=support, 3=management, 4=admin)
            password: Plain text password

        Returns:
            Dictionary with employee data (id, employee_number, name, email, role_id)

        Raises:
            Exception: If creation fails
        """
        session = Session()
        try:
            # Generate employee number
            employee_number = Employee.generate_employee_number(session)

            # Hash password
            password_hash = self.hash_password(password)

            # Create employee
            employee = Employee(
                employee_number=employee_number,
                name=name,
                email=email,
                role_id=role_id,
                password_hash=password_hash,
                failed_login_attempts=0,
                locked_until=None,
                last_login=None
            )

            session.add(employee)
            session.commit()

            # Get the data we need before closing the session
            employee_data = {
                'id': employee.id,
                'employee_number': employee.employee_number,
                'name': employee.name,
                'email': employee.email,
                'role_id': employee.role_id
            }

            logger.info(f"Created employee {employee_number} - {name}")
            return employee_data

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create employee: {e}")
            raise
        finally:
            session.close()
