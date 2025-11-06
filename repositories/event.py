"""
Event Repository using BaseRepository
Repository with specialized event queries
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from models import Event
from repositories.base import BaseRepository

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

    def find_without_support(self) -> List[Event]:
        """
        Find all events without an assigned support contact

        Returns:
            List of events
        """
        try:
            events = (
                self.db.query(Event).filter(Event.support_contact_id.is_(None)).all()
            )
            logger.debug(f"Found {len(events)} events without support contact")
            return events
        except Exception as e:
            logger.error(f"Error finding events without support: {e}")
            raise
