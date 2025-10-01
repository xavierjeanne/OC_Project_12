"""
Employee Repository using BaseRepository
Repository with specialized employee queries
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from models.models import Employee
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class EmployeeRepository(BaseRepository[Employee]):
    """
    Repository for Employee entity with specialized queries
    Extends BaseRepository with employee-specific methods
    """

    def __init__(self, db: Session):
        """
        Initialize employee repository

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Employee)

    def find_by_email(self, email: str) -> Optional[Employee]:
        """
        Find an employee by email address

        Args:
            email: Employee email

        Returns:
            Employee if found, None otherwise
        """
        try:
            employee = self.find_one_by(email=email)
            if employee:
                logger.debug(f"Found employee with email: {email}")
            else:
                logger.debug(f"No employee found with email: {email}")
            return employee
        except Exception as e:
            logger.error(f"Error finding employee by email: {e}")
            raise

    def find_by_role(self, role: str) -> List[Employee]:
        """
        Find all employees with a specific role

        Args:
            role: Employee role (sales, support, management)

        Returns:
            List of employees
        """
        try:
            employees = self.filter_by(role=role)
            logger.debug(f"Found {len(employees)} employees with role: {role}")
            return employees
        except Exception as e:
            logger.error(f"Error finding employees by role: {e}")
            raise

    def get_sales_team(self) -> List[Employee]:
        """
        Get all sales employees

        Returns:
            List of sales employees
        """
        try:
            employees = self.find_by_role("sales")
            logger.debug(f"Retrieved {len(employees)} sales employees")
            return employees
        except Exception as e:
            logger.error(f"Error retrieving sales team: {e}")
            raise

    def get_support_team(self) -> List[Employee]:
        """
        Get all support employees

        Returns:
            List of support employees
        """
        try:
            employees = self.find_by_role("support")
            logger.debug(f"Retrieved {len(employees)} support employees")
            return employees
        except Exception as e:
            logger.error(f"Error retrieving support team: {e}")
            raise

    def get_management_team(self) -> List[Employee]:
        """
        Get all management employees

        Returns:
            List of management employees
        """
        try:
            employees = self.find_by_role("management")
            logger.debug(f"Retrieved {len(employees)} management employees")
            return employees
        except Exception as e:
            logger.error(f"Error retrieving management team: {e}")
            raise

    def search_by_name(self, name_pattern: str) -> List[Employee]:
        """
        Search employees by name (partial match)

        Args:
            name_pattern: Name pattern to search

        Returns:
            List of matching employees
        """
        try:
            employees = (
                self.db.query(Employee)
                .filter(Employee.name.ilike(f"%{name_pattern}%"))
                .all()
            )
            logger.debug(f"Found {len(employees)} employees matching: {name_pattern}")
            return employees
        except Exception as e:
            logger.error(f"Error searching employees by name: {e}")
            raise

    def email_exists(self, email: str) -> bool:
        """
        Check if an email already exists

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        try:
            exists = self.find_one_by(email=email) is not None
            logger.debug(f"Email {email} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking email existence: {e}")
            raise

    def get_with_customers(self, employee_id: int) -> Optional[Employee]:
        """
        Get an employee with their assigned customers eagerly loaded

        Args:
            employee_id: Employee ID

        Returns:
            Employee with customers if found, None otherwise
        """
        try:
            employee = (
                self.db.query(Employee)
                .options(joinedload(Employee.customers))
                .filter(Employee.id == employee_id)
                .first()
            )
            if employee:
                logger.debug(
                    f"Retrieved employee {employee_id} with "
                    f"{len(employee.customers)} customers"
                )
            return employee
        except Exception as e:
            logger.error(f"Error retrieving employee with customers: {e}")
            raise

    def get_with_contracts(self, employee_id: int) -> Optional[Employee]:
        """
        Get an employee with their contracts eagerly loaded

        Args:
            employee_id: Employee ID

        Returns:
            Employee with contracts if found, None otherwise
        """
        try:
            employee = (
                self.db.query(Employee)
                .options(joinedload(Employee.contracts))
                .filter(Employee.id == employee_id)
                .first()
            )
            if employee:
                logger.debug(
                    f"Retrieved employee {employee_id} with "
                    f"{len(employee.contracts)} contracts"
                )
            return employee
        except Exception as e:
            logger.error(f"Error retrieving employee with contracts: {e}")
            raise
