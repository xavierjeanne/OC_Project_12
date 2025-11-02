"""
Tests pour améliorer la couverture des validateurs
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
    validate_string_not_empty
)


class TestValidators:
    """Tests pour améliorer la couverture des validateurs"""

    def test_validate_email_success(self):
        """Test validation email réussie"""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("  TEST@EXAMPLE.COM  ") == "test@example.com"
        assert validate_email(
            "user.name+tag@domain.co.uk"
            ) == "user.name+tag@domain.co.uk"

    def test_validate_email_errors(self):
        """Test erreurs validation email"""
        with pytest.raises(ValidationError, match="Email is required"):
            validate_email("")

        with pytest.raises(ValidationError, match="not valid"):
            validate_email("invalid-email")

    def test_validate_phone_success(self):
        """Test validation téléphone réussie"""
        assert validate_phone("0123456789") == "0123456789"
        assert validate_phone(
            "  01 23 45 67 89  "
            ) == "01 23 45 67 89"
        validate_phone("  01 23 45 67 89  ") == "01 23 45 67 89"
        assert validate_phone("+33123456789") == "+33123456789"
        assert validate_phone(None) is None

    def test_validate_phone_errors(self):
        """Test erreurs validation téléphone"""
        with pytest.raises(ValidationError, match="is not valid"):
            validate_phone("abc")

    def test_validate_positive_amount_success(self):
        """Test validation montant positif réussie"""
        assert validate_positive_amount(100.0) == 100.0
        assert validate_positive_amount(0.01) == 0.01

    def test_validate_positive_amount_errors(self):
        """Test erreurs validation montant positif"""
        with pytest.raises(ValidationError):
            validate_positive_amount(-10.0)

        with pytest.raises(ValidationError):
            validate_positive_amount(0.0)  # Doit être positif, pas zéro

    def test_validate_non_negative_amount_success(self):
        """Test validation montant non-négatif réussie"""
        assert validate_non_negative_amount(100.0) == 100.0
        assert validate_non_negative_amount(0.0) == 0.0

    def test_validate_non_negative_amount_errors(self):
        """Test erreurs validation montant non-négatif"""
        with pytest.raises(ValidationError):
            validate_non_negative_amount(-10.0)

    def test_validate_remaining_amount_success(self):
        """Test validation montant restant réussie"""
        # Ne devrait pas lever d'exception
        validate_remaining_amount(1000.0, 500.0)
        validate_remaining_amount(1000.0, 0.0)
        validate_remaining_amount(1000.0, 1000.0)

    def test_validate_remaining_amount_errors(self):
        """Test erreurs validation montant restant"""
        with pytest.raises(ValidationError):
            validate_remaining_amount(1000.0, 1500.0)  # Restant > total

    def test_validate_date_order_success(self):
        """Test validation ordre des dates réussie"""
        start = datetime.now()
        end = start + timedelta(hours=2)

        validate_date_order(start, end)

    def test_validate_date_order_errors(self):
        """Test erreurs validation ordre des dates"""
        start = datetime.now()
        end = start - timedelta(hours=1)  # End avant start

        with pytest.raises(ValidationError):
            validate_date_order(start, end)

    def test_validate_password_success(self):
        """Test validation mot de passe réussie"""
        # validate_password retourne (bool, str)
        is_valid, message = validate_password("TestPassword123!")
        assert is_valid is True
        assert message == "Password is valid"

    def test_validate_password_errors(self):
        """Test erreurs validation mot de passe"""
        # Mot de passe trop court
        is_valid, message = validate_password("short")
        assert is_valid is False
        assert "12 characters" in message

    def test_validate_positive_integer_success(self):
        """Test validation entier positif réussie"""
        assert validate_positive_integer(100) == 100
        assert validate_positive_integer(1) == 1

    def test_validate_positive_integer_errors(self):
        """Test erreurs validation entier positif"""
        with pytest.raises(ValidationError):
            validate_positive_integer(-10)

        with pytest.raises(ValidationError):
            validate_positive_integer(0)

    def test_validate_role_success(self):
        """Test validation rôle réussie"""
        valid_roles = ["sales", "support", "management"]  # Pas d'admin selon le code
        for role in valid_roles:
            assert validate_role(role) == role

    def test_validate_role_errors(self):
        """Test erreurs validation rôle"""
        with pytest.raises(ValidationError):
            validate_role("invalid_role")

    def test_validate_string_not_empty_success(self):
        """Test validation chaîne non-vide réussie"""
        assert validate_string_not_empty("test") == "test"
        assert validate_string_not_empty("  trimmed  ") == "trimmed"

    def test_validate_string_not_empty_errors(self):
        """Test erreurs validation chaîne non-vide"""
        with pytest.raises(ValidationError):
            validate_string_not_empty("")

        with pytest.raises(ValidationError):
            validate_string_not_empty("   ")
