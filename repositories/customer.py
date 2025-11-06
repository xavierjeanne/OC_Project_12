"""
Customer Repository using BaseRepository
Repository with specialized customer queries
"""

import logging

from sqlalchemy.orm import Session

from models import Customer
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CustomerRepository(BaseRepository[Customer]):
    """
    Repository for Customer entity with specialized queries
    Extends BaseRepository with customer-specific methods
    """

    def __init__(self, db: Session):
        """
        Initialize customer repository
        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Customer)
