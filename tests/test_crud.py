import os
import sys
import pytest
from datetime import datetime
from config import engine
from crud.contract_crud import (create_contract, delete_contract,
                                update_contract)
from crud.customer_crud import (Session, create_customer, delete_customer,
                                update_customer)
from crud.employee_crud import (create_employee, delete_employee,
                                update_employee)
from crud.event_crud import create_event, delete_event, update_event
from models import Base, Contract, Customer, Employee, Event
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


# Setup DB once per test session
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    from config import DATABASE_URL

    print("=== Test Setup ===")
    print(f"URL de connexion SQLAlchemy utilisée : {DATABASE_URL}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Tables created successfully")
    yield

    # Base.metadata.drop_all(engine)


# cleanup data between tests
@pytest.fixture(autouse=True)
def cleanup_data():
    yield
    # Clean up in reverse order of dependencies
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


# --- Customer CRUD ---
def test_create_and_get_customer():
    print("test_create_and_get_customer")
    create_customer("Alice", "alice@example.com", current_user=None)
    session = Session()
    try:
        customers = session.query(Customer).all()
        print(f"Nb customers: {len(customers)}")
        assert len(customers) == 1
        assert customers[0].full_name == "Alice"
        assert customers[0].email == "alice@example.com"
    finally:
        session.close()
    print("Fin test_create_and_get_customer")


