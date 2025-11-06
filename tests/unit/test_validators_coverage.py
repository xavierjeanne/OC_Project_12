"""
Tests improvement for validators coverage
"""

import pytest
from datetime import datetime, timedelta

from utils.validators import (
    ValidationError,
    validate_email,
    validate_phone,
    validate_positive_amount,
    validate_non_negative_amount,
    validate_remaining_amount,
    validate_date_order,
    validate_password,
    validate_positive_integer,
    validate_role,
    validate_string_not_empty,
)


class TestValidators:
    """Tests for improving coverage of validators"""

    def test_validate_email_success(self):
        """Test validation email successful"""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("  TEST@EXAMPLE.COM  ") == "test@example.com"
        assert (
            validate_email("user.name+tag@domain.co.uk") == "user.name+tag@domain.co.uk"
        )

    def test_validate_email_errors(self):
        """Test validation email errors"""
        with pytest.raises(ValidationError, match="Email is required"):
            validate_email("")

        with pytest.raises(ValidationError, match="not valid"):
            validate_email("invalid-email")

    def test_validate_phone_success(self):
        """Test validation phone successful"""
        assert validate_phone("0123456789") == "0123456789"
        assert validate_phone("  01 23 45 67 89  ") == "01 23 45 67 89"
        validate_phone("  01 23 45 67 89  ") == "01 23 45 67 89"
        assert validate_phone("+33123456789") == "+33123456789"
        assert validate_phone(None) is None

    def test_validate_phone_errors(self):
        """Test validation phone errors"""
        with pytest.raises(ValidationError, match="is not valid"):
            validate_phone("abc")

    def test_validate_positive_amount_success(self):
        """Test validation positive amount successful"""
        assert validate_positive_amount(100.0) == 100.0
        assert validate_positive_amount(0.01) == 0.01

    def test_validate_positive_amount_errors(self):
        """Test validation positive amount errors"""
        with pytest.raises(ValidationError):
            validate_positive_amount(-10.0)

        with pytest.raises(ValidationError):
            validate_positive_amount(0.0)

    def test_validate_non_negative_amount_success(self):
        """Test validation non-negative amount successful"""
        assert validate_non_negative_amount(100.0) == 100.0
        assert validate_non_negative_amount(0.0) == 0.0

    def test_validate_non_negative_amount_errors(self):
        """Test validation non-negative amount errors"""
        with pytest.raises(ValidationError):
            validate_non_negative_amount(-10.0)

    def test_validate_remaining_amount_success(self):
        """Test validation remaining amount successful"""
        validate_remaining_amount(1000.0, 500.0)
        validate_remaining_amount(1000.0, 0.0)
        validate_remaining_amount(1000.0, 1000.0)

    def test_validate_remaining_amount_errors(self):
        """Test validation remaining amount errors"""
        with pytest.raises(ValidationError):
            validate_remaining_amount(1000.0, 1500.0)  # Remaining > total

    def test_validate_date_order_success(self):
        """Test validation date order successful"""
        start = datetime.now()
        end = start + timedelta(hours=2)

        validate_date_order(start, end)

    def test_validate_date_order_errors(self):
        """Test validation date order errors"""
        start = datetime.now()
        end = start - timedelta(hours=1)  # End avant start

        with pytest.raises(ValidationError):
            validate_date_order(start, end)

    def test_validate_password_success(self):
        """Test validation password successful"""
        # validate_password returns (bool, str)
        is_valid, message = validate_password("TestPassword123!")
        assert is_valid is True
        assert message == "Password is valid"

    def test_validate_password_errors(self):
        """Test validation password errors"""
        # Mot de passe trop court
        is_valid, message = validate_password("short")
        assert is_valid is False
        assert "12 characters" in message

    def test_validate_positive_integer_success(self):
        """Test validation positive integer successful"""
        assert validate_positive_integer(100) == 100
        assert validate_positive_integer(1) == 1

    def test_validate_positive_integer_errors(self):
        """Test validation positive integer errors"""
        with pytest.raises(ValidationError):
            validate_positive_integer(-10)

        with pytest.raises(ValidationError):
            validate_positive_integer(0)

    def test_validate_role_success(self):
        """Test validation role successful"""
        valid_roles = ["sales", "support", "management"]
        for role in valid_roles:
            assert validate_role(role) == role

    def test_validate_role_errors(self):
        """Test validation role errors"""
        with pytest.raises(ValidationError):
            validate_role("invalid_role")

    def test_validate_string_not_empty_success(self):
        """Test validation string not empty successful"""
        assert validate_string_not_empty("test") == "test"
        assert validate_string_not_empty("  trimmed  ") == "trimmed"

    def test_validate_string_not_empty_errors(self):
        """Test validation string not empty errors"""
        with pytest.raises(ValidationError):
            validate_string_not_empty("")

        with pytest.raises(ValidationError):
            validate_string_not_empty("   ")
