
# Guide d'installation et d'utilisation

## 1. Créer un environnement virtuel

```powershell
python -m venv .venv
.venv\Scripts\Activate
```

## 2. Installer les dépendances

```powershell
pip install -r requirements.txt
```

## 3. Créer un utilisateur PostgreSQL et une base de données

## Prérequis
- PostgreSQL installé et démarré
- Accès à psql ou PgAdmin
- Port d'écoute PostgreSQL : 5433

## Étapes via psql

a. Ouvrir un terminal et lancer psql :
   ```powershell
   psql -U postgres -h localhost -p 5433
   ```
   (Entrez le mot de passe administrateur PostgreSQL)

b. Créer l'utilisateur non privilégié :
   ```sql
   CREATE USER env_db_user WITH PASSWORD 'env_db_password';
   ```

c. Créer la base de données :
   ```sql
   CREATE DATABASE env_db_name OWNER env_db_user;
   ```

d. Accorder les droits à l'utilisateur :
   ```sql
   GRANT CONNECT ON DATABASE env_db_name TO env_db_user;
   GRANT ALL PRIVILEGES ON DATABASE env_db_name TO env_db_user;
   ```

## 4. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet. Utilisez le modèle ci-dessous comme `env.example` :

```env
DB_USER=env_db_user
DB_PASSWORD=env_db_password
DB_HOST=localhost
DB_PORT=env_db_port
DB_NAME=env_db_name
```

Copiez `env.example` en `.env` et renseignez vos identifiants.


## 5. Initialiser la base de données

Lancez la commande suivante pour créer toutes les tables :

```powershell
python init_db.py
```

Creer un premier utilisateur qui sera l admin systeme du crm

### 2. Lancement de l'application

```bash
# Lancer l'application CLI
python -m cli.main

# Ou directement avec des commandes
python -m cli.main --help
```

## 🔐 Authentification

### Première connexion

```bash
# Se connecter avec votre numéro d'employé et mot de passe
python -m cli.main login

# Exemple
Enter employee number: ADMIN001
Enter password: ********
✅ Login successful! Welcome, Admin User
```

### Déconnexion

```bash
python -m cli.main logout
```

### Vérifier le statut de connexion

```bash
python -m cli.main status
```

## 👥 Gestion des Employés

### Lister les employés

```bash
# Voir tous les employés
python -m cli.main employee list

# Filtrer par rôle
python -m cli.main employee list --role admin
python -m cli.main employee list --role sales
python -m cli.main employee list --role support
```

### Créer un employé (Admin uniquement)

```bash
python -m cli.main employee create \
  --name "Jean Dupont" \
  --email "jean.dupont@epicevents.com" \
  --employee-number "EMP001" \
  --role-id 2
```

### Voir un employé spécifique

```bash
python -m cli.main employee get --id 1
```

### Modifier un employé

```bash
python -m cli.main employee update --id 1 \
  --name "Jean Martin" \
  --email "jean.martin@epicevents.com"
```

### Supprimer un employé

```bash
python -m cli.main employee delete --id 1
```

## 🏢 Gestion des Clients

### Lister les clients

```bash
# Tous les clients
python -m cli.main customer list

# Clients sans contact commercial (Admin/Management)
python -m cli.main customer list --no-contact

# Clients d'un commercial spécifique
python -m cli.main customer list --sales-contact-id 2
```

### Créer un client (Sales uniquement)

```bash
python -m cli.main customer create \
  --name "Entreprise ABC" \
  --email "contact@abc.com" \
  --company "ABC Corp" \
  --phone "+33123456789"
```

### Voir un client

```bash
python -m cli.main customer get --id 1
```

### Modifier un client

```bash
python -m cli.main customer update --id 1 \
  --name "Entreprise XYZ" \
  --phone "+33987654321"
```

### Supprimer un client

```bash
python -m cli.main customer delete --id 1
```

## 📄 Gestion des Contrats

### Lister les contrats

```bash
# Tous les contrats
python -m cli.main contract list

# Contrats non signés (Admin/Management)
python -m cli.main contract list --unsigned

# Contrats impayés (Admin/Management)
python -m cli.main contract list --unpaid
```

### Créer un contrat (Sales pour ses clients)