def test_update_customer():
    print("test_update_customer")
    create_customer("Bob", "bob@example.com", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        customer_id = customer.id
        session.close()
        update_customer(customer_id, current_user=None, full_name="Bobby")
        session = Session()
        updated = session.get(Customer, customer_id)
        print(f"Customer updated name: {updated.full_name}")
        assert updated.full_name == "Bobby"
    finally:
        session.close()
    print("Fin test_update_customer")


def test_delete_customer():
    print("Début test_delete_customer")
    create_customer("Charlie", "charlie@example.com", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        customer_id = customer.id
        session.close()
        delete_customer(customer_id, current_user=None)
        session = Session()
        result = session.get(Customer, customer_id)
        print(f"Customer after delete: {result}")
        assert result is None
    finally:
        session.close()
    print("Fin test_delete_customer")


# --- Employee CRUD ---
def test_create_and_get_employee():
    print("Début test_create_and_get_employee")
    create_employee("Eve", "eve@example.com", "sales", current_user=None)
    session = Session()
    try:
        employees = session.query(Employee).all()
        print(f"Nb employees: {len(employees)}")
        assert len(employees) == 1
        assert employees[0].name == "Eve"
        assert employees[0].role == "sales"
    finally:
        session.close()
    print("Fin test_create_and_get_employee")


def test_update_employee():
    print("Début test_update_employee")
    create_employee("Frank", "frank@example.com", "support", current_user=None)
    session = Session()
    try:
        employee = session.query(Employee).first()
        employee_id = employee.id
        session.close()
        update_employee(employee_id, current_user=None, role="management")
        session = Session()
        updated = session.get(Employee, employee_id)
        print(f"Employee updated role: {updated.role}")
        assert updated.role == "management"
    finally:
        session.close()
    print("Fin test_update_employee")


def test_delete_employee():
    print("Début test_delete_employee")
    create_employee("Grace", "grace@example.com", "support", current_user=None)
    session = Session()
    try:
        employee = session.query(Employee).first()
        employee_id = employee.id
        session.close()
        delete_employee(employee_id, current_user=None)
        session = Session()
        result = session.get(Employee, employee_id)
        print(f"Employee after delete: {result}")
        assert result is None
    finally:
        session.close()
    print("Fin test_delete_employee")


# --- Contract CRUD ---
def test_create_and_get_contract():
    create_customer("Henry", "henry@example.com", current_user=None)
    create_employee("Isaac", "isaac@example.com", "sales", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        employee = session.query(Employee).first()
        create_contract(
            customer.id, employee.id, 1000.0, 500.0, datetime.now(), current_user=None
        )
        contracts = session.query(Contract).all()
        assert len(contracts) == 1
        assert contracts[0].total_amount == 1000.0
    finally:
        session.close()


def test_update_contract():
    create_customer("Jack", "jack@example.com", current_user=None)
    create_employee("Kate", "kate@example.com", "sales", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        employee = session.query(Employee).first()
        create_contract(
            customer.id, employee.id, 2000.0, 1000.0, datetime.now(), current_user=None
        )
        contract = session.query(Contract).first()
        contract_id = contract.id
        session.close()
        update_contract(contract_id, current_user=None, signed=True)
        session = Session()
        updated = session.get(Contract, contract_id)
        assert updated.signed is True
    finally:
        session.close()


def test_delete_contract():
    create_customer("Leo", "leo@example.com", current_user=None)
    create_employee("Mona", "mona@example.com", "sales", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        employee = session.query(Employee).first()
        create_contract(
            customer.id, employee.id, 3000.0, 1500.0, datetime.now(), current_user=None
        )
        contract = session.query(Contract).first()
        contract_id = contract.id
        session.close()
        delete_contract(contract_id, current_user=None)
        session = Session()
        assert session.get(Contract, contract_id) is None
    finally:
        session.close()


# --- Event CRUD ---
def test_create_and_get_event():
    create_customer("Nina", "nina@example.com", current_user=None)
    create_employee("Oscar", "oscar@example.com", "support", current_user=None)
    create_employee("Paul", "paul@example.com", "sales", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        support = session.query(Employee).filter_by(role="support").first()
        sales = session.query(Employee).filter_by(role="sales").first()
        create_contract(
            customer.id, sales.id, 4000.0, 2000.0, datetime.now(), current_user=None
        )
        contract = session.query(Contract).first()
        create_event(
            contract.id,
            customer.id,
            support.id,
            "Epic Party",
            datetime.now(),
            datetime.now(),
            "Paris",
            100,
            current_user=None,
        )
        events = session.query(Event).all()
        assert len(events) == 1
        assert events[0].name == "Epic Party"
    finally:
        session.close()


def test_update_event():
    create_customer("Quinn", "quinn@example.com", current_user=None)
    create_employee("Rita", "rita@example.com", "support", current_user=None)
    create_employee("Sam", "sam@example.com", "sales", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        support = session.query(Employee).filter_by(role="support").first()
        sales = session.query(Employee).filter_by(role="sales").first()
        create_contract(
            customer.id, sales.id, 5000.0, 2500.0, datetime.now(), current_user=None
        )
        contract = session.query(Contract).first()
        create_event(
            contract.id,
            customer.id,
            support.id,
            "General Assembly",
            datetime.now(),
            datetime.now(),
            "Lyon",
            200,
            current_user=None,
        )
        event = session.query(Event).first()
        event_id = event.id
        session.close()
        update_event(event_id, current_user=None, attendees=250)
        session = Session()
        updated = session.get(Event, event_id)
        assert updated.attendees == 250
    finally:
        session.close()


def test_delete_event():
    print("Début test_delete_event")
    create_customer("Tom", "tom@example.com", current_user=None)
    create_employee("Uma", "uma@example.com", "support", current_user=None)
    create_employee("Vera", "vera@example.com", "sales", current_user=None)
    session = Session()
    try:
        customer = session.query(Customer).first()
        support = session.query(Employee).filter_by(role="support").first()
        sales = session.query(Employee).filter_by(role="sales").first()
        create_contract(
            customer.id, sales.id, 6000.0, 3000.0, datetime.now(), current_user=None
        )
        contract = session.query(Contract).first()
        create_event(
            contract.id,
            customer.id,
            support.id,
            "Wedding",
            datetime.now(),
            datetime.now(),
            "Nice",
            150,
            current_user=None,
        )
        event = session.query(Event).first()
        event_id = event.id
        session.close()
        delete_event(event_id, current_user=None)
        session = Session()
        result = session.get(Event, event_id)
        print(f"Event after delete: {result}")
        assert result is None
    finally:
        session.close()
    print("Fin test_delete_event")

    print("DEBUG: Fin de tous les tests pytest")
