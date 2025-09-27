# Création d'un utilisateur et d'une base PostgreSQL pour Epic Events CRM

## Prérequis
- PostgreSQL installé et démarré
- Accès à psql ou PgAdmin
- Port d'écoute PostgreSQL : 5433

## Étapes via psql

1. Ouvrir un terminal et lancer psql :
   ```powershell
   psql -U postgres -h localhost -p 5433
   ```
   (Entrez le mot de passe administrateur PostgreSQL)

2. Créer l'utilisateur non privilégié :
   ```sql
   CREATE USER epic_user WITH PASSWORD 'mot_de_passe_fort';
   ```

3. Créer la base de données :
   ```sql
   CREATE DATABASE epic_events_crm OWNER epic_user;
   ```

4. Accorder les droits à l'utilisateur :
   ```sql
   GRANT CONNECT ON DATABASE epic_events_crm TO epic_user;
   GRANT ALL PRIVILEGES ON DATABASE epic_events_crm TO epic_user;
   ```

## Sécurité
- Ne jamais utiliser l'utilisateur `postgres` pour l'application.
- Stocker le mot de passe dans un fichier `.env` (jamais en dur dans le code).

---
Ce guide fonctionne aussi dans PgAdmin (utilisez l'outil de requête SQL).
