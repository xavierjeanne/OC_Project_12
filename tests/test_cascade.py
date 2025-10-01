import os
import sys
import pytest
from datetime import datetime
from config import engine
from crud.contract_crud import create_contract
from crud.customer_crud import Session, create_customer, delete_customer
from crud.employee_crud import create_employee, delete_employee
from crud.event_crud import create_event
from models import Base, Contract, Customer, Employee, Event
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


# Setup DB once per test session
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    from config import DATABASE_URL

    print("=== Test Setup ===")
    print(f"Connection URL: {DATABASE_URL}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Tables created successfully")
    yield


# cleanup data between tests
@pytest.fixture(autouse=True)
def cleanup_data():
    yield
    session = Session()
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


def test_cascade_delete_customer_deletes_contracts_and_events():
    """
    Test that deleting a Customer also deletes its Contracts and Events
    thanks to cascade='all, delete-orphan'
    """
    print("\n=== Test CASCADE: Deleting Customer → Contract + Event ===")

    # Create an employee (sales + support)
    create_employee("Sales Person", "sales@test.com", "sales", current_user=None)
    create_employee("Support Person", "support@test.com", "support", current_user=None)

    # Create a customer
    create_customer("John Doe", "john@test.com", current_user=None)

    session = Session()
    customer = session.query(Customer).first()
    sales = session.query(Employee).filter_by(role="sales").first()
    support = session.query(Employee).filter_by(role="support").first()

    # Create a contract linked to the customer
    create_contract(
        customer.id, sales.id, 5000.0, 2500.0, datetime.now(), current_user=None
    )
    contract = session.query(Contract).first()

    # Create an event linked to the contract and the customer
    create_event(
        contract.id,
        customer.id,
        support.id,
        "Wedding",
        datetime.now(),
        datetime.now(),
        "Paris",
        100,
        current_user=None,
    )

    # Check that everything exists
    assert session.query(Customer).count() == 1
    assert session.query(Contract).count() == 1
    assert session.query(Event).count() == 1
    print("✅ Before deletion: 1 Customer, 1 Contract, 1 Event")

    # Delete the customer
    customer_id = customer.id
    session.close()
    delete_customer(customer_id, current_user=None)

    # Check that the customer, contract AND event have been deleted
    session = Session()
    assert session.query(Customer).count() == 0
    assert session.query(Contract).count() == 0
    assert session.query(Event).count() == 0
    print("✅ After deletion Customer: 0 Customer, 0 Contract, 0 Event (CASCADE OK)")
    session.close()


def test_cascade_delete_contract_deletes_events():
    """
    Test that deleting a Contract also deletes its Events
    """
    print("\n=== Test CASCADE: Deleting Contract → Event ===")

    # Create entities
    create_employee("Sales Person", "sales2@test.com", "sales", current_user=None)
    create_employee("Support Person", "support2@test.com", "support", current_user=None)
    create_customer("Jane Doe", "jane@test.com", current_user=None)

    session = Session()
    customer = session.query(Customer).first()
    sales = session.query(Employee).filter_by(role="sales").first()
    support = session.query(Employee).filter_by(role="support").first()

    # Create contract and event
    create_contract(
        customer.id, sales.id, 3000.0, 1500.0, datetime.now(), current_user=None
    )
    contract = session.query(Contract).first()
    create_event(
        contract.id,
        customer.id,
        support.id,
        "Conference",
        datetime.now(),
        datetime.now(),
        "Lyon",
        50,
        current_user=None,
    )

    # Check
    assert session.query(Contract).count() == 1
    assert session.query(Event).count() == 1
    print("✅ Before deletion: 1 Contract, 1 Event")

    # Delete the contract
    contract_id = contract.id
    session.close()
    from crud.contract_crud import delete_contract

    delete_contract(contract_id, current_user=None)

    # Check that the event has also been deleted
    session = Session()
    assert session.query(Contract).count() == 0
    assert session.query(Event).count() == 0
    print("✅ After deletion Contract: 0 Contract, 0 Event (CASCADE OK)")
    session.close()


