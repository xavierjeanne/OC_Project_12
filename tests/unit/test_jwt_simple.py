"""
Tests for JWT Service - Simplified Version
Tests core JWT functionality
"""

import pytest
import jwt
import os
from unittest.mock import patch
from services.jwt_service import JWTService


class TestJWTServiceSimple:
    """Simplified test suite for JWT Service"""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service instance"""
        return JWTService()

    @pytest.fixture
    def sample_employee_data(self):
        """Sample employee data for testing"""
        return {
            "id": 1,
            "employee_number": "EMP001",
            "name": "Test User",
            "email": "test@example.com",
            "role": "admin",
            "role_id": 4,
        }

    def test_create_access_token(self, jwt_service, sample_employee_data):
        """Test creating access token"""
        with patch.dict(os.environ, {"EPIC_EVENTS_JWT_SECRET": "test_secret_key"}):
            token = jwt_service.create_access_token(sample_employee_data)

            assert isinstance(token, str)
            assert len(token) > 0

            # Verify token can be decoded
            secret = jwt_service._get_secret_key()
            payload = jwt.decode(token, secret, algorithms=[jwt_service.algorithm])

            assert payload["sub"] == "1"
            assert payload["employee_number"] == "EMP001"
            assert payload["name"] == "Test User"
            assert payload["type"] == "access"

    def test_create_refresh_token(self, jwt_service, sample_employee_data):
        """Test creating refresh token"""
        with patch.dict(os.environ, {"EPIC_EVENTS_JWT_SECRET": "test_secret_key"}):
            token = jwt_service.create_refresh_token(sample_employee_data)

            assert isinstance(token, str)
            assert len(token) > 0

            # Verify token structure
            secret = jwt_service._get_secret_key()
            payload = jwt.decode(token, secret, algorithms=[jwt_service.algorithm])

            assert payload["sub"] == "1"
            assert payload["type"] == "refresh"

    def test_verify_valid_token(self, jwt_service, sample_employee_data):
        """Test verifying valid tokens"""
        with patch.dict(os.environ, {"EPIC_EVENTS_JWT_SECRET": "test_secret_key"}):
            access_token = jwt_service.create_access_token(sample_employee_data)
            refresh_token = jwt_service.create_refresh_token(sample_employee_data)

            # Verify access token
            access_payload = jwt_service.verify_token(access_token, "access")
            assert access_payload is not None
            assert access_payload["type"] == "access"

            # Verify refresh token
            refresh_payload = jwt_service.verify_token(refresh_token, "refresh")
            assert refresh_payload is not None
            assert refresh_payload["type"] == "refresh"

    def test_verify_invalid_token(self, jwt_service):
        """Test verifying invalid token"""
        with patch.dict(os.environ, {"EPIC_EVENTS_JWT_SECRET": "test_secret_key"}):
            payload = jwt_service.verify_token("invalid_token", "access")
            assert payload is None

    def test_verify_wrong_token_type(self, jwt_service, sample_employee_data):
        """Test verifying token with wrong type"""
        with patch.dict(os.environ, {"EPIC_EVENTS_JWT_SECRET": "test_secret_key"}):
            access_token = jwt_service.create_access_token(sample_employee_data)

            # Try to verify access token as refresh token
            payload = jwt_service.verify_token(access_token, "refresh")
            assert payload is None

    def test_algorithm_setting(self, jwt_service):
        """Test that correct algorithm is used"""
        assert jwt_service.algorithm == "HS256"

    def test_secret_key_generation(self, jwt_service):
        """Test secret key functionality"""
        with patch.dict(os.environ, {"EPIC_EVENTS_JWT_SECRET": "test_secret"}):
            secret = jwt_service._get_secret_key()
            assert secret == "test_secret"

    def test_token_structure(self, jwt_service, sample_employee_data):
        """Test JWT token structure"""
        with patch.dict(os.environ, {"EPIC_EVENTS_JWT_SECRET": "test_secret_key"}):
            token = jwt_service.create_access_token(sample_employee_data)

            # JWT should have 3 parts separated by dots
            parts = token.split(".")
            assert len(parts) == 3
