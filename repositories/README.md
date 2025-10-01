# Base Repository Pattern

## Vue d'ensemble

Le `BaseRepository` fournit une couche d'abstraction générique pour toutes les opérations CRUD (Create, Read, Update, Delete) sur les entités de la base de données. Il utilise le pattern Repository et les génériques Python (TypeVar) pour assurer la réutilisabilité du code.

## Architecture

```
BaseRepository<T>
    ↑
    ├── CustomerRepository
    ├── EmployeeRepository
    ├── ContractRepository
    └── EventRepository
```

## Fonctionnalités du BaseRepository

### Méthodes CRUD de base

1. **create(data: Dict)** - Créer une nouvelle entité
2. **get_by_id(id: int)** - Récupérer une entité par son ID
3. **get_all(limit, offset)** - Récupérer toutes les entités avec pagination
4. **update(id: int, data: Dict)** - Mettre à jour une entité
5. **delete(id: int)** - Supprimer une entité

### Méthodes utilitaires

6. **filter_by(**kwargs)** - Filtrer par critères multiples
7. **find_one_by(**kwargs)** - Trouver une seule entité
8. **exists(id: int)** - Vérifier l'existence
9. **count()** - Compter le nombre total d'entités

## Utilisation

### 1. Créer un Repository Spécialisé

```python
from repositories.base_repository import BaseRepository
from models.models import Customer
from sqlalchemy.orm import Session

class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session):
        super().__init__(db, Customer)
    
    # Ajouter des méthodes spécifiques au Customer
    def find_by_email(self, email: str):
        return self.find_one_by(email=email)
    
    def search_by_name(self, pattern: str):
        return self.db.query(Customer).filter(
            Customer.full_name.ilike(f"%{pattern}%")
        ).all()
```

### 2. Utiliser le Repository dans le Code

```python
from sqlalchemy.orm import Session
from repositories.customer_repository_oop_example import CustomerRepositoryOOP

# Dans votre fonction ou service
def create_new_customer(db: Session, customer_data: dict):
    # Initialiser le repository
    customer_repo = CustomerRepositoryOOP(db)
    
    # Créer un nouveau client
    customer = customer_repo.create({
        'full_name': 'John Doe',
        'email': 'john@example.com',
        'phone': '0123456789',
        'company_name': 'ACME Corp'
    })
    
    return customer

def get_customer_details(db: Session, customer_id: int):
    customer_repo = CustomerRepositoryOOP(db)
    
    # Récupérer un client
    customer = customer_repo.get_by_id(customer_id)
    
    # Ou avec ses contrats
    customer_with_contracts = customer_repo.get_with_contracts(customer_id)
    
    return customer

def search_customers(db: Session, search_term: str):
    customer_repo = CustomerRepositoryOOP(db)
    
    # Rechercher par nom
    results = customer_repo.search_by_name(search_term)
    
    return results
```

### 3. Dans un Service Layer

```python
from repositories.customer_repository_oop_example import CustomerRepositoryOOP
from validations.validators import validate_email, ValidationError
from security.permissions import require_permission

class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerRepositoryOOP(db)
    
    def create_customer(self, data: dict, current_user):
        # Vérifier les permissions
        require_permission(current_user, Permission.CREATE_CUSTOMER)
        
        # Valider les données
        validate_email(data['email'])
        
        # Vérifier l'unicité de l'email
        if self.repo.email_exists(data['email']):
            raise ValidationError("Email already exists")
        
        # Créer le client via le repository
        return self.repo.create(data)
    
    def get_all_customers(self, limit=None, offset=0):
        return self.repo.get_all(limit=limit, offset=offset)
    
    def update_customer(self, customer_id: int, data: dict, current_user):
        # Vérifier les permissions
        require_permission(current_user, Permission.UPDATE_CUSTOMER)
        
        # Vérifier que le client existe
        if not self.repo.exists(customer_id):
            return None
        
        # Mettre à jour via le repository
        return self.repo.update(customer_id, data)
```

