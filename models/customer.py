"""
Customer model for CRM
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    company_name = Column(String)
    date_created = Column(DateTime)
    last_contact = Column(DateTime)
    sales_contact_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))

    # Relationships
    sales_contact = relationship("Employee", back_populates="customers")
    contracts = relationship(
        "Contract", back_populates="customer", cascade="all, delete-orphan"
    )
    events = relationship(
        "Event", back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self):
        message = f"id={self.id}, name='{self.full_name}'," f" email='{self.email}'"
        return f"<Customer({message})>"
