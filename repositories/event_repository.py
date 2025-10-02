"""
Event Repository using BaseRepository
Repository with specialized event queries
"""

import logging
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.models import Event
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class EventRepository(BaseRepository[Event]):
    """
    Repository for Event entity with specialized queries
    Extends BaseRepository with event-specific methods
    """

    def __init__(self, db: Session):
        """
        Initialize event repository

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Event)

    def find_by_contract(self, contract_id: int) -> List[Event]:
        """
        Find all events for a specific contract

        Args:
            contract_id: Contract ID

        Returns:
            List of events
        """
        try:
            events = self.filter_by(contract_id=contract_id)
            logger.debug(f"Found {len(events)} events for contract ID: {contract_id}")
            return events
        except Exception as e:
            logger.error(f"Error finding events by contract: {e}")
            raise

    def find_by_customer(self, customer_id: int) -> List[Event]:
        """
        Find all events for a specific customer

        Args:
            customer_id: Customer ID

        Returns:
            List of events
        """
        try:
            events = self.filter_by(customer_id=customer_id)
            logger.debug(f"Found {len(events)} events for customer ID: {customer_id}")
            return events
        except Exception as e:
            logger.error(f"Error finding events by customer: {e}")
            raise

    def find_by_support_contact(self, support_contact_id: int) -> List[Event]:
        """
        Find all events assigned to a specific support contact

        Args:
            support_contact_id: Support employee ID

        Returns:
            List of events
        """
        try:
            events = self.filter_by(support_contact_id=support_contact_id)
            logger.debug(
                f"Found {len(events)} events for support contact ID:"
                f"{support_contact_id}"
            )
            return events
        except Exception as e:
            logger.error(f"Error finding events by support contact: {e}")
            raise

    def find_by_location(self, location: str) -> List[Event]:
        """
        Find all events at a specific location

        Args:
            location: Event location

        Returns:
            List of events
        """
        try:
            events = self.filter_by(location=location)
            logger.debug(f"Found {len(events)} events at location: {location}")
            return events
        except Exception as e:
            logger.error(f"Error finding events by location: {e}")
            raise

    def find_upcoming(self, days: int = 30) -> List[Event]:
        """
        Find all upcoming events within the specified number of days

        Args:
            days: Number of days to look ahead (default: 30)

        Returns:
            List of upcoming events
        """
        try:
            today = date.today()
            cutoff_date = today + timedelta(days=days)

            events = (
                self.db.query(Event)
                .filter(
                    Event.event_date_start >= today,
                    Event.event_date_start <= cutoff_date,
                )
                .order_by(Event.event_date_start)
                .all()
            )
            logger.debug(f"Found {len(events)} upcoming events in next {days} days")
            return events
        except Exception as e:
            logger.error(f"Error finding upcoming events: {e}")
            raise

    def find_past(self) -> List[Event]:
        """
        Find all past events

        Returns:
            List of past events
        """
        try:
            today = date.today()
            events = (
                self.db.query(Event)
                .filter(Event.event_date_end < today)
                .order_by(Event.event_date_end.desc())
                .all()
            )
            logger.debug(f"Found {len(events)} past events")
            return events
        except Exception as e:
            logger.error(f"Error finding past events: {e}")
            raise

    def find_in_date_range(
        self, start_date: date, end_date: date
    ) -> List[Event]:
        """
        Find all events within a specific date range

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            List of events
        """
        try:
            events = (
                self.db.query(Event)
                .filter(
                    Event.event_date_start >= start_date,
                    Event.event_date_start <= end_date,
                )
                .order_by(Event.event_date_start)
                .all()
            )
            logger.debug(
                f"Found {len(events)} events between {start_date} and {end_date}"
            )
            return events
        except Exception as e:
            logger.error(f"Error finding events in date range: {e}")
            raise

    def find_by_name_pattern(self, name_pattern: str) -> List[Event]:
        """
        Search events by name (partial match)

        Args:
            name_pattern: Name pattern to search

        Returns:
            List of matching events
        """
        try:
            events = (
                self.db.query(Event)
                .filter(Event.event_name.ilike(f"%{name_pattern}%"))
                .all()
            )
            logger.debug(f"Found {len(events)} events matching: {name_pattern}")
            return events
        except Exception as e:
            logger.error(f"Error searching events by name: {e}")
            raise

    def find_large_events(self, min_attendees: int) -> List[Event]:
        """
        Find events with a minimum number of attendees

        Args:
            min_attendees: Minimum number of attendees

        Returns:
            List of events
        """
        try:
            events = (
                self.db.query(Event)
                .filter(Event.attendees >= min_attendees)
                .order_by(Event.attendees.desc())
                .all()
            )
            logger.debug(
                f"Found {len(events)} events with at least {min_attendees} attendees"
            )
            return events
        except Exception as e:
            logger.error(f"Error finding large events: {e}")
            raise

    def find_without_support(self) -> List[Event]:
        """
        Find all events without an assigned support contact

        Returns:
            List of events
        """
        try:
            events = (
                self.db.query(Event)
                .filter(Event.support_contact_id.is_(None))
                .all()
            )
            logger.debug(f"Found {len(events)} events without support contact")
            return events
        except Exception as e:
            logger.error(f"Error finding events without support: {e}")
            raise

    def get_total_attendees(self) -> int:
        """
        Calculate total number of attendees across all events

        Returns:
            Total attendees count
        """
        try:
            total = self.db.query(func.sum(Event.attendees)).scalar() or 0
            logger.debug(f"Total attendees across all events: {total}")
            return total
        except Exception as e:
            logger.error(f"Error calculating total attendees: {e}")
            raise

    def get_with_contract(self, event_id: int) -> Optional[Event]:
        """
        Get an event with its contract eagerly loaded

        Args:
            event_id: Event ID

        Returns:
            Event with contract if found, None otherwise
        """
        try:
            event = (
                self.db.query(Event)
                .options(joinedload(Event.contract))
                .filter(Event.id == event_id)
                .first()
            )
            if event:
                logger.debug(f"Retrieved event {event_id} with contract")
            return event
        except Exception as e:
            logger.error(f"Error retrieving event with contract: {e}")
            raise

    def get_with_customer(self, event_id: int) -> Optional[Event]:
        """
        Get an event with its customer eagerly loaded

        Args:
            event_id: Event ID

        Returns:
            Event with customer if found, None otherwise
        """
        try:
            event = (
                self.db.query(Event)
                .options(joinedload(Event.customer))
                .filter(Event.id == event_id)
                .first()
            )
            if event:
                logger.debug(f"Retrieved event {event_id} with customer")
            return event
        except Exception as e:
            logger.error(f"Error retrieving event with customer: {e}")
            raise
