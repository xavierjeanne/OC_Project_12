"""
Employee Repository using BaseRepository
Repository with specialized employee queries
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from models import Employee
from repositories.base import BaseRepository

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
