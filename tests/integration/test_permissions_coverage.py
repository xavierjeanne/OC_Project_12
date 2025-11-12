"""
Integration tests to improve permissions system coverage
"""

import pytest
from datetime import datetime

from models import Role
from repositories import (
    CustomerRepository,
    EmployeeRepository,
    ContractRepository,
    EventRepository,
)
from services.auth import AuthService
from utils.permissions import (
    Permission,
    PermissionError,
    ROLE_PERMISSIONS,
    has_permission,
    require_permission,
    can_update_own_assigned_customer,
    can_update_own_assigned_contract,
    can_update_own_assigned_event,
    get_role_permissions,
    describe_permissions,
)


@pytest.fixture
def permissions_session(test_db):
    """Session for permissions tests - uses roles created in conftest.py"""
    yield test_db


@pytest.fixture
def permissions_roles(permissions_session):
    """Retrieve roles created in conftest.py - avoids DetachedInstanceError"""
    roles_data = {}
    for role_name in ["sales", "support", "management", "admin"]:
        role = permissions_session.query(Role).filter_by(name=role_name).first()
        if role:
            roles_data[role_name] = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
            }

    # Return a dict-like object that allows accessing both id and full role
    class RoleHelper:

        def __init__(self, session, roles_data):
            self.session = session
            self.roles_data = roles_data

        def __getitem__(self, key):
            if key not in self.roles_data:
                raise KeyError(f"Role '{key}' not found")

            # Return fresh role object from current session
            role_id = self.roles_data[key]["id"]
            return self.session.query(Role).filter(Role.id == role_id).first()

    return RoleHelper(permissions_session, roles_data)


@pytest.fixture
def auth_service_permissions():
    """Authentication service for permissions tests"""
    return AuthService()


@pytest.fixture
def permissions_repos(permissions_session):
    """Repositories for permissions tests"""
    return {
        "customer": CustomerRepository(permissions_session),
        "employee": EmployeeRepository(permissions_session),
        "contract": ContractRepository(permissions_session),
        "event": EventRepository(permissions_session),
    }


