"""
Tests for CASCADE behaviors in database relationships
Tests that foreign key constraints work properly with CASCADE DELETE and SET NULL
"""

from datetime import datetime

import pytest
from sqlalchemy.orm import sessionmaker

from db.config import engine
from models import Base, Contract, Customer, Employee, Event, Role
from repositories import (ContractRepository, CustomerRepository,
                          EmployeeRepository, EventRepository)
from services.auth import AuthService


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Setup database once per test session"""
    from db.config import DATABASE_URL

    print("\n=== Test Cascade Setup ===")
    print(f"Connection URL: {DATABASE_URL}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("✅ Tables created successfully")
    yield


@pytest.fixture
def test_session():
    """Create a fresh database session for each test"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Cleanup after each test
    try:
        session.query(Event).delete()
        session.query(Contract).delete()
        session.query(Customer).delete()
        session.query(Employee).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        session.close()


@pytest.fixture
def roles_setup(test_session):
    """Create basic roles for tests"""
    # Create roles if they don't exist
    sales_role = test_session.query(Role).filter_by(name="sales").first()
    if not sales_role:
        sales_role = Role(name="sales", description="Sales team")
        test_session.add(sales_role)

    management_role = test_session.query(Role).filter_by(name="management").first()
    if not management_role:
        management_role = Role(name="management", description="Management team")
        test_session.add(management_role)

    support_role = test_session.query(Role).filter_by(name="support").first()
    if not support_role:
        support_role = Role(name="support", description="Support team")
        test_session.add(support_role)

    test_session.commit()

    return {
        "sales": sales_role,
        "management": management_role,
        "support": support_role
    }


@pytest.fixture
def customer_repo(test_session):
    """Customer repository instance"""
    return CustomerRepository(test_session)


@pytest.fixture
def employee_repo(test_session):
    """Employee repository instance"""
    return EmployeeRepository(test_session)


@pytest.fixture
def auth_service():
    """Create AuthService for employee creation"""
    return AuthService()


def create_test_employee_with_auth(auth_service, name, email, role_id, password="TestPass123!"):
    """Helper to create employee with authentication"""
    return auth_service.create_employee_with_password(
        name=name,
        email=email,
        role_id=role_id,
        password=password
    )


@pytest.fixture
def contract_repo(test_session):
    """Contract repository instance"""
    return ContractRepository(test_session)


@pytest.fixture
def event_repo(test_session):
    """Event repository instance"""
    return EventRepository(test_session)


def test_cascade_delete_customer_deletes_contracts_and_events(
    test_session, customer_repo, employee_repo, contract_repo, event_repo, roles_setup, auth_service
):
    """
    Test that deleting a Customer also deletes its Contracts and Events
    thanks to cascade='all, delete-orphan' on relationships
    """
    print("\n=== Test CASCADE: Deleting Customer → Contract + Event ===")

    # Create employees with authentication
    sales_data = create_test_employee_with_auth(
        auth_service, "Sales Person", "sales@test.com", roles_setup["sales"].id
    )
    support_data = create_test_employee_with_auth(
        auth_service, "Support Person", "support@test.com", roles_setup["support"].id
    )
    
    # Get employee objects from database
    sales = employee_repo.get_by_id(sales_data["id"])
    support = employee_repo.get_by_id(support_data["id"])

    # Create a customer
    customer = customer_repo.create(
        {"full_name": "John Doe", "email": "john@test.com", "phone": "0123456789"}
    )

    # Create a contract linked to the customer
    contract = contract_repo.create(
        {
            "customer_id": customer.id,
            "sales_contact_id": sales.id,
            "total_amount": 5000.0,
            "remaining_amount": 2500.0,
            "date_created": datetime.now(),
            "signed": False,
        }
    )

    # Create an event linked to the contract and the customer
    event_repo.create(
        {
            "contract_id": contract.id,
            "customer_id": customer.id,
            "support_contact_id": support.id,
            "name": "Wedding",
            "date_start": datetime.now(),
            "date_end": datetime.now(),
            "location": "Paris",
            "attendees": 100,
            "notes": "Test event",
        }
    )

    # Check that everything exists
    assert customer_repo.count() == 1
    assert contract_repo.count() == 1
    assert event_repo.count() == 1
    print("✅ Before deletion: 1 Customer, 1 Contract, 1 Event")

    # Delete the customer
    customer_repo.delete(customer.id)
    test_session.commit()

    # Check that the customer, contract AND event have been deleted (CASCADE)
    assert customer_repo.count() == 0
    assert contract_repo.count() == 0
    assert event_repo.count() == 0
    print("✅ After deletion Customer: 0 Customer, 0 Contract, 0 Event (CASCADE OK)")


