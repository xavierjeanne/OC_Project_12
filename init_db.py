"""
CRM Database Initialization
Creates tables and inserts base data (roles)
"""

from models import Base, Role, Session, init_db
from db.config import engine


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
            Role(name="sales", description="Sales team - Customer and contract management"),
            Role(name="support", description="Support team - Event management and customer service"),
            Role(name="management", description="Management - Full system access")
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


def create_database():
    """Completely recreates the database"""
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    
    print("Creating tables...")
    init_db()
    
    print("Creating base roles...")
    create_base_roles()
    
    print("Database initialized successfully")


def main():
    """Main entry point"""
    print("=" * 50)
    print("CRM DATABASE INITIALIZATION")
    print("=" * 50)
    
    try:
        create_database()
        
        print("Creating tables (if missing)...")
        init_db()
        
        print("Checking roles...")
        create_base_roles()
        
        print("Initialization completed")
        
        # Display final state
        session = Session()
        try:
            role_count = session.query(Role).count()
            print(f"\nFinal state: {role_count} roles in database")
            
            # List roles
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
        print(f"\nReady! You can now:")
        print("   1. Run tests: pytest tests/")
        print("   2. Create employees with role_id (1=sales, 2=support, 3=management)")
        print("   3. Use the CRM application")
    else:
        print("\nInitialization failed")
        exit(1)