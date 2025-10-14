"""
Customer Repository using BaseRepository
Repository with specialized customer queries
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

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

    def find_by_email(self, email: str) -> Optional[Customer]:
        """
        Find a customer by email address
        Args:
            email: Customer email
        Returns:
            Customer if found, None otherwise
        """
        try:
            customer = self.find_one_by(email=email)
            if customer:
                logger.debug(f"Found customer with email: {email}")
            else:
                logger.debug(f"No customer found with email: {email}")
            return customer
        except Exception as e:
            logger.error(f"Error finding customer by email: {e}")
            raise

    def find_by_company(self, company_name: str) -> List[Customer]:
        """
        Find all customers from a specific company
        Args:
            company_name: Company name
        Returns:
            List of customers
        """
        try:
            customers = self.filter_by(company_name=company_name)
            logger.debug(f"Found {len(customers)} customers for company:"
                         f"{company_name}")
            return customers
        except Exception as e:
            logger.error(f"Error finding customers by company: {e}")
            raise

    def find_by_sales_contact(self, sales_contact_id: int) -> List[Customer]:
        """
        Find all customers assigned to a specific sales contact
        Args:
            sales_contact_id: Sales employee ID
        Returns:
            List of customers
        """
        try:
            customers = self.filter_by(sales_contact_id=sales_contact_id)
            logger.debug(
                f"Found {len(customers)} customers for sales contact ID"
                f": {sales_contact_id}"
            )
            return customers
        except Exception as e:
            logger.error(f"Error finding customers by sales contact: {e}")
            raise

    def search_by_name(self, name_pattern: str) -> List[Customer]:
        """
        Search customers by name (partial match)
        Args:
            name_pattern: Name pattern to search
        Returns:
            List of matching customers
        """
        try:
            customers = (
                self.db.query(Customer)
                .filter(Customer.full_name.ilike(f"%{name_pattern}%"))
                .all()
            )
            logger.debug(f"Found {len(customers)} customers matching: {name_pattern}")
            return customers
        except Exception as e:
            logger.error(f"Error searching customers by name: {e}")
            raise

    def get_customers_without_sales_contact(self) -> List[Customer]:
        """
        Get all customers without an assigned sales contact
        Returns:
            List of customers
        """
        try:
            customers = (
                self.db.query(Customer)
                .filter(Customer.sales_contact_id.is_(None))
                .all()
            )
            logger.debug(f"Found {len(customers)} customers without sales contact")
            return customers
        except Exception as e:
            logger.error(f"Error finding customers without sales contact: {e}")
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

    def get_with_contracts(self, customer_id: int) -> Optional[Customer]:
        """
        Get a customer with their contracts eagerly loaded
        Args:
            customer_id: Customer ID
        Returns:
            Customer with contracts if found, None otherwise
        """
        try:
            customer = (
                self.db.query(Customer)
                .options(joinedload(Customer.contracts))
                .filter(Customer.id == customer_id)
                .first()
            )
            if customer:
                logger.debug(
                    f"Retrieved customer {customer_id} with "
                    f"{len(customer.contracts)} contracts"
                )
            return customer
        except Exception as e:
            logger.error(f"Error retrieving customer with contracts: {e}")
            raise

    def get_with_events(self, customer_id: int) -> Optional[Customer]:
        """
        Get a customer with their events eagerly loaded
        Args:
            customer_id: Customer ID
        Returns:
            Customer with events if found, None otherwise
        """
        try:
            customer = (
                self.db.query(Customer)
                .options(joinedload(Customer.events))
                .filter(Customer.id == customer_id)
                .first()
            )
            if customer:
                logger.debug(
                    f"Retrieved customer {customer_id} with "
                    f"{len(customer.events)} events"
                )
            return customer
        except Exception as e:
            logger.error(f"Error retrieving customer with events: {e}")
            raise
