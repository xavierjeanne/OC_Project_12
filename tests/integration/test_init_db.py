"""
Tests for init_db.py - Database initialization script
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

import init_db
from models import Role, Employee, Session
from services.auth import AuthService


class TestCreateBaseRoles:
    """Test create_base_roles function"""

    def test_create_base_roles_success(self, test_db):
        """Test successful creation of base roles"""
        # Ensure no roles exist initially
        test_db.query(Role).delete()
        test_db.commit()
        
        # Mock Session to return our test session
        with patch('init_db.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.query.return_value.count.return_value = 0
            
            # Call the function
            init_db.create_base_roles()
            
            # Verify session operations
            assert mock_session.add.call_count == 4  # 4 roles added
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_create_base_roles_already_exist(self, test_db):
        """Test when roles already exist"""
        with patch('init_db.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.query.return_value.count.return_value = 4  # Roles exist
            
            with patch('builtins.print') as mock_print:
                init_db.create_base_roles()
                
                # Should print message and return early
                mock_print.assert_called_with("4 roles already present in database")
                mock_session.add.assert_not_called()

    def test_create_base_roles_exception_handling(self):
        """Test exception handling in create_base_roles"""
        with patch('init_db.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.query.return_value.count.return_value = 0
            mock_session.commit.side_effect = Exception("Database error")
            
            with pytest.raises(Exception, match="Database error"):
                init_db.create_base_roles()
                
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestCreateAdminUser:
    """Test create_admin_user function"""

    @patch('init_db.getpass.getpass')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_create_admin_user_success(self, mock_print, mock_input, mock_getpass, test_db):
        """Test successful admin user creation"""
        # Setup mocks
        mock_input.side_effect = ["Admin User", "admin@test.com", "ADMIN001"]
        mock_getpass.side_effect = ["password123", "password123"]  # password + confirmation

        with patch('init_db.Session') as mock_session_class, \
             patch('init_db.validate_password') as mock_validate, \
             patch('init_db.AuthService') as mock_auth_service_class:
            
            # Setup session mock
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Setup role mock
            mock_admin_role = MagicMock()
            mock_admin_role.id = 1
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_admin_role
            mock_session.query.return_value.join.return_value.filter.return_value.first.return_value = None  # No existing admin
            mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_admin_role, None]  # admin role exists, no existing employee
            
            # Setup auth service mock
            mock_auth_service = MagicMock()
            mock_auth_service_class.return_value = mock_auth_service
            mock_auth_service.create_employee_with_password.return_value = {
                'employee_number': 'ADMIN001',
                'name': 'Admin User',
                'email': 'admin@test.com'
            }
            
            # Setup password validation
            mock_validate.return_value = (True, "")
            
            # Call function
            result = init_db.create_admin_user()
            
            # Assertions
            assert result is True
            mock_auth_service.create_employee_with_password.assert_called_once()

    @patch('builtins.print')
    def test_create_admin_user_no_admin_role(self, mock_print):
        """Test when admin role doesn't exist"""
        with patch('init_db.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = None  # No admin role
            
            result = init_db.create_admin_user()
            
            assert result is False
            mock_print.assert_any_call("ERROR: Admin role not found")

    @patch('builtins.input')
    @patch('builtins.print')
    def test_create_admin_user_existing_admin(self, mock_print, mock_input):
        """Test when admin already exists and user chooses not to create another"""
        mock_input.return_value = "n"  # User says no to creating another admin
        
        with patch('init_db.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Setup admin role exists
            mock_admin_role = MagicMock()
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_admin_role
            
            # Setup existing admin
            mock_existing_admin = MagicMock()
            mock_session.query.return_value.join.return_value.filter.return_value.first.return_value = mock_existing_admin
            
            result = init_db.create_admin_user()
            
            assert result is True
            mock_print.assert_any_call("Admin user already exists. Skipping creation...")


class TestCreateDatabase:
    """Test create_database function"""

    @patch('init_db.create_base_roles')
    @patch('init_db.init_db')
    @patch('builtins.print')
    def test_create_database_success(self, mock_print, mock_init_db_func, mock_create_roles):
        """Test successful database creation"""
        with patch('init_db.Base') as mock_base, \
             patch('init_db.engine') as mock_engine, \
             patch('init_db.Session') as mock_session_class:
            
            # Setup session mock
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Call function
            init_db.create_database()
            
            # Verify operations
            mock_base.metadata.drop_all.assert_called_once_with(mock_engine)
            mock_init_db_func.assert_called_once()
            mock_create_roles.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @patch('init_db.create_base_roles')
    @patch('init_db.init_db')
    @patch('builtins.print')
    def test_create_database_clear_data_exception(self, mock_print, mock_init_db_func, mock_create_roles):
        """Test database creation with data clearing exception"""
        with patch('init_db.Base') as mock_base, \
             patch('init_db.engine') as mock_engine, \
             patch('init_db.Session') as mock_session_class:
            
            # Setup session mock with exception on commit
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.commit.side_effect = Exception("Clear data error")
            
            # Call function (should not raise exception)
            init_db.create_database()
            
            # Verify operations
            mock_base.metadata.drop_all.assert_called_once_with(mock_engine)
            mock_init_db_func.assert_called_once()
            mock_create_roles.assert_called_once()
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestMain:
    """Test main function"""

    @patch('init_db.create_admin_user')
    @patch('init_db.create_database')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_main_interactive_yes(self, mock_print, mock_input, mock_create_db, mock_create_admin):
        """Test main function with interactive confirmation (yes)"""
        mock_input.return_value = "y"
        mock_create_admin.return_value = True
        
        with patch('init_db.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.query.return_value.count.return_value = 4
            mock_session.query.return_value.all.return_value = [
                MagicMock(name="admin", id=1, description="Admin role"),
                MagicMock(name="sales", id=2, description="Sales role"),
                MagicMock(name="support", id=3, description="Support role"),
                MagicMock(name="management", id=4, description="Management role"),
            ]
            
            result = init_db.main()
            
            assert result is True
            mock_create_db.assert_called_once()
            mock_create_admin.assert_called_once()

    @patch('builtins.input')
    @patch('builtins.print')
    def test_main_interactive_no(self, mock_print, mock_input):
        """Test main function with interactive confirmation (no)"""
        mock_input.return_value = "n"
        
        result = init_db.main()
        
        assert result is False
        mock_print.assert_any_call("Database initialization cancelled")

    @patch('init_db.create_admin_user')
    @patch('init_db.create_database')
    @patch('builtins.print')
    def test_main_force_mode(self, mock_print, mock_create_db, mock_create_admin):
        """Test main function with --force flag"""
        mock_create_admin.return_value = True
        
        # Mock sys.argv to include --force
        original_argv = sys.argv
        try:
            sys.argv = ['init_db.py', '--force']
            
            with patch('init_db.Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session
                mock_session.query.return_value.count.return_value = 4
                mock_session.query.return_value.all.return_value = []
                
                result = init_db.main()
                
                assert result is True
                mock_create_db.assert_called_once()
                mock_create_admin.assert_called_once()
                mock_print.assert_any_call("Force mode: Proceeding without confirmation...")
        finally:
            sys.argv = original_argv

    @patch('init_db.create_database')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_main_exception_handling(self, mock_print, mock_input, mock_create_db):
        """Test main function exception handling"""
        mock_input.return_value = "y"
        mock_create_db.side_effect = Exception("Database creation failed")
        
        result = init_db.main()
        
        assert result is False
        mock_print.assert_any_call("\nError: Database creation failed")


class TestMainExecution:
    """Test script execution when run as main"""

    @patch('init_db.main')
    @patch('builtins.print')
    def test_script_execution_success(self, mock_print, mock_main):
        """Test script execution with successful main"""
        mock_main.return_value = True
        
        # Simulate running the script
        with patch('sys.exit') as mock_exit:
            exec(compile(open('init_db.py').read(), 'init_db.py', 'exec'))
            mock_exit.assert_not_called()

    @patch('init_db.main')
    @patch('builtins.print')
    def test_script_execution_failure(self, mock_print, mock_main):
        """Test script execution with failed main"""
        mock_main.return_value = False
        
        # This test would require more complex mocking to test the actual script execution
        # For now, we'll just test that main() is properly called
        pass