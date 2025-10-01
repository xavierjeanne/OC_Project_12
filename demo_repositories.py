"""
Démonstration des Repositories OOP
Montre comment utiliser les nouveaux repositories
"""

from sqlalchemy.orm import Session

from db.config import engine, get_db
from repositories import (
    ContractRepository,
    CustomerRepository,
    EmployeeRepository,
    EventRepository,
)


def demo_customer_repository(db: Session):
    """Démonstration du CustomerRepository"""
    print("\n" + "=" * 50)
    print("📋 CUSTOMER REPOSITORY DEMO")
    print("=" * 50)

    repo = CustomerRepository(db)

    # Compter les clients
    count = repo.count()
    print(f"\n✅ Total customers: {count}")

    if count > 0:
        # Récupérer tous les clients
        customers = repo.get_all(limit=5)
        print(f"\n📝 First {len(customers)} customers:")
        for customer in customers:
            print(f"  - {customer.full_name} ({customer.email})")

        # Recherche par nom
        if customers:
            first_name = customers[0].full_name.split()[0]
            results = repo.search_by_name(first_name)
            print(f"\n🔍 Search for '{first_name}': {len(results)} results")

        # Clients sans commercial
        without_sales = repo.get_customers_without_sales_contact()
        print(f"\n⚠️  Customers without sales contact: {len(without_sales)}")


def demo_employee_repository(db: Session):
    """Démonstration du EmployeeRepository"""
    print("\n" + "=" * 50)
    print("👥 EMPLOYEE REPOSITORY DEMO")
    print("=" * 50)

    repo = EmployeeRepository(db)

    # Compter les employés
    count = repo.count()
    print(f"\n✅ Total employees: {count}")

    if count > 0:
        # Par équipe
        sales = repo.get_sales_team()
        support = repo.get_support_team()
        management = repo.get_management_team()

        print(f"\n📊 Team breakdown:")
        print(f"  - Sales: {len(sales)}")
        print(f"  - Support: {len(support)}")
        print(f"  - Management: {len(management)}")

        # Afficher les employés
        employees = repo.get_all(limit=5)
        print(f"\n📝 Employees:")
        for emp in employees:
            print(f"  - {emp.name} ({emp.role}) - {emp.email}")


def demo_contract_repository(db: Session):
    """Démonstration du ContractRepository"""
    print("\n" + "=" * 50)
    print("📄 CONTRACT REPOSITORY DEMO")
    print("=" * 50)

    repo = ContractRepository(db)

    # Compter les contrats
    count = repo.count()
    print(f"\n✅ Total contracts: {count}")

    if count > 0:
        # Statistiques
        signed = repo.find_signed()
        unsigned = repo.find_unsigned()
        with_balance = repo.find_with_balance()

        print(f"\n📊 Contract statistics:")
        print(f"  - Signed: {len(signed)}")
        print(f"  - Unsigned: {len(unsigned)}")
        print(f"  - With balance: {len(with_balance)}")

        # Finances
        total_revenue = repo.get_total_revenue()
        total_outstanding = repo.get_total_outstanding()

        print(f"\n💰 Financial statistics:")
        print(f"  - Total revenue: ${total_revenue:,.2f}")
        print(f"  - Total outstanding: ${total_outstanding:,.2f}")
        print(f"  - Total paid: ${(total_revenue - total_outstanding):,.2f}")


def demo_event_repository(db: Session):
    """Démonstration du EventRepository"""
    print("\n" + "=" * 50)
    print("📅 EVENT REPOSITORY DEMO")
    print("=" * 50)

    repo = EventRepository(db)

    # Compter les événements
    count = repo.count()
    print(f"\n✅ Total events: {count}")

    if count > 0:
        # Événements à venir
        upcoming = repo.find_upcoming(days=30)
        past = repo.find_past()
        without_support = repo.find_without_support()

        print(f"\n📊 Event statistics:")
        print(f"  - Upcoming (30 days): {len(upcoming)}")
        print(f"  - Past events: {len(past)}")
        print(f"  - Without support: {len(without_support)}")

        # Total participants
        total_attendees = repo.get_total_attendees()
        print(f"\n👥 Total attendees: {total_attendees:,}")

        # Afficher les prochains événements
        if upcoming:
            print(f"\n📅 Next upcoming events:")
            for event in upcoming[:3]:
                print(
                    f"  - {event.event_name} on {event.event_date_start} "
                    f"({event.attendees} attendees)"
                )


def main():
    """Fonction principale"""
    print("\n" + "🚀" * 25)
    print("DÉMONSTRATION DES REPOSITORIES OOP")
    print("🚀" * 25)

    # Obtenir une session
    db = next(get_db())

    try:
        # Démonstrations
        demo_customer_repository(db)
        demo_employee_repository(db)
        demo_contract_repository(db)
        demo_event_repository(db)

        print("\n" + "✅" * 25)
        print("DÉMONSTRATION TERMINÉE AVEC SUCCÈS!")
        print("✅" * 25 + "\n")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    main()
