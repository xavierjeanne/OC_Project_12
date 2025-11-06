"""
Tests to verify Sentry integration
"""

import pytest
from unittest.mock import patch, Mock
from utils.sentry_config import (
    init_sentry,
    log_employee_creation,
    log_employee_update,
    log_contract_signature,
    log_unexpected_error,
    filter_sensitive_data,
    capture_exceptions,
)


class TestSentryConfiguration:
    """Sentry configuration tests"""

    @patch("utils.sentry_config.os.getenv")
    @patch("utils.sentry_config.sentry_sdk.init")
    def test_init_sentry_with_dsn(self, mock_init, mock_getenv):
        """Test Sentry initialization with DSN"""
        mock_getenv.side_effect = lambda key, default=None: {
            "SENTRY_DSN": "https://test@sentry.io/123",
            "ENVIRONMENT": "test",
            "APP_VERSION": "1.0.0",
        }.get(key, default)

        init_sentry()

        mock_init.assert_called_once()
        call_args = mock_init.call_args[1]
        assert call_args["dsn"] == "https://test@sentry.io/123"
        assert call_args["environment"] == "test"
        assert call_args["send_default_pii"] is False
        assert call_args["release"] == "1.0.0"

    @patch("utils.sentry_config.os.getenv")
    @patch("utils.sentry_config.logger")
    def test_init_sentry_without_dsn(self, mock_logger, mock_getenv):
        """Test initialization without DSN (dev mode)"""
        mock_getenv.return_value = None

        init_sentry()

        mock_logger.warning.assert_called_once_with(
            "SENTRY_DSN not found in environment variables. Sentry monitoring disabled."
        )

    def test_filter_sensitive_data_password(self):
        """Test filtering of sensitive data (password)"""
        event = {"message": "User login failed with password: secret123"}

        filtered_event = filter_sensitive_data(event, None)

        assert "password" not in filtered_event["message"]
        assert "***FILTERED***" in filtered_event["message"]

    def test_filter_sensitive_data_vars(self):
        """Test le filtrage des variables sensibles"""
        event = {
            "exception": {
                "values": [
                    {
                        "stacktrace": {
                            "frames": [
                                {
                                    "vars": {
                                        "password": "secret123",
                                        "user_token": "abc123",
                                        "username": "test_user",
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

        filtered_event = filter_sensitive_data(event, None)

        frame_vars = filtered_event["exception"]["values"][0]["stacktrace"]["frames"][
            0
        ]["vars"]
        assert frame_vars["password"] == "***FILTERED***"
        assert frame_vars["user_token"] == "***FILTERED***"
        assert frame_vars["username"] == "test_user"  # Non sensible


class TestSentryLogging:
    """Tests for business-level logging functions"""

    @patch("utils.sentry_config.sentry_sdk.add_breadcrumb")
    @patch("utils.sentry_config.logger")
    def test_log_employee_creation(self, mock_logger, mock_breadcrumb):
        """Test employee creation logging"""
        log_employee_creation(123, "Jean Dupont", "admin@test.com")

        mock_breadcrumb.assert_called_once_with(
            message="Employee created: Jean Dupont",
            category="employee.create",
            data={
                "employee_id": 123,
                "employee_name": "Jean Dupont",
                "created_by": "admin@test.com",
            },
            level="info",
        )

        mock_logger.info.assert_called_once()

    @patch("utils.sentry_config.sentry_sdk.add_breadcrumb")
    @patch("utils.sentry_config.logger")
    def test_log_employee_update(self, mock_logger, mock_breadcrumb):
        """Test employee modification logging"""
        changes = {"name": {"old": "Jean", "new": "Jean Dupont"}}

        log_employee_update(123, "Jean Dupont", "admin@test.com", changes)

        mock_breadcrumb.assert_called_once_with(
            message="Employee updated: Jean Dupont",
            category="employee.update",
            data={
                "employee_id": 123,
                "employee_name": "Jean Dupont",
                "updated_by": "admin@test.com",
                "changes": changes,
            },
            level="info",
        )

    @patch("utils.sentry_config.sentry_sdk.add_breadcrumb")
    @patch("utils.sentry_config.sentry_sdk.capture_message")
    @patch("utils.sentry_config.logger")
    def test_log_contract_signature_high_value(
        self, mock_logger, mock_capture, mock_breadcrumb
    ):
        """Test high-value contract signing logging"""
        log_contract_signature(456, "Client Important", "sales@test.com", 15000.0)

        mock_breadcrumb.assert_called_once()
        mock_capture.assert_called_once_with(
            "High-value contract signed: €15,000.00 for Client Important", level="info"
        )

    @patch("utils.sentry_config.sentry_sdk.capture_exception")
    @patch("utils.sentry_config.logger")
    def test_log_unexpected_error(self, mock_logger, mock_capture):
        """Test le logging d'erreur inattendue"""
        error = ValueError("Test error")
        context = {"test": "context"}

        log_unexpected_error(error, context)

        mock_capture.assert_called_once_with(error)
        mock_logger.error.assert_called_once()


class TestCaptureExceptionsDecorator:
    """Tests for the capture_exceptions decorator"""

    def test_capture_exceptions_decorator_success(self):
        """Test that decorator doesn't interfere with normal functions"""

        @capture_exceptions
        def test_function(x, y):
            return x + y

        result = test_function(2, 3)
        assert result == 5

    @patch("utils.sentry_config.log_unexpected_error")
    def test_capture_exceptions_decorator_with_error(self, mock_log_error):
        """Test that decorator captures errors"""

        @capture_exceptions
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_function()

        mock_log_error.assert_called_once()
        args = mock_log_error.call_args[0]
        assert isinstance(args[0], ValueError)
        assert args[0].args[0] == "Test error"


class TestSentryIntegration:
    """Sentry integration tests"""

    @patch.dict(
        "os.environ",
        {"SENTRY_DSN": "https://test@sentry.io/123", "ENVIRONMENT": "test"},
    )
    def test_sentry_integration_flow(self):
        """Test complet du flow Sentry"""
        # This test verifies Sentry can be initialized without error
        # and that logging functions can be invoked
        try:
            init_sentry()
            log_employee_creation(1, "Test User", "test@example.com")
            log_contract_signature(1, "Test Client", "sales@example.com", 1000.0)

            # Test captured exception
            try:
                raise ValueError("Test exception for Sentry")
            except ValueError as e:
                log_unexpected_error(e, {"test": "context"})

        except Exception as e:
            pytest.fail(f"Sentry integration failed: {e}")

    @patch("utils.sentry_config.sentry_sdk")
    def test_breadcrumb_integration(self, mock_sentry_sdk):
        """Test breadcrumb integration"""
        mock_sentry_sdk.add_breadcrumb = Mock()

        log_employee_creation(1, "Test User", "admin@test.com")

        # Verify that a breadcrumb was added
        mock_sentry_sdk.add_breadcrumb.assert_called_once()
        call_args = mock_sentry_sdk.add_breadcrumb.call_args[1]

        assert call_args["category"] == "employee.create"
        assert call_args["level"] == "info"
        assert "Test User" in call_args["message"]
