"""
Contract Repository using BaseRepository
Repository with specialized contract queries
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from models import Contract
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ContractRepository(BaseRepository[Contract]):
    """
    Repository for Contract entity with specialized queries
    Extends BaseRepository with contract-specific methods
    """

    def __init__(self, db: Session):
        """
        Initialize contract repository

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Contract)

    def find_signed(self) -> List[Contract]:
        """
        Find all signed contracts

        Returns:
            List of signed contracts
        """
        try:
            contracts = self.filter_by(signed=True)
            logger.debug(f"Found {len(contracts)} signed contracts")
            return contracts
        except Exception as e:
            logger.error(f"Error finding signed contracts: {e}")
            raise

    def find_unsigned(self) -> List[Contract]:
        """
        Find all unsigned contracts

        Returns:
            List of unsigned contracts
        """
        try:
            contracts = self.filter_by(signed=False)
            logger.debug(f"Found {len(contracts)} unsigned contracts")
            return contracts
        except Exception as e:
            logger.error(f"Error finding unsigned contracts: {e}")
            raise

    def find_with_balance(self) -> List[Contract]:
        """
        Find all contracts with remaining balance (unpaid)

        Returns:
            List of contracts with balance
        """
        try:
            contracts = (
                self.db.query(Contract).filter(Contract.remaining_amount > 0).all()
            )
            logger.debug(f"Found {len(contracts)} contracts with outstanding balance")
            return contracts
        except Exception as e:
            logger.error(f"Error finding contracts with balance: {e}")
            raise
