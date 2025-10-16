
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
   CREATE DATABASE crm_test_db OWNER env_db_user;
   ```

d. Accorder les droits à l'utilisateur :
   ```sql
   GRANT CONNECT ON DATABASE env_db_name TO env_db_user;
   GRANT ALL PRIVILEGES ON DATABASE env_db_name TO env_db_user;
   GRANT CONNECT ON DATABASE crm_test_db TO env_db_user;
   GRANT ALL PRIVILEGES ON DATABASE crm_test_db TO env_db_user;
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
Copiez `env.example` en `.env.test` et renseignez vos identifiants pour les tests.

## 5. Initialiser la base de données

Lancez la commande suivante pour créer toutes les tables :

```powershell
python init_db.py
```

Creer un premier utilisateur qui sera l admin systeme du crm

## 6. Se connecter a l application 


```powershell
python epicevents.py login
```