def test_cascade_delete_contract_deletes_events(
    test_session, customer_repo, employee_repo, contract_repo, event_repo, roles_setup, auth_service
):
    """
    Test that deleting a Contract also deletes its Events
    thanks to cascade='all, delete-orphan' on contract.events relationship
    """
    print("\n=== Test CASCADE: Deleting Contract → Event ===")

    # Create employees with authentication
    sales_data = create_test_employee_with_auth(
        auth_service, "Sales Person", "sales2@test.com", roles_setup["sales"].id
    )
    support_data = create_test_employee_with_auth(
        auth_service, "Support Person", "support2@test.com", roles_setup["support"].id
    )
    
    # Get employee objects from database
    sales = employee_repo.get_by_id(sales_data["id"])
    support = employee_repo.get_by_id(support_data["id"])
    customer = customer_repo.create(
        {"full_name": "Jane Doe", "email": "jane@test.com", "phone": "0123456789"}
    )

    # Create contract
    contract = contract_repo.create(
        {
            "customer_id": customer.id,
            "sales_contact_id": sales.id,
            "total_amount": 3000.0,
            "remaining_amount": 1500.0,
            "date_created": datetime.now(),
            "signed": False,
        }
    )

    # Create event
    event_repo.create(
        {
            "contract_id": contract.id,
            "customer_id": customer.id,
            "support_contact_id": support.id,
            "name": "Conference",
            "date_start": datetime.now(),
            "date_end": datetime.now(),
            "location": "Lyon",
            "attendees": 50,
            "notes": "Test conference",
        }
    )

    # Check
    assert contract_repo.count() == 1
    assert event_repo.count() == 1
    print("✅ Before deletion: 1 Contract, 1 Event")

    # Delete the contract
    contract_repo.delete(contract.id)
    test_session.commit()

    # Check that the event has also been deleted (CASCADE)
    assert contract_repo.count() == 0
    assert event_repo.count() == 0
    print("✅ After deletion Contract: 0 Contract, 0 Event (CASCADE OK)")


def test_delete_employee_sets_null_on_foreign_keys(
    test_session, customer_repo, employee_repo, contract_repo, event_repo, roles_setup, auth_service
):
    """
    Test that deleting an Employee sets to NULL the foreign keys
    in Customer, Contract, Event thanks to ondelete='SET NULL'
    """
    print("\n=== Test CASCADE: Deleting Employee → SET NULL ===")

    # Create employees with authentication
    sales_data = create_test_employee_with_auth(
        auth_service, "Sales Person", "sales3@test.com", roles_setup["sales"].id
    )
    support_data = create_test_employee_with_auth(
        auth_service, "Support Person", "support3@test.com", roles_setup["support"].id
    )
    
    # Get employee objects from database
    sales = employee_repo.get_by_id(sales_data["id"])
    support = employee_repo.get_by_id(support_data["id"])

    # Create customer linked to sales
    customer = customer_repo.create(
        {
            "full_name": "Bob Smith",
            "email": "bob@test.com",
            "phone": "0123456789",
            "sales_contact_id": sales.id,
        }
    )

    # Create contract
    contract = contract_repo.create(
        {
            "customer_id": customer.id,
            "sales_contact_id": sales.id,
            "total_amount": 4000.0,
            "remaining_amount": 2000.0,
            "date_created": datetime.now(),
            "signed": False,
        }
    )

    # Create event
    event = event_repo.create(
        {
            "contract_id": contract.id,
            "customer_id": customer.id,
            "support_contact_id": support.id,
            "name": "Gala",
            "date_start": datetime.now(),
            "date_end": datetime.now(),
            "location": "Nice",
            "attendees": 200,
            "notes": "Test gala",
        }
    )

    # Check foreign keys before deletion
    test_session.refresh(customer)
    test_session.refresh(event)
    print(
        f"Before: Customer.sales_contact_id = {customer.sales_contact_id}, "
        f"Event.support_contact_id = {event.support_contact_id}"
    )

    # Delete the sales employee
    employee_repo.delete(sales.id)
    test_session.commit()

    # Check that entities still exist but with FK set to NULL
    assert customer_repo.count() == 1, "Customer should still exist"
    assert contract_repo.count() == 1, "Contract should still exist"
    assert event_repo.count() == 1, "Event should still exist"

    # Refresh to get updated values
    test_session.refresh(customer)
    test_session.refresh(contract)

    assert customer.sales_contact_id is None, "Customer.sales_contact_id should be NULL"
    assert contract.sales_contact_id is None, "Contract.sales_contact_id should be NULL"
    print(
        "✅ After deletion Sales:"
        "Customer and Contract exist with FK = NULL (SET NULL OK)"
    )

    # Delete the support employee
    employee_repo.delete(support.id)
    test_session.commit()

    # Check event still exists with NULL FK
    assert event_repo.count() == 1, "Event should still exist"
    test_session.refresh(event)
    assert event.support_contact_id is None, "Event.support_contact_id should be NULL"
    print("✅ After deletion Support: Event exists with FK = NULL (SET NULL OK)")


def test_employee_deletion_preserves_related_entities(
    test_session, customer_repo, employee_repo, roles_setup, auth_service
):
    """
    Test that deleting an Employee does not delete related Customers,
    only sets the foreign key to NULL
    """
    print("\n=== Test: Deleting Employee preserves related entities ===")

    # Create employee with authentication
    employee_data = create_test_employee_with_auth(
        auth_service, "Sales Manager", "manager@test.com", roles_setup["sales"].id
    )
    employee = employee_repo.get_by_id(employee_data["id"])
    customer = customer_repo.create(
        {
            "full_name": "Alice Wonder",
            "email": "alice@test.com",
            "phone": "0123456789",
            "sales_contact_id": employee.id,
        }
    )

    assert customer_repo.count() == 1
    assert customer.sales_contact_id == employee.id
    print("✅ Before deletion: 1 Employee, 1 Customer linked")

    # Delete the employee
    employee_repo.delete(employee.id)
    test_session.commit()

    # Check that the Customer still exists
    assert employee_repo.count() == 0, "Employee should be deleted"
    assert customer_repo.count() == 1, "Customer should still exist"

    test_session.refresh(customer)
    assert customer.sales_contact_id is None, "Foreign key should be NULL"
    print(
        "✅ After deletion Employee: Customer"
        " exists with FK = NULL (Correct behavior)"
    )