```bash
python -m cli.main contract create \
  --customer-id 1 \
  --total-amount 15000.50 \
  --remaining-amount 5000.00 \
  --status "draft"
```

### Voir un contrat

```bash
python -m cli.main contract get --id 1
```

### Signer un contrat (Sales)

```bash
python -m cli.main contract update --id 1 --signed
```

### Marquer comme payé (Admin/Management)

```bash
python -m cli.main contract update --id 1 \
  --remaining-amount 0
```

## 🎉 Gestion des Événements

### Lister les événements

```bash
# Tous les événements
python -m cli.main event list

# Événements sans support assigné (Admin/Management)
python -m cli.main event list --no-support

# Événements d'un support spécifique
python -m cli.main event list --support-contact-id 3
```

### Créer un événement (Sales pour contrats signés)

```bash
python -m cli.main event create \
  --contract-id 1 \
  --name "Mariage de Luxe" \
  --start-date "2024-06-15 14:00" \
  --end-date "2024-06-15 23:00" \
  --location "Château de Versailles" \
  --attendees 120 \
  --notes "Thème vintage"
```

### Voir un événement

```bash
python -m cli.main event get --id 1
```

### Assigner un support (Admin/Management)

```bash
python -m cli.main event update --id 1 \
  --support-contact-id 3
```

### Modifier un événement (Support assigné)

```bash
python -m cli.main event update --id 1 \
  --location "Grand Palais" \
  --attendees 150
```

## 🔍 Recherche et Filtres

### Recherche globale

```bash
# Rechercher dans tous les modules
python -m cli.main search "Dupont"

# Rechercher par email
python -m cli.main customer list | grep "dupont@"
```

### Filtres avancés

```bash
# Contrats par montant
python -m cli.main contract list --min-amount 10000

# Événements par date
python -m cli.main event list --start-date "2024-06-01"
```

## 📊 Rapports et Statistiques

### Tableau de bord

```bash
python -m cli.main dashboard
```

### Statistiques par module

```bash
# Statistiques employés
python -m cli.main employee stats

# Statistiques clients
python -m cli.main customer stats

# Statistiques contrats
python -m cli.main contract stats
```

## 🎨 Options d'affichage

### Format de sortie

```bash
# Format tableau (par défaut)
python -m cli.main customer list

# Format JSON
python -m cli.main customer list --format json

# Format CSV
python -m cli.main customer list --format csv
```

### Pagination

```bash
# Limiter les résultats
python -m cli.main customer list --limit 10

# Page spécifique
python -m cli.main customer list --page 2 --limit 10
```

## 🔧 Gestion des Erreurs

### Messages d'aide

```bash
# Aide générale
python -m cli.main --help

# Aide pour un module
python -m cli.main employee --help

# Aide pour une commande
python -m cli.main employee create --help
```

### Gestion des erreurs courantes

- **Authentification requise** : Utilisez `python -m cli.main login`
- **Permissions insuffisantes** : Vérifiez votre rôle avec `python -m cli.main status`
- **Données manquantes** : Utilisez `--help` pour voir les paramètres requis
- **Erreurs de format** : Vérifiez le format des emails, téléphones, dates

## 👨‍💼 Rôles et Permissions

### Admin/Management
- ✅ Gestion complète des employés
- ✅ Vue sur tous les clients, contrats, événements
- ✅ Assignment des supports aux événements
- ✅ Gestion des paiements

### Sales (Commercial)
- ✅ Gestion de ses clients
- ✅ Création/modification de contrats pour ses clients
- ✅ Création d'événements pour contrats signés
- ❌ Pas d'accès aux employés

### Support
- ✅ Vue sur ses événements assignés
- ✅ Modification des événements assignés
- ❌ Pas de création de clients/contrats
- ❌ Pas d'accès aux employés

## 🚨 Dépannage

### Problèmes de connexion

```bash
# Vérifier la configuration
python -c "from db.config import test_connection; test_connection()"

# Réinitialiser la base de données
python init_db.py --reset
```

### Problèmes d'authentification

```bash
# Effacer la session
python -m cli.main logout
rm .epic_events_tokens

# Reconnexion
python -m cli.main login
```

### Logs et debug

```bash
# Mode verbose
python -m cli.main --verbose customer list

# Logs détaillés
python -m cli.main --debug employee create --help
```

---