def test_delete_employee_sets_null_on_foreign_keys():
    """
    Test that deleting an Employee sets to NULL the foreign
    keys in Customer, Contract, Event
    thanks to ondelete='SET NULL'
    """
    print("\n=== Test CASCADE: Deleting Employee → SET NULL ===")

    # Create employee, customer, contract, event
    create_employee("Sales Person", "sales3@test.com", "sales", current_user=None)
    create_employee("Support Person", "support3@test.com", "support", current_user=None)
    create_customer("Bob Smith", "bob@test.com", current_user=None)

    session = Session()
    customer = session.query(Customer).first()
    sales = session.query(Employee).filter_by(role="sales").first()
    support = session.query(Employee).filter_by(role="support").first()

    # Link the customer to the sales
    customer.sales_contact_id = sales.id
    session.commit()

    create_contract(
        customer.id, sales.id, 4000.0, 2000.0, datetime.now(), current_user=None
    )
    contract = session.query(Contract).first()
    create_event(
        contract.id,
        customer.id,
        support.id,
        "Gala",
        datetime.now(),
        datetime.now(),
        "Nice",
        200,
        current_user=None,
    )

    # Check foreign keys before deletion
    session.refresh(customer)
    event = session.query(Event).first()
    print(
        f"Customer.sales_contact_id = {customer.sales_contact_id}, "
        f"Event.support_contact_id = {event.support_contact_id}"
    )

    # Delete the sales employee
    sales_id = sales.id
    support_id = support.id
    session.close()
    delete_employee(sales_id, current_user=None)

    # Check that the entities still exist but with FK set to NULL
    session = Session()
    assert session.query(Customer).count() == 1, "Customer should still exist"
    assert session.query(Contract).count() == 1, "Contract should still exist"
    assert session.query(Event).count() == 1, "Event should still exist"

    customer = session.query(Customer).first()
    contract = session.query(Contract).first()
    assert customer.sales_contact_id is None, "Customer.sales_contact_id should be NULL"
    assert contract.sales_contact_id is None, "Contract.sales_contact_id should be NULL"
    print(
        "✅ After deletion Sales Employee:"
        " Customer and Contract exist with FK = NULL (SET NULL OK)"
    )

    # Delete the support employee
    session.close()
    delete_employee(support_id, current_user=None)

    session = Session()
    assert session.query(Event).count() == 1, "Event should still exist"
    event = session.query(Event).first()
    assert event.support_contact_id is None, "Event.support_contact_id should be NULL"
    print(
        "✅ After deletion Support Employee: Event exists with FK = NULL (SET NULL OK)"
    )
    session.close()


def test_employee_deletion_preserves_related_entities():
    """
    Test that deleting an Employee does not delete related Customers
    """
    print("\n=== Test: Deleting Employee preserves related entities ===")

    # Create employee and related customer
    create_employee("Sales Manager", "manager@test.com", "sales", current_user=None)
    create_customer("Alice Wonder", "alice@test.com", current_user=None)

    session = Session()
    employee = session.query(Employee).first()
    customer = session.query(Customer).first()

    # Link the customer to the employee
    customer.sales_contact_id = employee.id
    session.commit()

    assert session.query(Customer).count() == 1
    print("✅ Before deletion: 1 Employee, 1 Customer linked")

    # Delete the employee
    employee_id = employee.id
    session.close()
    delete_employee(employee_id, current_user=None)

    # Check that the Customer still exists
    session = Session()
    assert session.query(Employee).count() == 0, "Employee should be deleted"
    assert session.query(Customer).count() == 1, "Customer should still exist"
    customer = session.query(Customer).first()
    assert customer.sales_contact_id is None, "Foreign key should be NULL"
    print(
        "✅ After deletion Employee: Customer exists with FK = NULL (Correct behavior)"
    )
    session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