## Avantages du Pattern Repository

### 1. **Séparation des Préoccupations**
- La logique métier (services) est séparée de l'accès aux données (repositories)
- Les contrôleurs/CLI n'interagissent qu'avec les services
- Les services utilisent les repositories pour les opérations DB

### 2. **Testabilité**
- Facile de créer des mocks des repositories pour les tests unitaires
- Tests des services sans vraie base de données

```python
# Test avec mock
def test_create_customer():
    mock_repo = MagicMock(spec=CustomerRepositoryOOP)
    mock_repo.create.return_value = Customer(id=1, email="test@test.com")
    
    service = CustomerService(mock_session)
    service.repo = mock_repo
    
    result = service.create_customer(data, current_user)
    
    assert result.id == 1
    mock_repo.create.assert_called_once()
```

### 3. **Réutilisabilité**
- Les méthodes CRUD de base sont définies une seule fois
- Tous les repositories héritent de ces méthodes
- Moins de code dupliqué

### 4. **Maintenabilité**
- Changements de la base de données isolés dans les repositories
- Facile d'ajouter du caching ou du logging
- Modifications centralisées

### 5. **Abstraction de la Base de Données**
- Le reste de l'application ne dépend pas de SQLAlchemy
- Possibilité de changer d'ORM sans impacter le code métier

## Structure des Fichiers

```
repositories/
├── __init__.py
├── base_repository.py                    # ✅ Classe générique de base
├── customer_repository_oop_example.py    # ✅ Exemple complet
├── customer_repository.py                # Fonctions existantes (à migrer)
├── employee_repository.py                # Fonctions existantes (à migrer)
├── contract_repository.py                # Fonctions existantes (à migrer)
└── event_repository.py                   # Fonctions existantes (à migrer)
```

## Migration des Repositories Existants

Vos repositories actuels utilisent des fonctions. Voici comment migrer vers le pattern OOP:

### Avant (Fonctionnel)
```python
def create_customer(full_name, email, phone=None, company_name=None):
    session = Session()
    customer = Customer(
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company_name
    )
    session.add(customer)
    session.commit()
    return customer
```

### Après (OOP avec BaseRepository)
```python
class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session):
        super().__init__(db, Customer)
    
    # La méthode create() est héritée de BaseRepository
    # Pas besoin de la réécrire!
    
    # Ajouter seulement les méthodes spécifiques
    def find_by_email(self, email: str):
        return self.find_one_by(email=email)
```

### Utilisation
```python
# Avant
customer = create_customer("John Doe", "john@example.com")

# Après
repo = CustomerRepository(db)
customer = repo.create({
    'full_name': 'John Doe',
    'email': 'john@example.com'
})
```

## Logging

Le BaseRepository inclut du logging automatique:
- Info: Créations, mises à jour, suppressions
- Debug: Lectures, comptages, vérifications d'existence
- Error: Toutes les exceptions SQLAlchemy

```python
# Automatiquement loggé par le BaseRepository
logger.info("Created Customer with ID 1")
logger.debug("Retrieved 10 Customer entities")
logger.error("Error creating Customer: Integrity constraint violation")
```

## Gestion des Erreurs

Le BaseRepository capture et relance les `SQLAlchemyError`:
- Les transactions sont automatiquement rollback en cas d'erreur
- Les erreurs sont loggées avant d'être relancées
- Le code appelant peut capturer et gérer les exceptions

```python
try:
    customer = repo.create(invalid_data)
except SQLAlchemyError as e:
    print(f"Database error: {e}")
    # L'erreur a déjà été loggée par le repository
```

## Prochaines Étapes

1. **Migrer les repositories existants** vers le pattern OOP
2. **Créer les services** qui utilisent les repositories
3. **Écrire des tests unitaires** pour les repositories
4. **Implémenter le caching** si nécessaire

## Exemple Complet d'Utilisation

Voir le fichier `customer_repository_oop_example.py` pour un exemple complet et fonctionnel!
