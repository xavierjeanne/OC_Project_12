"""
Employee model for CRM users
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # Authentication fields
    password_hash = Column(String(128))
    employee_number = Column(String(20), unique=True)

    # Relationships
    employee_role = relationship("Role", back_populates="employees")
    customers = relationship("Customer", back_populates="sales_contact")
    contracts = relationship("Contract", back_populates="sales_contact")
    events_support = relationship("Event", back_populates="support_contact")
    
    @property
    def role(self):
        """Compatibility property to get role name"""
        return self.employee_role.name if self.employee_role else None
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', email='{self.email}')>"