class TestPermissions:
    """Tests to improve permissions system coverage"""

    def test_permission_enum_values(self):
        """Test that the Permission enumeration contains the correct values"""
        # Check that all permissions exist
        assert Permission.CREATE_CUSTOMER.value == "create_customer"
        assert Permission.READ_CUSTOMER.value == "read_customer"
        assert Permission.UPDATE_CUSTOMER.value == "update_customer"
        assert Permission.DELETE_CUSTOMER.value == "delete_customer"

        assert Permission.CREATE_EMPLOYEE.value == "create_employee"
        assert Permission.READ_EMPLOYEE.value == "read_employee"
        assert Permission.UPDATE_EMPLOYEE.value == "update_employee"
        assert Permission.DELETE_EMPLOYEE.value == "delete_employee"

    def test_role_permissions_sales(self):
        """Test permissions of the sales role"""
        sales_permissions = ROLE_PERMISSIONS["sales"]

        # Sales can create/read/update customers
        assert Permission.CREATE_CUSTOMER in sales_permissions
        assert Permission.READ_CUSTOMER in sales_permissions
        assert Permission.UPDATE_CUSTOMER in sales_permissions
        # But not delete
        assert Permission.DELETE_CUSTOMER not in sales_permissions

        # Sales can read and update contracts (but not create or sign)
        assert Permission.CREATE_CONTRACT not in sales_permissions
        assert Permission.READ_CONTRACT in sales_permissions
        assert Permission.UPDATE_CONTRACT in sales_permissions
        assert Permission.SIGN_CONTRACT not in sales_permissions

    def test_role_permissions_support(self):
        """Test permissions of the support role"""
        support_permissions = ROLE_PERMISSIONS["support"]

        # Support can only read customers
        assert Permission.READ_CUSTOMER in support_permissions
        assert Permission.CREATE_CUSTOMER not in support_permissions
        assert Permission.UPDATE_CUSTOMER not in support_permissions
        assert Permission.DELETE_CUSTOMER not in support_permissions

        # Support can read and update events
        assert Permission.READ_EVENT in support_permissions
        assert Permission.UPDATE_EVENT in support_permissions
        assert Permission.CREATE_EVENT not in support_permissions

    def test_role_permissions_management(self):
        """Test permissions of the management role"""
        management_permissions = ROLE_PERMISSIONS["management"]

        # Management has all permissions
        all_permissions = list(Permission)
        for permission in all_permissions:
            assert permission in management_permissions

    def test_has_permission_with_valid_employee(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test has_permission with valid employee"""
        # Create a sales employee
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Employee",
            email="sales_perms@test.com",
            role_id=permissions_roles["sales"].id,
            password="TestPassword123!",
        )
        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])

        # Test granted permissions
        assert has_permission(sales_employee, Permission.CREATE_CUSTOMER) is True
        assert has_permission(sales_employee, Permission.READ_CUSTOMER) is True
        assert has_permission(sales_employee, Permission.UPDATE_CONTRACT) is True

        # Test denied permissions (corrected)
        assert has_permission(sales_employee, Permission.CREATE_CONTRACT) is False
        assert has_permission(sales_employee, Permission.DELETE_CUSTOMER) is False
        assert has_permission(sales_employee, Permission.DELETE_EMPLOYEE) is False

    def test_has_permission_with_none_employee(self):
        """Test has_permission with None employee"""
        assert has_permission(None, Permission.CREATE_CUSTOMER) is False
        assert has_permission(None, Permission.READ_CUSTOMER) is False

    def test_has_permission_with_invalid_role(self):
        """Test has_permission with invalid role"""
        # Create a mock employee with an invalid role
        mock_employee = type(
            "MockEmployee",
            (),
            {
                "role": "invalid_role",  # RRole that does not exist in ROLE_PERMISSIONS
                "name": "Test Employee",
            },
        )()

        # An invalid role should return False
        assert has_permission(mock_employee, Permission.CREATE_CUSTOMER) is False

    def test_require_permission_success(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test require_permission with granted permission"""
        # Create a management employee
        mgmt_data = auth_service_permissions.create_employee_with_password(
            name="Management Employee",
            email="mgmt_perms@test.com",
            role_id=permissions_roles["management"].id,
            password="TestPassword123!",
        )
        mgmt_employee = permissions_repos["employee"].get_by_id(mgmt_data["id"])

        # Should not raise an exception
        require_permission(mgmt_employee, Permission.DELETE_CUSTOMER)
        require_permission(mgmt_employee, Permission.CREATE_EMPLOYEE)

    def test_require_permission_failure_none_employee(self):
        """Test require_permission with None employee"""
        with pytest.raises(PermissionError, match="Authentication required"):
            require_permission(None, Permission.CREATE_CUSTOMER)

    def test_require_permission_insufficient_permission(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test require_permission with insufficient permission"""
        # Create a support employee
        support_data = auth_service_permissions.create_employee_with_password(
            name="Support Employee",
            email="support_perms@test.com",
            role_id=permissions_roles["support"].id,
            password="TestPassword123!",
        )
        support_employee = permissions_repos["employee"].get_by_id(support_data["id"])

        # Should raise an exception
        with pytest.raises(PermissionError, match="does not have permission"):
            require_permission(support_employee, Permission.DELETE_CUSTOMER)

    def test_can_update_own_assigned_customer_success(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test can_update_own_assigned_customer with assigned customer"""
        # Create sales employee
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Assigned",
            email="sales_assigned@test.com",
            role_id=permissions_roles["sales"].id,
            password="TestPassword123!",
        )
        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])

        # Create assigned customer for this employee
        customer = permissions_repos["customer"].create(
            {
                "full_name": "Assigned Customer",
                "email": "assigned@test.com",
                "phone": "0123456789",
                "sales_contact_id": sales_employee.id,
            }
        )

        # Sales can update their assigned customer
        assert can_update_own_assigned_customer(sales_employee, customer) is True

    def test_can_update_own_assigned_customer_failure(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test can_update_own_assigned_customer with unassigned customer"""
        # Create two sales employees
        sales1_data = auth_service_permissions.create_employee_with_password(
            name="Sales 1",
            email="sales1_assigned@test.com",
            role_id=permissions_roles["sales"].id,
            password="TestPassword123!",
        )
        sales2_data = auth_service_permissions.create_employee_with_password(
            name="Sales 2",
            email="sales2_assigned@test.com",
            role_id=permissions_roles["sales"].id,
            password="TestPassword123!",
        )

        sales1_employee = permissions_repos["employee"].get_by_id(sales1_data["id"])
        sales2_employee = permissions_repos["employee"].get_by_id(sales2_data["id"])

        # Create assigned customer for sales1
        customer = permissions_repos["customer"].create(
            {
                "full_name": "Other Customer",
                "email": "other@test.com",
                "phone": "0123456789",
                "sales_contact_id": sales1_employee.id,
            }
        )

        # Sales2 cannot update sales1's customer
        assert can_update_own_assigned_customer(sales2_employee, customer) is False

    def test_can_update_own_assigned_customer_management(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test can_update_own_assigned_customer with management role"""
        # Create management employee
        mgmt_data = auth_service_permissions.create_employee_with_password(
            name="Manager",
            email="manager_assigned@test.com",
            role_id=permissions_roles["management"].id,
            password="TestPassword123!",
        )
        manager = permissions_repos["employee"].get_by_id(mgmt_data["id"])

        # Create any customer
        customer = permissions_repos["customer"].create(
            {
                "full_name": "Any Customer",
                "email": "any@test.com",
                "phone": "0123456789",
            }
        )

        # Management can update any customer
        assert can_update_own_assigned_customer(manager, customer) is True

    def test_can_update_with_none_parameters(self):
        """Test can_update methods with None parameters"""
        assert can_update_own_assigned_customer(None, None) is False
        assert can_update_own_assigned_customer(None, "fake_customer") is False

    def test_permission_error_exception(self):
        """Test PermissionError exception"""
        with pytest.raises(PermissionError):
            raise PermissionError("Test error message")

    def test_get_role_permissions(self):
        """Test get_role_permissions function"""
        # Test rôles valides
        sales_perms = get_role_permissions("sales")
        assert isinstance(sales_perms, list)
        assert Permission.CREATE_CUSTOMER in sales_perms

        support_perms = get_role_permissions("support")
        assert isinstance(support_perms, list)
        assert Permission.READ_CUSTOMER in support_perms
        assert Permission.CREATE_CUSTOMER not in support_perms

        # Test rôle invalide
        invalid_perms = get_role_permissions("invalid_role")
        assert invalid_perms == []

    def test_describe_permissions(self):
        """Test describe_permissions function"""
        # Test rôles valides
        sales_desc = describe_permissions("sales")
        assert isinstance(sales_desc, str)
        assert "sales" in sales_desc.lower()

        support_desc = describe_permissions("support")
        assert isinstance(support_desc, str)
        assert "support" in support_desc.lower()

        management_desc = describe_permissions("management")
        assert isinstance(management_desc, str)
        assert "management" in management_desc.lower()

        # Invalid role
        invalid_desc = describe_permissions("invalid_role")
        assert (
            "No permissions" in invalid_desc
            or "Unknown role" in invalid_desc
            or "Invalid role" in invalid_desc
        )

    def test_can_update_own_assigned_contract(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test can_update_own_assigned_contract method"""
        # Create sales employee
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Contract",
            email="sales_contract@test.com",
            role_id=permissions_roles["sales"].id,
            password="TestPassword123!",
        )
        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])

        # Create customer and contract
        customer = permissions_repos["customer"].create(
            {
                "full_name": "Contract Customer",
                "email": "contract_customer@test.com",
                "phone": "0123456789",
            }
        )

        contract = permissions_repos["contract"].create(
            {
                "customer_id": customer.id,
                "sales_contact_id": sales_employee.id,
                "total_amount": 5000.0,
                "remaining_amount": 2500.0,
                "date_created": datetime.now(),
                "signed": False,
            }
        )

        # Sales can update their own contract
        assert can_update_own_assigned_contract(sales_employee, contract) is True

        # Test with None
        assert can_update_own_assigned_contract(None, contract) is False
        assert can_update_own_assigned_contract(sales_employee, None) is False

    def test_can_update_own_assigned_event(
        self, permissions_roles, auth_service_permissions, permissions_repos
    ):
        """Test can_update_own_assigned_event method"""
        # Create employees
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Event Test",
            email="sales_event_test@test.com",
            role_id=permissions_roles["sales"].id,
            password="TestPassword123!",
        )
        support_data = auth_service_permissions.create_employee_with_password(
            name="Support Event Test",
            email="support_event_test@test.com",
            role_id=permissions_roles["support"].id,
            password="TestPassword123!",
        )

        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])
        support_employee = permissions_repos["employee"].get_by_id(support_data["id"])

        # Create customer, contract and event
        customer = permissions_repos["customer"].create(
            {
                "full_name": "Event Customer",
                "email": "event_customer@test.com",
                "phone": "0123456789",
            }
        )

        contract = permissions_repos["contract"].create(
            {
                "customer_id": customer.id,
                "sales_contact_id": sales_employee.id,
                "total_amount": 3000.0,
                "remaining_amount": 1500.0,
                "date_created": datetime.now(),
                "signed": True,
            }
        )

        event = permissions_repos["event"].create(
            {
                "contract_id": contract.id,
                "customer_id": customer.id,
                "support_contact_id": support_employee.id,
                "name": "Test Event Permission",
                "date_start": datetime.now(),
                "date_end": datetime.now(),
                "location": "Test Location",
                "attendees": 50,
                "notes": "Permission test",
            }
        )

        # Support can update their assigned event
        assert can_update_own_assigned_event(support_employee, event) is True

        # Sales cannot update the event assigned to support
        assert can_update_own_assigned_event(sales_employee, event) is False

        # Test with None
        assert can_update_own_assigned_event(None, event) is False
