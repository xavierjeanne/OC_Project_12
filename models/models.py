from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from db.config import engine

Base = declarative_base()


# --- MODELS ---


# --- Create tables in the database ---
def init_db():
    Base.metadata.create_all(engine)
    print("All tables created successfully.")


# --- Simple CRUD example ---
Session = sessionmaker(bind=engine)


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)  # sales, management, support

    # Relationships
    customers = relationship("Customer", back_populates="sales_contact")
    contracts = relationship("Contract", back_populates="sales_contact")
    events_support = relationship("Event", back_populates="support_contact")


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

    sales_contact = relationship("Employee", back_populates="customers")
    contracts = relationship(
        "Contract", back_populates="customer", cascade="all, delete-orphan"
    )
    events = relationship(
        "Event", back_populates="customer", cascade="all, delete-orphan"
    )


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"))
    sales_contact_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    total_amount = Column(Float)
    remaining_amount = Column(Float)
    date_created = Column(DateTime)
    signed = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="contracts")
    sales_contact = relationship("Employee", back_populates="contracts")
    events = relationship(
        "Event", back_populates="contract", cascade="all, delete-orphan"
    )


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

    contract = relationship("Contract", back_populates="events")
    customer = relationship("Customer", back_populates="events")
    support_contact = relationship("Employee", back_populates="events_support")


if __name__ == "__main__":
    # Create tables
    init_db()
