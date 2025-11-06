"""
Employee model for CRM users
"""

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import relationship
from models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    # Authentication fields
    password_hash = Column(String(255), nullable=False)
    employee_number = Column(String(10), unique=True, nullable=False)

    # Login attempts
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    # Timestamps
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

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

    @staticmethod
    def generate_employee_number(session):
        """Generate next employee number in format EMP001, EMP002, etc."""
        # Find the last employee number
        last_employee = (
            session.query(Employee).order_by(Employee.employee_number.desc()).first()
        )

        if not last_employee:
            return "EMP001"

        # Extract numeric part and increment
        last_num = int(last_employee.employee_number[3:])  # Remove "EMP"
        next_num = last_num + 1
        return f"EMP{next_num:03d}"  # Format with 3 digits : EMP001, EMP002...
