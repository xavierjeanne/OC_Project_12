"""
Role model for user authentication and authorization
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)  # sales, management, support
    description = Column(String)

    # Relationships
    employees = relationship("Employee", back_populates="employee_role")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
