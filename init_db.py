"""
CRM Database Initialization
Creates tables and inserts base data (roles)
"""

from models import Base, Role, Session, init_db
from db.config import engine
from services.auth import AuthService
import getpass
from utils.validators import validate_password


def create_base_roles():
    """Creates base system roles"""
    session = Session()

    try:
        # Check if roles already exist
        existing_roles = session.query(Role).count()
        if existing_roles > 0:
            print(f"{existing_roles} roles already present in database")
            return

        # Create the 3 base roles
        roles = [
            Role(
                name="sales",
                description="Sales team - Customer and contract management",
            ),
            Role(
                name="support",
                description="Support team - Event management and customer service",
            ),
            Role(name="management", description="Management - Full system access"),
            Role(name="admin", description="System administrator - Full system access"),
        ]

        for role in roles:
            session.add(role)
            print(f"Role created: {role.name}")

        session.commit()
        print(f"{len(roles)} roles created successfully")

    except Exception as e:
        session.rollback()
        print(f"Error creating roles: {e}")
        raise

    finally:
        session.close()


def create_admin_user():
    """Create the first admin user interactively"""
    print("\n" + "=" * 50)
    print("CREATE FIRST ADMIN USER")
    print("=" * 50)

    session = Session()
    try:
        # Check if admin role exists
        admin_role = session.query(Role).filter_by(name="admin").first()
        if not admin_role:
            print("ERROR: Admin role not found")
            return False

        # Check if admin already exists
        existing_admin = (
            session.query(Role)
            .join(Role.employees)
            .filter(Role.name == "admin")
            .first()
        )
        if existing_admin:
            print("Admin user already exists. Skipping creation...")
            return True

        print("\nEnter admin user details:")

        # Get name
        while True:
            name = input("Full name: ").strip()
            if name:
                break
            print("Name is required")

        # Get email
        while True:
            email = input("Email: ").strip()
            if email and "@" in email:
                break
            print("Valid email is required")

        # Get password with validation
        auth_service = AuthService()
        while True:
            password = getpass.getpass("Password: ")
            is_valid, message = validate_password(password)  # Directement la fonction

            if is_valid:
                confirm = getpass.getpass("Confirm password: ")
                if password == confirm:
                    break
                else:
                    print("Passwords do not match")
            else:
                print(f"Invalid password: {message}")

        # Create admin
        try:
            admin_employee = auth_service.create_employee_with_password(
                name=name, email=email, role_id=admin_role.id, password=password
            )

            print("\nAdmin created successfully!")
            print(f"Employee Number: {admin_employee['employee_number']}")
            print(f"Name: {admin_employee['name']}")
            print(f"Email: {admin_employee['email']}")
            return True

        except Exception as e:
            print(f"Error creating admin: {e}")
            return False

    finally:
        session.close()


def create_database():
    """Completely recreates the database"""
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)

    print("Creating tables...")
    init_db()

    # Clear any remaining data (in case of foreign key issues)
    session = Session()
    try:
        # Delete all data in correct order
        from models import Employee, Customer, Contract, Event

        session.query(Event).delete()
        session.query(Contract).delete()
        session.query(Customer).delete()
        session.query(Employee).delete()
        session.query(Role).delete()
        session.commit()
        print("All existing data cleared")
    except Exception as e:
        session.rollback()
        print(f"Warning: Could not clear existing data: {e}")
    finally:
        session.close()

    print("Creating base roles...")
    create_base_roles()

    print("Database initialized successfully")


def main():
    """Main entry point"""
    print("=" * 50)
    print("CRM DATABASE INITIALIZATION")
    print("=" * 50)

    # Check for --force flag
    import sys

    force_mode = "--force" in sys.argv

    if not force_mode:
        response = input("Do you want to create the database? (y/N): ")
        if response.lower() != "y":
            print("Database initialization cancelled")
            return False
    else:
        print("Force mode: Proceeding without confirmation...")

    try:
        create_database()

        success = create_admin_user()

        if success:
            print("\n" + "=" * 50)
            print("DATABASE INITIALIZATION COMPLETE")
            print("=" * 50)
        else:
            print("\nWarning: Database created but admin user creation failed")

        # Display final state
        session = Session()
        try:
            role_count = session.query(Role).count()
            print(f"\nFinal state: {role_count} roles in database")

            roles = session.query(Role).all()
            for role in roles:
                print(f"   - {role.name} (ID: {role.id}) - {role.description}")

        finally:
            session.close()

    except Exception as e:
        print(f"\nError: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()

    if success:
        print("\nEverything is ready!")
    else:
        print("\nInitialization failed")
        exit(1)
