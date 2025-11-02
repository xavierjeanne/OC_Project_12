"""
Configuration des fixtures pour tests d'intégration
Tests avec base de données PostgreSQL réelle
"""
# Les fixtures de base sont héritées du conftest.py parent
# Ce fichier peut contenir des fixtures spécifiques aux tests d'intégration

import pytest
from services.auth import AuthService
from repositories.customer import CustomerRepository
from repositories.employee import EmployeeRepository
from repositories.contract import ContractRepository  
from repositories.event import EventRepository


@pytest.fixture
def integration_repos(test_db):
    """Repositories pour tests d'intégration"""
    return {
        "customer": CustomerRepository(test_db),
        "employee": EmployeeRepository(test_db),
        "contract": ContractRepository(test_db),
        "event": EventRepository(test_db)
    }


@pytest.fixture
def auth_service_integration():
    """Service d'authentification pour tests d'intégration"""
    return AuthService()


@pytest.fixture
def sample_integration_data():
    """Données de test pour intégration"""
    return {
        "customer": {
            "full_name": "Integration Test Customer",
            "email": "integration@test.com",
            "phone": "0123456789",
            "company_name": "Integration Corp"
        },
        "employee": {
            "name": "Integration Employee",
            "email": "employee@integration.com"
        }
    }