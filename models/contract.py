"""
Contract model for CRM
"""

from sqlalchemy import Column, Integer, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"))
    sales_contact_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    total_amount = Column(Float)
    remaining_amount = Column(Float)
    date_created = Column(DateTime)
    signed = Column(Boolean, default=False)

    # Relationships
    customer = relationship("Customer", back_populates="contracts")
    sales_contact = relationship("Employee", back_populates="contracts")
    events = relationship(
        "Event", back_populates="contract", cascade="all, delete-orphan"
    )

    def __repr__(self):
        message = (
            f"id={self.id}, customer_id={self.customer_id},"
            f" amount={self.total_amount}"
        )
        return f"<Contract({message})>"
