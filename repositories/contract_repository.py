"""
Contract Repository using BaseRepository
Repository with specialized contract queries
"""

import logging
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.models import Contract
from repositories.base_repository import BaseRepository

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

    def find_by_customer(self, customer_id: int) -> List[Contract]:
        """
        Find all contracts for a specific customer

        Args:
            customer_id: Customer ID

        Returns:
            List of contracts
        """
        try:
            contracts = self.filter_by(customer_id=customer_id)
            logger.debug(f"Found {len(contracts)} contracts for customer ID: {customer_id}")
            return contracts
        except Exception as e:
            logger.error(f"Error finding contracts by customer: {e}")
            raise

    def find_by_sales_contact(self, sales_contact_id: int) -> List[Contract]:
        """
        Find all contracts assigned to a specific sales contact

        Args:
            sales_contact_id: Sales employee ID

        Returns:
            List of contracts
        """
        try:
            contracts = self.filter_by(sales_contact_id=sales_contact_id)
            logger.debug(
                f"Found {len(contracts)} contracts for sales contact ID: {sales_contact_id}"
            )
            return contracts
        except Exception as e:
            logger.error(f"Error finding contracts by sales contact: {e}")
            raise

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
                self.db.query(Contract)
                .filter(Contract.remaining_amount > 0)
                .all()
            )
            logger.debug(f"Found {len(contracts)} contracts with outstanding balance")
            return contracts
        except Exception as e:
            logger.error(f"Error finding contracts with balance: {e}")
            raise

    def find_fully_paid(self) -> List[Contract]:
        """
        Find all fully paid contracts

        Returns:
            List of fully paid contracts
        """
        try:
            contracts = self.filter_by(remaining_amount=0)
            logger.debug(f"Found {len(contracts)} fully paid contracts")
            return contracts
        except Exception as e:
            logger.error(f"Error finding fully paid contracts: {e}")
            raise

    def find_by_amount_range(
        self, min_amount: Decimal, max_amount: Decimal
    ) -> List[Contract]:
        """
        Find contracts within a specific amount range

        Args:
            min_amount: Minimum total amount
            max_amount: Maximum total amount

        Returns:
            List of contracts
        """
        try:
            contracts = (
                self.db.query(Contract)
                .filter(
                    Contract.total_amount >= min_amount,
                    Contract.total_amount <= max_amount,
                )
                .all()
            )
            logger.debug(
                f"Found {len(contracts)} contracts between {min_amount} and {max_amount}"
            )
            return contracts
        except Exception as e:
            logger.error(f"Error finding contracts by amount range: {e}")
            raise

    def get_total_revenue(self) -> Decimal:
        """
        Calculate total revenue from all contracts

        Returns:
            Total revenue (sum of all contract amounts)
        """
        try:
            total = self.db.query(func.sum(Contract.total_amount)).scalar() or Decimal(0)
            logger.debug(f"Total revenue: {total}")
            return total
        except Exception as e:
            logger.error(f"Error calculating total revenue: {e}")
            raise

    def get_total_outstanding(self) -> Decimal:
        """
        Calculate total outstanding amount across all contracts

        Returns:
            Total outstanding amount
        """
        try:
            total = (
                self.db.query(func.sum(Contract.remaining_amount)).scalar() or Decimal(0)
            )
            logger.debug(f"Total outstanding: {total}")
            return total
        except Exception as e:
            logger.error(f"Error calculating total outstanding: {e}")
            raise

    def get_with_events(self, contract_id: int) -> Optional[Contract]:
        """
        Get a contract with its events eagerly loaded

        Args:
            contract_id: Contract ID

        Returns:
            Contract with events if found, None otherwise
        """
        try:
            contract = (
                self.db.query(Contract)
                .options(joinedload(Contract.events))
                .filter(Contract.id == contract_id)
                .first()
            )
            if contract:
                logger.debug(
                    f"Retrieved contract {contract_id} with "
                    f"{len(contract.events)} events"
                )
            return contract
        except Exception as e:
            logger.error(f"Error retrieving contract with events: {e}")
            raise

    def get_with_customer(self, contract_id: int) -> Optional[Contract]:
        """
        Get a contract with its customer eagerly loaded

        Args:
            contract_id: Contract ID

        Returns:
            Contract with customer if found, None otherwise
        """
        try:
            contract = (
                self.db.query(Contract)
                .options(joinedload(Contract.customer))
                .filter(Contract.id == contract_id)
                .first()
            )
            if contract:
                logger.debug(f"Retrieved contract {contract_id} with customer")
            return contract
        except Exception as e:
            logger.error(f"Error retrieving contract with customer: {e}")
            raise
