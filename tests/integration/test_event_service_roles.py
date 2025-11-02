"""
Tests for EventService with role-based access control
Tests the list_events functionality with different user roles
"""

import pytest
from unittest.mock import MagicMock, patch
from services.event import EventService
from utils.permissions import Permission


class TestEventServiceRoleBasedAccess:
    """Test suite for EventService role-based access control"""

    @pytest.fixture
    def mock_repository(self):
        """Mock event repository"""
        return MagicMock()

    @pytest.fixture
    def event_service(self, mock_repository):
        """Create EventService with mocked repository"""
        return EventService(mock_repository)

    @pytest.fixture
    def admin_user(self):
        """Admin user fixture"""
        return {
            'id': 1,
            'name': 'Admin User',
            'role': 'admin',
            'role_id': 4
        }

    @pytest.fixture
    def management_user(self):
        """Management user fixture"""
        return {
            'id': 2,
            'name': 'Manager User',
            'role': 'management',
            'role_id': 3
        }

    @pytest.fixture
    def sales_user(self):
        """Sales user fixture"""
        return {
            'id': 3,
            'name': 'Sales User',
            'role': 'sales',
            'role_id': 1
        }

    @pytest.fixture
    def support_user(self):
        """Support user fixture"""
        return {
            'id': 4,
            'name': 'Support User',
            'role': 'support',
            'role_id': 2
        }

    @patch('services.event.require_permission')
    def test_list_events_admin_sees_all(self, mock_require_permission,
                                        event_service, mock_repository,
                                        admin_user):
        """Test that admin users see all events"""
        # Setup
        mock_events = [MagicMock(), MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_events

        # Execute
        result = event_service.list_events(admin_user)

        # Verify
        mock_require_permission.assert_called_once_with(admin_user,
                                                        Permission.READ_EVENT)
        mock_repository.get_all.assert_called_once()
        assert result == mock_events

    @patch('services.event.require_permission')
    def test_list_events_management_sees_all(self, mock_require_permission,
                                             event_service, mock_repository,
                                             management_user):
        """Test that management users see all events"""
        # Setup
        mock_events = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_events

        # Execute
        result = event_service.list_events(management_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            management_user, Permission.READ_EVENT)
        mock_repository.get_all.assert_called_once()
        assert result == mock_events

    @patch('services.event.require_permission')
    def test_list_events_sales_sees_all(self, mock_require_permission,
                                        event_service, mock_repository,
                                        sales_user):
        """Test that sales users see all events (for coordination)"""
        # Setup
        mock_events = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_events

        # Execute
        result = event_service.list_events(sales_user)

        # Verify
        mock_require_permission.assert_called_once_with(sales_user,
                                                        Permission.READ_EVENT)
        mock_repository.get_all.assert_called_once()
        assert result == mock_events

    @patch('services.event.require_permission')
    def test_list_events_support_sees_all_events(self,
                                                    mock_require_permission,
                                                    event_service,
                                                    mock_repository,
                                                    support_user):
        """Test that support users now see ALL events (conformité)"""
        # Setup
        mock_events = [MagicMock(), MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_events

        # Execute
        result = event_service.list_events(support_user)

        # Verify
        mock_require_permission.assert_called_once_with(
            support_user,
            Permission.READ_EVENT)
        mock_repository.get_all.assert_called_once()
        mock_repository.find_by_support_contact.assert_not_called()
        assert result == mock_events

    @patch('services.event.require_permission')
    def test_list_events_unknown_role_sees_all_events(self,
                                                    mock_require_permission,
                                                    event_service,
                                                    mock_repository):
        """Test that even unknown roles now see ALL events (conformité)"""
        # Setup
        unknown_user = {'id': 5, 'name': 'Unknown', 'role': 'unknown'}
        mock_events = [MagicMock(), MagicMock()]
        mock_repository.get_all.return_value = mock_events

        # Execute
        result = event_service.list_events(unknown_user)

        # Verify
        mock_require_permission.assert_called_once_with(unknown_user,
                                                        Permission.READ_EVENT
                                                        )
        mock_repository.get_all.assert_called_once()
        mock_repository.find_by_support_contact.assert_not_called()
        assert result == mock_events
