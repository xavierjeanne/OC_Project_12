"""
Base Repository Pattern
Generic CRUD operations for all entities
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Type variable for generic model
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic repository with common CRUD operations
    This class provides basic database operations that can be inherited
    by entity-specific repositories.
    Attributes:
    db: SQLAlchemy database session
        db: SQLAlchemy database session
        model: The SQLAlchemy model class
    """

    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize the repository
        Args:
            db: SQLAlchemy database session
            model: The SQLAlchemy model class for this repository
        """
        self.db = db
        self.model = model

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity
        Args:
            data: Dictionary with entity data
        Returns:
            Created entity
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            entity = self.model(**data)
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            logger.info(f"Created {self.model.__name__} with ID {entity.id}")
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Get an entity by ID
        Args:
            entity_id: Entity ID
        Returns:
            Entity if found, None otherwise
        """
        try:
            entity = self.db.query(self.model).filter(
                self.model.id == entity_id).first()
            if entity:
                logger.debug(f"Retrieved {self.model.__name__} with ID {entity_id}")
            else:
                logger.debug(f"{self.model.__name__} with ID {entity_id} not found")
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving {self.model.__name__} by ID: {e}")
            raise

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        Get all entities with optional pagination
        Args:
            limit: Maximum number of results (None for all)
            offset: Number of results to skip
        Returns:
            List of entities
        """
        try:
            query = self.db.query(self.model)
            if offset > 0:
                query = query.offset(offset)

            if limit is not None:
                query = query.limit(limit)

            entities = query.all()
            logger.debug(f"Retrieved {len(entities)} {self.model.__name__} entities")
            return entities
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all {self.model.__name__}: {e}")
            raise

    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity
        Args:
            entity_id: Entity ID
            data: Dictionary with fields to update
        Returns:
            Updated entity if found, None otherwise
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                logger.warning(f"{self.model.__name__} with ID {entity_id}"
                               f"not found for update")
                return None
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            self.db.commit()
            self.db.refresh(entity)
            logger.info(f"Updated {self.model.__name__} with ID {entity_id}")
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise

    def delete(self, entity_id: int) -> bool:
        """
        Delete an entity
        Args:
            entity_id: Entity ID
        Returns:
            True if deleted, False if not found
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                logger.warning(f"{self.model.__name__} with ID {entity_id}"
                               f" not found for deletion")
                return False
            self.db.delete(entity)
            self.db.commit()
            logger.info(f"Deleted {self.model.__name__} with ID {entity_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise

    def filter_by(self, **kwargs) -> List[T]:
        """
        Filter entities by specific criteria
        Args:
            **kwargs: Filter criteria as keyword arguments
        Returns:
            List of matching entities
        Example:
            repository.filter_by(email="user@example.com", role="sales")
        """
        try:
            entities = self.db.query(self.model).filter_by(**kwargs).all()
            logger.debug(
                f"Retrieved {len(entities)} {self.model.__name__} entities "
                f"matching filters: {kwargs}"
            )
            return entities
        except SQLAlchemyError as e:
            logger.error(f"Error filtering {self.model.__name__}: {e}")
            raise

    def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists
        Args:
            entity_id: Entity ID
        Returns:
            True if exists, False otherwise
        """
        try:
            exists = (
                self.db.query(self.model.id)
                .filter(self.model.id == entity_id)
                .first()
                is not None
            )
            logger.debug(f"{self.model.__name__} with ID {entity_id} exists: {exists}")
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__}: {e}")
            raise

    def count(self) -> int:
        """
        Count total number of entities
        Returns:
            Total count
        """
        try:
            count = self.db.query(func.count(self.model.id)).scalar()
            logger.debug(f"Total {self.model.__name__} count: {count}")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise

    def find_one_by(self, **kwargs) -> Optional[T]:
        """
        Find a single entity by specific criteria
        Args:
            **kwargs: Filter criteria as keyword arguments
        Returns:
            Entity if found, None otherwise
        Example:
            repository.find_one_by(email="user@example.com")
        """
        try:
            entity = self.db.query(self.model).filter_by(**kwargs).first()
            if entity:
                logger.debug(f"Found {self.model.__name__} matching {kwargs}")
            else:
                logger.debug(f"No {self.model.__name__} found matching {kwargs}")
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Error finding {self.model.__name__}: {e}")
            raise
