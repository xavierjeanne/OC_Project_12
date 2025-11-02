"""
Tests pour améliorer la couverture des permissions de sécurité
Tests avec PostgreSQL pour cohérence production
"""

import pytest
from datetime import datetime

from models import Customer, Employee, Role, Contract, Event
from repositories import (CustomerRepository,
                          EmployeeRepository,
                          ContractRepository,
                          EventRepository)
from services.auth import AuthService
from utils.permissions import (
    Permission, PermissionError, ROLE_PERMISSIONS,
    has_permission, require_permission,
    can_update_own_assigned_customer, can_update_own_assigned_contract,
    can_update_own_assigned_event, get_role_permissions, describe_permissions
)


@pytest.fixture
def permissions_session(test_db):
    """Session pour tests de permissions - utilise les rôles créés dans conftest.py"""
    yield test_db


@pytest.fixture
def permissions_roles(permissions_session):
    """Récupérer les rôles créés dans conftest.py - évite DetachedInstanceError"""
    roles_data = {}
    for role_name in ["sales", "support", "management", "admin"]:
        role = permissions_session.query(Role).filter_by(name=role_name).first()
        if role:
            roles_data[role_name] = {
                'id': role.id,
                'name': role.name,
                'description': role.description
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
            role_id = self.roles_data[key]['id']
            return self.session.query(Role).filter(Role.id == role_id).first()
    
    return RoleHelper(permissions_session, roles_data)


@pytest.fixture
def auth_service_permissions():
    """Service d'authentification pour tests de permissions"""
    return AuthService()


@pytest.fixture
def permissions_repos(permissions_session):
    """Repositories pour tests de permissions"""
    return {
        "customer": CustomerRepository(permissions_session),
        "employee": EmployeeRepository(permissions_session),
        "contract": ContractRepository(permissions_session),
        "event": EventRepository(permissions_session)
    }


class TestPermissions:
    """Tests pour améliorer la couverture du système de permissions"""

    def test_permission_enum_values(self):
        """Test que l'énumération Permission contient les bonnes valeurs"""
        # Vérifier que toutes les permissions existent
        assert Permission.CREATE_CUSTOMER.value == "create_customer"
        assert Permission.READ_CUSTOMER.value == "read_customer"
        assert Permission.UPDATE_CUSTOMER.value == "update_customer"
        assert Permission.DELETE_CUSTOMER.value == "delete_customer"

        assert Permission.CREATE_EMPLOYEE.value == "create_employee"
        assert Permission.READ_EMPLOYEE.value == "read_employee"
        assert Permission.UPDATE_EMPLOYEE.value == "update_employee"
        assert Permission.DELETE_EMPLOYEE.value == "delete_employee"

    def test_role_permissions_sales(self):
        """Test permissions du rôle sales"""
        sales_permissions = ROLE_PERMISSIONS["sales"]

        # Sales peut créer/lire/modifier des clients
        assert Permission.CREATE_CUSTOMER in sales_permissions
        assert Permission.READ_CUSTOMER in sales_permissions
        assert Permission.UPDATE_CUSTOMER in sales_permissions
        # Mais pas supprimer
        assert Permission.DELETE_CUSTOMER not in sales_permissions

        # Sales peut tout faire avec les contrats
        assert Permission.CREATE_CONTRACT in sales_permissions
        assert Permission.READ_CONTRACT in sales_permissions
        assert Permission.UPDATE_CONTRACT in sales_permissions
        assert Permission.SIGN_CONTRACT in sales_permissions

    def test_role_permissions_support(self):
        """Test permissions du rôle support"""
        support_permissions = ROLE_PERMISSIONS["support"]

        # Support peut seulement lire les clients
        assert Permission.READ_CUSTOMER in support_permissions
        assert Permission.CREATE_CUSTOMER not in support_permissions
        assert Permission.UPDATE_CUSTOMER not in support_permissions
        assert Permission.DELETE_CUSTOMER not in support_permissions

        # Support peut lire et modifier les événements
        assert Permission.READ_EVENT in support_permissions
        assert Permission.UPDATE_EVENT in support_permissions
        assert Permission.CREATE_EVENT not in support_permissions

    def test_role_permissions_management(self):
        """Test permissions du rôle management"""
        management_permissions = ROLE_PERMISSIONS["management"]

        # Management a toutes les permissions
        all_permissions = list(Permission)
        for permission in all_permissions:
            assert permission in management_permissions

    def test_has_permission_with_valid_employee(self,
                                                permissions_roles,
                                                auth_service_permissions,
                                                permissions_repos):
        """Test has_permission avec employé valide"""
        # Créer un employé sales
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Employee", email="sales_perms@test.com",
            role_id=permissions_roles["sales"].id, password="TestPassword123!"
        )
        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])

        # Test permissions accordées
        assert has_permission(sales_employee, Permission.CREATE_CUSTOMER) is True
        assert has_permission(sales_employee, Permission.READ_CUSTOMER) is True
        assert has_permission(sales_employee, Permission.CREATE_CONTRACT) is True

        # Test permissions refusées
        assert has_permission(sales_employee, Permission.DELETE_CUSTOMER) is False
        assert has_permission(sales_employee, Permission.DELETE_EMPLOYEE) is False

    def test_has_permission_with_none_employee(self):
        """Test has_permission avec employé None"""
        assert has_permission(None, Permission.CREATE_CUSTOMER) is False
        assert has_permission(None, Permission.READ_CUSTOMER) is False

    def test_has_permission_with_invalid_role(self):
        """Test has_permission avec rôle invalide"""
        # Créer un mock employee avec un rôle invalide
        mock_employee = type('MockEmployee', (), {
            'role': 'invalid_role',  # Rôle qui n'existe pas dans ROLE_PERMISSIONS
            'name': 'Test Employee'
        })()

        # Un rôle invalide devrait retourner False
        assert has_permission(mock_employee, Permission.CREATE_CUSTOMER) is False

    def test_require_permission_success(self,
                                        permissions_roles,
                                        auth_service_permissions,
                                        permissions_repos):
        """Test require_permission avec permission accordée"""
        # Créer un employé management
        mgmt_data = auth_service_permissions.create_employee_with_password(
            name="Management Employee", email="mgmt_perms@test.com",
            role_id=permissions_roles["management"].id, password="TestPassword123!"
        )
        mgmt_employee = permissions_repos["employee"].get_by_id(mgmt_data["id"])

        # Ne devrait pas lever d'exception
        require_permission(mgmt_employee, Permission.DELETE_CUSTOMER)
        require_permission(mgmt_employee, Permission.CREATE_EMPLOYEE)

    def test_require_permission_failure_none_employee(self):
        """Test require_permission avec employé None"""
        with pytest.raises(PermissionError, match="Authentication required"):
            require_permission(None, Permission.CREATE_CUSTOMER)

    def test_require_permission_insufficient_permission(self,
                                                        permissions_roles,
                                                        auth_service_permissions,
                                                        permissions_repos):
        """Test require_permission avec permission insuffisante"""
        # Créer un employé support
        support_data = auth_service_permissions.create_employee_with_password(
            name="Support Employee", email="support_perms@test.com",
            role_id=permissions_roles["support"].id, password="TestPassword123!"
        )
        support_employee = permissions_repos["employee"].get_by_id(support_data["id"])

        # Devrait lever une exception
        with pytest.raises(PermissionError, match="does not have permission"):
            require_permission(support_employee, Permission.DELETE_CUSTOMER)

    def test_can_update_own_assigned_customer_success(self,
                                                      permissions_roles,
                                                      auth_service_permissions,
                                                      permissions_repos):
        """Test can_update_own_assigned_customer avec client assigné"""
        # Créer employé sales
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Assigned", email="sales_assigned@test.com",
            role_id=permissions_roles["sales"].id, password="TestPassword123!"
        )
        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])

        # Créer client assigné à cet employé
        customer = permissions_repos["customer"].create({
            "full_name": "Assigned Customer",
            "email": "assigned@test.com",
            "phone": "0123456789",
            "sales_contact_id": sales_employee.id
        })

        # Sales peut modifier son client assigné
        assert can_update_own_assigned_customer(sales_employee, customer) is True

    def test_can_update_own_assigned_customer_failure(self,
                                                      permissions_roles,
                                                      auth_service_permissions,
                                                      permissions_repos):
        """Test can_update_own_assigned_customer avec client non assigné"""
        # Créer deux employés sales
        sales1_data = auth_service_permissions.create_employee_with_password(
            name="Sales 1", email="sales1_assigned@test.com",
            role_id=permissions_roles["sales"].id, password="TestPassword123!"
        )
        sales2_data = auth_service_permissions.create_employee_with_password(
            name="Sales 2", email="sales2_assigned@test.com",
            role_id=permissions_roles["sales"].id, password="TestPassword123!"
        )

        sales1_employee = permissions_repos["employee"].get_by_id(sales1_data["id"])
        sales2_employee = permissions_repos["employee"].get_by_id(sales2_data["id"])

        # Créer client assigné à sales1
        customer = permissions_repos["customer"].create({
            "full_name": "Other Customer",
            "email": "other@test.com",
            "phone": "0123456789",
            "sales_contact_id": sales1_employee.id
        })

        # Sales2 ne peut pas modifier le client de sales1
        assert can_update_own_assigned_customer(sales2_employee, customer) is False

    def test_can_update_own_assigned_customer_management(self,
                                                         permissions_roles,
                                                         auth_service_permissions,
                                                         permissions_repos):
        """Test can_update_own_assigned_customer avec rôle management"""
        # Créer employé management
        mgmt_data = auth_service_permissions.create_employee_with_password(
            name="Manager", email="manager_assigned@test.com",
            role_id=permissions_roles["management"].id, password="TestPassword123!"
        )
        manager = permissions_repos["employee"].get_by_id(mgmt_data["id"])

        # Créer client quelconque
        customer = permissions_repos["customer"].create({
            "full_name": "Any Customer",
            "email": "any@test.com",
            "phone": "0123456789"
        })

        # Management peut modifier n'importe quel client
        assert can_update_own_assigned_customer(manager, customer) is True

    def test_can_update_with_none_parameters(self):
        """Test méthodes can_update avec paramètres None"""
        assert can_update_own_assigned_customer(None, None) is False
        assert can_update_own_assigned_customer(None, "fake_customer") is False

    def test_permission_error_exception(self):
        """Test que PermissionError est une exception valide"""
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

        # Test rôle invalide
        invalid_desc = describe_permissions("invalid_role")
        assert ("No permissions"
                in invalid_desc or "Unknown role"
                in invalid_desc or "Invalid role"
                in invalid_desc)

    def test_can_update_own_assigned_contract(self,
                                              permissions_roles,
                                              auth_service_permissions,
                                              permissions_repos):
        """Test can_update_own_assigned_contract method"""
        # Créer employé sales
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Contract", email="sales_contract@test.com",
            role_id=permissions_roles["sales"].id, password="TestPassword123!"
        )
        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])

        # Créer client et contrat
        customer = permissions_repos["customer"].create({
            "full_name": "Contract Customer",
            "email": "contract_customer@test.com",
            "phone": "0123456789"
        })

        contract = permissions_repos["contract"].create({
            "customer_id": customer.id,
            "sales_contact_id": sales_employee.id,
            "total_amount": 5000.0,
            "remaining_amount": 2500.0,
            "date_created": datetime.now(),
            "signed": False
        })

        # Sales peut modifier son propre contrat
        assert can_update_own_assigned_contract(sales_employee, contract) is True

        # Test avec None
        assert can_update_own_assigned_contract(None, contract) is False
        assert can_update_own_assigned_contract(sales_employee, None) is False

    def test_can_update_own_assigned_event(self,
                                           permissions_roles,
                                           auth_service_permissions,
                                           permissions_repos):
        """Test can_update_own_assigned_event method"""
        # Créer employés
        sales_data = auth_service_permissions.create_employee_with_password(
            name="Sales Event Test", email="sales_event_test@test.com",
            role_id=permissions_roles["sales"].id, password="TestPassword123!"
        )
        support_data = auth_service_permissions.create_employee_with_password(
            name="Support Event Test", email="support_event_test@test.com",
            role_id=permissions_roles["support"].id, password="TestPassword123!"
        )

        sales_employee = permissions_repos["employee"].get_by_id(sales_data["id"])
        support_employee = permissions_repos["employee"].get_by_id(support_data["id"])

        # Créer client, contrat et événement
        customer = permissions_repos["customer"].create({
            "full_name": "Event Customer",
            "email": "event_customer@test.com",
            "phone": "0123456789"
        })

        contract = permissions_repos["contract"].create({
            "customer_id": customer.id,
            "sales_contact_id": sales_employee.id,
            "total_amount": 3000.0,
            "remaining_amount": 1500.0,
            "date_created": datetime.now(),
            "signed": True
        })

        event = permissions_repos["event"].create({
            "contract_id": contract.id,
            "customer_id": customer.id,
            "support_contact_id": support_employee.id,
            "name": "Test Event Permission",
            "date_start": datetime.now(),
            "date_end": datetime.now(),
            "location": "Test Location",
            "attendees": 50,
            "notes": "Permission test"
        })

        # Support peut modifier son événement assigné
        assert can_update_own_assigned_event(support_employee, event) is True

        # Sales ne peut pas modifier l'événement assigné au support
        assert can_update_own_assigned_event(sales_employee, event) is False

        # Test avec None
        assert can_update_own_assigned_event(None, event) is False
