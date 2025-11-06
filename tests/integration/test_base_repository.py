"""
Tests for BaseRepository
Demonstrates how to test the repository pattern with PostgreSQL
"""

import pytest
from models import Customer
from repositories.customer import CustomerRepository


@pytest.fixture
def customer_repo(test_db):
    """Create a customer repository instance"""
    return CustomerRepository(test_db)


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return {
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "0123456789",
        "company_name": "ACME Corp",
    }


# Tests for BaseRepository methods
class TestBaseRepository:
    """Test suite for BaseRepository CRUD operations"""

    def test_create_entity(self, customer_repo, sample_customer_data):
        """Test creating a new entity"""
        customer = customer_repo.create(sample_customer_data)

        assert customer.id is not None
        assert customer.full_name == "John Doe"
        assert customer.email == "john@example.com"
        assert customer.company_name == "ACME Corp"

    def test_get_by_id_existing(self, customer_repo, sample_customer_data):
        """Test retrieving an existing entity by ID"""
        created = customer_repo.create(sample_customer_data)
        retrieved = customer_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.email == created.email

    def test_get_by_id_not_found(self, customer_repo):
        """Test retrieving a non-existent entity"""
        result = customer_repo.get_by_id(99999)
        assert result is None

    def test_get_all_empty(self, customer_repo):
        """Test getting all entities when database is empty"""
        results = customer_repo.get_all()
        assert len(results) == 0

    def test_get_all_with_data(self, customer_repo, sample_customer_data):
        """Test getting all entities"""
        customer_repo.create(sample_customer_data)
        customer_repo.create(
            {
                **sample_customer_data,
                "email": "jane@example.com",
                "full_name": "Jane Doe",
            }
        )

        results = customer_repo.get_all()
        assert len(results) == 2

    def test_get_all_with_pagination(self, customer_repo, sample_customer_data):
        """Test pagination with limit and offset"""
        # Create 5 customers
        for i in range(5):
            customer_repo.create(
                {
                    **sample_customer_data,
                    "email": f"user{i}@example.com",
                    "full_name": f"User {i}",
                }
            )

        # Get first 2
        page1 = customer_repo.get_all(limit=2, offset=0)
        assert len(page1) == 2

        # Get next 2
        page2 = customer_repo.get_all(limit=2, offset=2)
        assert len(page2) == 2

        # Verify they are different
        assert page1[0].id != page2[0].id

    def test_update_entity(self, customer_repo, sample_customer_data):
        """Test updating an entity"""
        customer = customer_repo.create(sample_customer_data)

        updated = customer_repo.update(customer.id, {"full_name": "John Smith"})

        assert updated is not None
        assert updated.full_name == "John Smith"
        assert updated.email == sample_customer_data["email"]

    def test_update_nonexistent(self, customer_repo):
        """Test updating a non-existent entity"""
        result = customer_repo.update(99999, {"full_name": "Test"})
        assert result is None

    def test_delete_entity(self, customer_repo, sample_customer_data):
        """Test deleting an entity"""
        customer = customer_repo.create(sample_customer_data)
        result = customer_repo.delete(customer.id)

        assert result is True

        # Verify it's deleted
        retrieved = customer_repo.get_by_id(customer.id)
        assert retrieved is None

    def test_delete_nonexistent(self, customer_repo):
        """Test deleting a non-existent entity"""
        result = customer_repo.delete(99999)
        assert result is False

    def test_filter_by(self, customer_repo, sample_customer_data):
        """Test filtering by specific criteria"""
        customer_repo.create(sample_customer_data)
        customer_repo.create(
            {
                **sample_customer_data,
                "email": "jane@example.com",
                "full_name": "Jane Doe",
                "company_name": "Other Corp",
            }
        )

        # Filter by company
        results = customer_repo.filter_by(company_name="ACME Corp")
        assert len(results) == 1
        assert results[0].company_name == "ACME Corp"

    def test_exists(self, customer_repo, sample_customer_data):
        """Test checking if entity exists"""
        customer = customer_repo.create(sample_customer_data)

        assert customer_repo.exists(customer.id) is True
        assert customer_repo.exists(99999) is False


# Example of testing with mocks
class TestWithMocks:
    """Examples of testing services with mocked repositories"""

    def test_service_with_mock_repository(self):
        """Example: Testing a service with a mocked repository"""
        from unittest.mock import MagicMock

        # Create a mock repository
        mock_repo = MagicMock(spec=CustomerRepository)
        mock_customer = Customer(id=1, full_name="John Doe", email="john@example.com")
        mock_repo.create.return_value = mock_customer

        # Use the mock in your service
        result = mock_repo.create({"full_name": "John Doe"})

        assert result.id == 1
        mock_repo.create.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
