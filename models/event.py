"""
Event model for CRM
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"))
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"))
    support_contact_id = Column(
        Integer, ForeignKey("employees.id", ondelete="SET NULL")
    )
    name = Column(String, nullable=False)
    date_start = Column(DateTime)
    date_end = Column(DateTime)
    location = Column(String)
    attendees = Column(Integer)
    notes = Column(Text)

    # Relationships
    contract = relationship("Contract", back_populates="events")
    customer = relationship("Customer", back_populates="events")
    support_contact = relationship("Employee", back_populates="events_support")
    
    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', customer_id={self.customer_id})>"