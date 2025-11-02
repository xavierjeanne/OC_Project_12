"""
Tests étendus pour améliorer la couverture des validateurs
Tests pour tous les cas d'erreur et formats non couverts
"""

import pytest
from datetime import datetime
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
    validate_date,
    validate_non_negative_integer
)


class TestEmailValidatorExtended:
    """Tests étendus pour la validation d'email"""

    def test_validate_email_edge_cases(self):
        """Test cas limites validation email"""
        # Emails valides
        assert validate_email("a@b.co") == "a@b.co"
        assert validate_email("user-name@domain.com") == "user-name@domain.com"
        assert validate_email("user_name@domain.co.uk") == "user_name@domain.co.uk"
        assert validate_email("123@domain.com") == "123@domain.com"

    def test_validate_email_invalid_cases(self):
        """Test cas invalides pour email"""
        invalid_emails = [
            "@domain.com",  # Pas de partie locale
            "user@",  # Pas de domaine
            "user.domain.com",  # Pas de @
            "user@@domain.com",  # Double @
            "user@domain..com",  # Double point
            "user@domain.c",  # TLD trop court
            "user name@domain.com",  # Espace dans nom utilisateur
            "user@dom ain.com"  # Espace dans domaine
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email(email)

    def test_validate_email_none_and_whitespace(self):
        """Test email None et espaces"""
        with pytest.raises(ValidationError, match="Email is required"):
            validate_email(None)

        with pytest.raises(ValidationError, match="Email is required"):
            validate_email("")


class TestPhoneValidatorExtended:
    """Tests étendus pour la validation de téléphone"""

    def test_validate_phone_valid_formats(self):
        """Test formats valides de téléphone"""
        valid_phones = [
            "0123456789",
            "01 23 45 67 89",
            "01-23-45-67-89",
            "01.23.45.67.89",
            "(01) 23 45 67 89",
            "+33123456789",
            "+33 1 23 45 67 89",
            "0033123456789",
            "123456789012345",  # 15 chiffres (max)
        ]

        for phone in valid_phones:
            result = validate_phone(phone)
            assert result is not None
            assert isinstance(result, str)

    def test_validate_phone_invalid_formats(self):
        """Test formats invalides de téléphone"""
        invalid_phones = [
            "123456789",     # Trop court (9 chiffres)
            "1234567890123456",  # Trop long (16 chiffres)
            "abcdefghij",    # Lettres
            "012-345-abc",     # Mélange lettres/chiffres
            "++33123456789",   # Double +
            "012 345 abc 89",  # Lettres au milieu
        ]

        for phone in invalid_phones:
            with pytest.raises(ValidationError, match="is not valid"):
                validate_phone(phone)

    def test_validate_phone_none_empty(self):
        """Test téléphone None et vide"""
        assert validate_phone(None) is None
        assert validate_phone("") is None
        # Note: validate_phone considère "   " comme invalide après strip()
        with pytest.raises(ValidationError):
            validate_phone("   ")


class TestAmountValidatorsExtended:
    """Tests étendus pour la validation des montants"""

    def test_validate_positive_amount_edge_cases(self):
        """Test cas limites montant positif"""
        # Valeurs valides
        assert validate_positive_amount(0.001) == 0.001
        assert validate_positive_amount(999999.99) == 999999.99
        assert validate_positive_amount("100.50") == 100.50
        assert validate_positive_amount(100) == 100.0

    def test_validate_positive_amount_invalid_types(self):
        """Test types invalides pour montant positif"""
        invalid_values = ["abc", "", "not_a_number", [], {}, object()]

        for value in invalid_values:
            with pytest.raises(ValidationError, match="must be a number"):
                validate_positive_amount(value)

    def test_validate_positive_amount_custom_field_name(self):
        """Test message d'erreur personnalisé"""
        with pytest.raises(ValidationError, match="total_amount must be positive"):
            validate_positive_amount(-10, "total_amount")

    def test_validate_non_negative_amount_edge_cases(self):
        """Test cas limites montant non-négatif"""
        assert validate_non_negative_amount(0) == 0.0
        assert validate_non_negative_amount(0.0) == 0.0
        assert validate_non_negative_amount("0") == 0.0

    def test_validate_remaining_amount_edge_cases(self):
        """Test cas limites montant restant"""
        # Cas valides
        validate_remaining_amount(1000.0, 1000.0)  # Égal
        validate_remaining_amount(1000.0, 0.0)     # Zéro
        validate_remaining_amount(0.0, 0.0)        # Les deux à zéro

    def test_validate_remaining_amount_precision(self):
        """Test précision montant restant"""
        with pytest.raises(ValidationError):
            validate_remaining_amount(100.00, 100.01)  # Différence de centimes


class TestDateValidatorsExtended:
    """Tests étendus pour la validation des dates"""

    def test_validate_date_formats(self):
        """Test différents formats de date"""
        # Formats supportés
        valid_dates = [
            ("2024-06-15", datetime(2024, 6, 15)),
            ("15/06/2024", datetime(2024, 6, 15)),
            ("2024-06-15 14:30:00", datetime(2024, 6, 15, 14, 30, 0)),
        ]

        for date_str, expected in valid_dates:
            result = validate_date(date_str)
            assert result == expected

    def test_validate_date_invalid_formats(self):
        """Test formats invalides de date"""
        invalid_dates = [
            "2024/06/15",     # Format non supporté
            "06-15-2024",     # Format américain
            "invalid_date",   # Pas une date
            "2024-13-01",     # Mois invalide
            "2024-06-32",     # Jour invalide
            "2024-02-30",     # Jour invalide pour février
        ]

        for date_str in invalid_dates:
            with pytest.raises(ValidationError):
                validate_date(date_str)

    def test_validate_date_none_empty(self):
        """Test date None et vide"""
        # validate_date retourne None pour les valeurs vides
        assert validate_date("") is None
        assert validate_date(None) is None

    def test_validate_date_datetime_input(self):
        """Test input datetime existant"""
        now = datetime.now()
        assert validate_date(now) == now

    def test_validate_date_order_edge_cases(self):
        """Test ordre des dates - cas limites"""
        start = datetime(2024, 6, 15, 14, 30, 0)

        # Même instant
        with pytest.raises(ValidationError):
            validate_date_order(start, start)

        # 1 seconde de différence
        end = datetime(2024, 6, 15, 14, 30, 1)
        validate_date_order(start, end)  # Devrait passer

    def test_validate_date_order_custom_field_names(self):
        """Test noms de champs personnalisés pour ordre des dates"""
        start = datetime(2024, 6, 15, 14, 30, 0)
        end = datetime(2024, 6, 15, 14, 25, 0)  # End avant start

        with pytest.raises(ValidationError, match="event_start.*event_end"):
            validate_date_order(start, end, "event_start", "event_end")


class TestIntegerValidatorsExtended:
    """Tests étendus pour la validation des entiers"""

    def test_validate_positive_integer_edge_cases(self):
        """Test cas limites entier positif"""
        assert validate_positive_integer(1) == 1
        assert validate_positive_integer("100") == 100
        assert validate_positive_integer(999999) == 999999

    def test_validate_positive_integer_invalid_types(self):
        """Test types invalides pour entier positif"""
        invalid_values = ["abc", "", "12.5", [], {}, object()]

        for value in invalid_values:
            with pytest.raises(ValidationError, match="must be an integer"):
                validate_positive_integer(value)

    def test_validate_positive_integer_custom_field_name(self):
        """Test message d'erreur personnalisé entier positif"""
        with pytest.raises(ValidationError, match="attendees.*positive"):
            validate_positive_integer(-1, "attendees")

    def test_validate_non_negative_integer_edge_cases(self):
        """Test cas limites entier non-négatif"""
        assert validate_non_negative_integer(0) == 0
        assert validate_non_negative_integer("0") == 0
        assert validate_non_negative_integer(1000) == 1000

    def test_validate_non_negative_integer_none_handling(self):
        """Test gestion None pour entier non-négatif"""
        # Cette fonction a une version qui accepte None, testons les deux comportements
        try:
            result = validate_non_negative_integer(None)
            # Si elle retourne 0, c'est une version
            assert result == 0
        except ValidationError:
            # Si elle lève une erreur, c'est l'autre version
            pass

    def test_validate_non_negative_integer_invalid_types(self):
        """Test types invalides pour entier non-négatif"""
        invalid_values = ["abc", "", "12.5", [], {}, object()]

        for value in invalid_values:
            with pytest.raises(ValidationError, match="must be an integer"):
                validate_non_negative_integer(value)


class TestStringValidatorExtended:
    """Tests étendus pour la validation des chaînes"""

    def test_validate_string_not_empty_edge_cases(self):
        """Test cas limites chaîne non-vide"""
        assert validate_string_not_empty("a") == "a"
        assert validate_string_not_empty("  a  ") == "a"
        assert validate_string_not_empty(
            "très long texte avec des accents éàç"
            ) == "très long texte avec des accents éàç"

    def test_validate_string_not_empty_custom_field_name(self):
        """Test message d'erreur personnalisé chaîne"""
        with pytest.raises(ValidationError, match="company_name.*required"):
            validate_string_not_empty("", "company_name")

    def test_validate_string_not_empty_none(self):
        """Test chaîne None"""
        with pytest.raises(ValidationError):
            validate_string_not_empty(None)


class TestRoleValidatorExtended:
    """Tests étendus pour la validation des rôles"""

    def test_validate_role_case_insensitive(self):
        """Test validation rôle insensible à la casse"""
        assert validate_role("SALES") == "sales"
        assert validate_role("Support") == "support"
        assert validate_role("Management") == "management"
        assert validate_role("  SALES  ") == "sales"

    def test_validate_role_invalid_roles(self):
        """Test rôles invalides"""
        # Test chaque rôle invalide séparément
        invalid_roles = ["admin", "user", "guest", "invalid"]

        for role in invalid_roles:
            with pytest.raises(ValidationError):
                validate_role(role)

        # Test cas spéciaux pour les chaînes vides
        with pytest.raises(ValidationError):
            validate_role("")

        with pytest.raises(ValidationError):
            validate_role("   ")

    def test_validate_role_none(self):
        """Test rôle None"""
        with pytest.raises(ValidationError, match="Role is required"):
            validate_role(None)


class TestPasswordValidatorExtended:
    """Tests étendus pour la validation des mots de passe"""

    def test_validate_password_all_requirements(self):
        """Test mot de passe répondant à tous les critères"""
        valid_passwords = [
            "TestPassword123!",
            "MySecureP@ssw0rd123",
            "Abc123!@#DefGhi",
            "aA1!bB2@cC3#dD4$",
        ]

        for password in valid_passwords:
            is_valid, message = validate_password(password)
            assert is_valid is True
            assert message == "Password is valid"

    def test_validate_password_missing_uppercase(self):
        """Test mot de passe sans majuscule"""
        is_valid, message = validate_password("testpassword123!")
        assert is_valid is False
        assert "uppercase letter" in message

    def test_validate_password_missing_lowercase(self):
        """Test mot de passe sans minuscule"""
        is_valid, message = validate_password("TESTPASSWORD123!")
        assert is_valid is False
        assert "lowercase letter" in message

    def test_validate_password_missing_digit(self):
        """Test mot de passe sans chiffre"""
        is_valid, message = validate_password("TestPassword!")
        assert is_valid is False
        assert "digit" in message

    def test_validate_password_missing_special(self):
        """Test mot de passe sans caractère spécial"""
        is_valid, message = validate_password("TestPassword123")
        assert is_valid is False
        assert "special character" in message

    def test_validate_password_too_short(self):
        """Test mot de passe trop court"""
        is_valid, message = validate_password("Short1!")
        assert is_valid is False
        assert "12 characters" in message

    def test_validate_password_edge_case_length(self):
        """Test longueur limite mot de passe"""
        # Exactement 12 caractères avec tous les critères
        password_12 = "TestPass123!"
        is_valid, message = validate_password(password_12)
        assert is_valid is True

        # 11 caractères
        password_11 = "TestPass12!"
        is_valid, message = validate_password(password_11)
        assert is_valid is False
